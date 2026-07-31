import hashlib
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ingestion.contracts import AdapterRecord, PlatformAdapter
from app.modules.ingestion.matcher import CanonicalCandidate, ListingMatcher, MatchResult
from app.modules.ingestion.models import IngestionBatch, IngestionRecord, ListingMatchRecord
from app.modules.listings.models import (
    CanonicalListing,
    Facility,
    ListingFacility,
    PlatformListing,
    RoomType,
)
from app.modules.platforms.models import Platform
from app.modules.pricing.models import PriceSnapshot


class ImportSummary(BaseModel):
    batch_id: int
    status: str
    received_count: int
    imported_count: int
    failed_count: int
    auto_matched_count: int
    created_count: int
    review_required_count: int


class IngestionService:
    def __init__(self, session: AsyncSession, matcher: ListingMatcher | None = None) -> None:
        self.session = session
        self.matcher = matcher or ListingMatcher()

    async def import_from(self, adapter: PlatformAdapter) -> ImportSummary:
        platform = await self.session.scalar(
            select(Platform).where(Platform.code == adapter.platform_code)
        )
        if platform is None:
            raise ValueError(f"Unknown platform: {adapter.platform_code}")

        batch = IngestionBatch(
            platform_id=platform.id,
            source_type=adapter.source_type,
            source_label=adapter.source_label,
            status="running",
            started_at=datetime.now(UTC).replace(tzinfo=None),
        )
        self.session.add(batch)
        await self.session.flush()

        try:
            records = await adapter.fetch()
        except Exception as exc:
            batch.status = "failed"
            batch.error_summary = str(exc)[:2000]
            batch.completed_at = datetime.now(UTC).replace(tzinfo=None)
            await self.session.commit()
            raise

        batch.received_count = len(records)
        decisions = {"auto_matched": 0, "created": 0, "review_required": 0}

        for adapter_record in records:
            ingestion_record = IngestionRecord(
                batch_id=batch.id,
                external_id=adapter_record.external_id,
                raw_payload=adapter_record.raw_payload,
                normalized_payload=adapter_record.normalized.model_dump(mode="json"),
                status="received",
            )
            self.session.add(ingestion_record)
            await self.session.flush()

            try:
                async with self.session.begin_nested():
                    decision = await self._import_record(platform, ingestion_record, adapter_record)
                ingestion_record.status = "imported"
                batch.imported_count += 1
                decisions[decision] += 1
            except Exception as exc:
                ingestion_record.status = "failed"
                ingestion_record.error_message = str(exc)[:2000]
                batch.failed_count += 1

        batch.status = "completed" if batch.failed_count == 0 else "completed_with_errors"
        batch.completed_at = datetime.now(UTC).replace(tzinfo=None)
        await self.session.commit()
        return ImportSummary(
            batch_id=batch.id,
            status=batch.status,
            received_count=batch.received_count,
            imported_count=batch.imported_count,
            failed_count=batch.failed_count,
            auto_matched_count=decisions["auto_matched"],
            created_count=decisions["created"],
            review_required_count=decisions["review_required"],
        )

    async def _import_record(
        self,
        platform: Platform,
        ingestion_record: IngestionRecord,
        adapter_record: AdapterRecord,
    ) -> str:
        listing = adapter_record.normalized
        candidates = await self._candidates(listing.city)
        result = self.matcher.match(listing, candidates)
        canonical = await self._resolve_canonical(adapter_record, result)

        platform_listing = await self._upsert_platform_listing(
            platform,
            canonical if result.decision != "review_required" else None,
            adapter_record,
        )
        ingestion_record.platform_listing_id = platform_listing.id
        self.session.add(
            ListingMatchRecord(
                ingestion_record_id=ingestion_record.id,
                canonical_listing_id=canonical.id if canonical else None,
                method="weighted_similarity",
                score=result.score,
                decision=result.decision,
                evidence=result.evidence,
            )
        )

        if canonical and result.decision != "review_required":
            await self._upsert_facilities(canonical, listing.facility_codes)
        await self._upsert_rooms_and_prices(platform_listing, adapter_record)
        await self.session.flush()
        return result.decision

    async def _candidates(self, city: str) -> list[CanonicalCandidate]:
        rows = (
            await self.session.scalars(
                select(CanonicalListing).where(
                    CanonicalListing.city == city,
                    CanonicalListing.status == "active",
                )
            )
        ).all()
        return [
            CanonicalCandidate(
                id=row.id,
                public_id=row.public_id,
                name=row.name,
                district=row.district,
                address=row.address,
                latitude=row.latitude,
                longitude=row.longitude,
            )
            for row in rows
        ]

    async def _resolve_canonical(
        self,
        adapter_record: AdapterRecord,
        result: MatchResult,
    ) -> CanonicalListing | None:
        if result.candidate is not None:
            return await self.session.get(CanonicalListing, result.candidate.id)
        if result.decision != "created":
            return None

        listing = adapter_record.normalized
        digest = (
            hashlib.sha1(f"{listing.city}|{listing.name}|{listing.address}".encode())
            .hexdigest()[:10]
            .upper()
        )
        public_id = f"SS_{digest}"
        canonical = await self.session.scalar(
            select(CanonicalListing).where(CanonicalListing.public_id == public_id)
        )
        if canonical is None:
            canonical = CanonicalListing(
                public_id=public_id,
                name=listing.name,
                listing_type=listing.listing_type,
                summary=listing.summary,
                province=listing.province,
                city=listing.city,
                district=listing.district,
                address=listing.address,
                latitude=listing.latitude,
                longitude=listing.longitude,
                status="active",
            )
            self.session.add(canonical)
            await self.session.flush()
        return canonical

    async def _upsert_platform_listing(
        self,
        platform: Platform,
        canonical: CanonicalListing | None,
        adapter_record: AdapterRecord,
    ) -> PlatformListing:
        listing = adapter_record.normalized
        platform_listing = await self.session.scalar(
            select(PlatformListing).where(
                PlatformListing.platform_id == platform.id,
                PlatformListing.external_id == listing.external_id,
            )
        )
        values: dict[str, Any] = {
            "name": listing.name,
            "address": listing.address,
            "rating": listing.rating,
            "review_count": listing.review_count,
            "source_url": listing.source_url,
            "status": listing.status,
            "last_synced_at": listing.captured_at,
        }
        if platform_listing is None:
            platform_listing = PlatformListing(
                platform_id=platform.id,
                external_id=listing.external_id,
                canonical_listing_id=canonical.id if canonical else None,
                **values,
            )
            self.session.add(platform_listing)
        else:
            if canonical is not None:
                platform_listing.canonical_listing_id = canonical.id
            for field, value in values.items():
                setattr(platform_listing, field, value)
        await self.session.flush()
        return platform_listing

    async def _upsert_facilities(
        self,
        canonical: CanonicalListing,
        facility_codes: list[str],
    ) -> None:
        if not facility_codes:
            return
        facilities = (
            await self.session.scalars(select(Facility).where(Facility.code.in_(facility_codes)))
        ).all()
        for facility in facilities:
            link = await self.session.get(ListingFacility, (canonical.id, facility.id))
            if link is None:
                self.session.add(
                    ListingFacility(
                        canonical_listing_id=canonical.id,
                        facility_id=facility.id,
                        source="ingestion",
                    )
                )

    async def _upsert_rooms_and_prices(
        self,
        platform_listing: PlatformListing,
        adapter_record: AdapterRecord,
    ) -> None:
        for normalized_room in adapter_record.normalized.rooms:
            room = await self.session.scalar(
                select(RoomType).where(
                    RoomType.platform_listing_id == platform_listing.id,
                    RoomType.external_id == normalized_room.external_id,
                )
            )
            room_values = normalized_room.model_dump(exclude={"prices"})
            if room is None:
                room = RoomType(platform_listing_id=platform_listing.id, **room_values)
                self.session.add(room)
            else:
                for field, value in room_values.items():
                    setattr(room, field, value)
            await self.session.flush()

            for normalized_price in normalized_room.prices:
                identity = {
                    "room_type_id": room.id,
                    "check_in": normalized_price.check_in,
                    "check_out": normalized_price.check_out,
                    "guest_count": normalized_price.guest_count,
                    "captured_at": normalized_price.captured_at,
                    "price_type": normalized_price.price_type,
                }
                price = await self.session.scalar(select(PriceSnapshot).filter_by(**identity))
                price_values = normalized_price.model_dump(exclude=set(identity) - {"room_type_id"})
                for field in ("check_in", "check_out", "guest_count", "captured_at", "price_type"):
                    price_values.pop(field, None)
                if price is None:
                    price = PriceSnapshot(**identity, **price_values)
                    self.session.add(price)
                else:
                    for field, value in price_values.items():
                        setattr(price, field, value)
