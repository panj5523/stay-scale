import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from app.modules.ingestion.contracts import (
    AdapterRecord,
    NormalizedListing,
    NormalizedPrice,
    NormalizedRoom,
)

FACILITY_MAP = {
    "WiFi": "wifi",
    "无线网络": "wifi",
    "厨房": "kitchen",
    "洗衣机": "washer",
    "空调": "air_conditioning",
    "停车位": "parking",
    "投影": "projector",
    "一楼房型": "ground_floor",
    "海景": "sea_view",
}


class FixturePlatformAdapter:
    source_type = "fixture"

    def __init__(self, platform_code: str, fixture_path: Path) -> None:
        self.platform_code = platform_code
        self.fixture_path = fixture_path.resolve()
        self.source_label = self.fixture_path.name

    async def fetch(self) -> list[AdapterRecord]:
        payload = json.loads(self.fixture_path.read_text(encoding="utf-8"))
        if payload.get("platform") != self.platform_code:
            raise ValueError("Fixture platform does not match the requested platform")
        return [self._normalize(raw) for raw in payload.get("listings", [])]

    def _normalize(self, raw: dict[str, Any]) -> AdapterRecord:
        location = raw["location"]
        rooms = [self._normalize_room(room) for room in raw.get("rooms", [])]
        listing = NormalizedListing(
            external_id=str(raw["listingId"]).strip(),
            name=str(raw["title"]).strip(),
            listing_type=raw.get("propertyType", "homestay"),
            summary=self._optional_text(raw.get("description")),
            province=str(location["province"]).strip(),
            city=str(location["city"]).strip(),
            district=str(location["district"]).strip(),
            address=str(location["address"]).strip(),
            latitude=Decimal(str(location["latitude"])),
            longitude=Decimal(str(location["longitude"])),
            rating=Decimal(str(raw["rating"])) if raw.get("rating") is not None else None,
            review_count=int(raw.get("reviewCount", 0)),
            source_url=str(raw["url"]),
            captured_at=raw["capturedAt"],
            facility_codes=list(
                dict.fromkeys(
                    FACILITY_MAP[facility]
                    for facility in raw.get("amenities", [])
                    if facility in FACILITY_MAP
                )
            ),
            rooms=rooms,
        )
        return AdapterRecord(
            external_id=listing.external_id,
            raw_payload=raw,
            normalized=listing,
        )

    @staticmethod
    def _normalize_room(raw: dict[str, Any]) -> NormalizedRoom:
        prices = [
            NormalizedPrice(
                check_in=price["checkIn"],
                check_out=price["checkOut"],
                guest_count=price.get("guests", 2),
                currency=price.get("currency", "CNY"),
                room_subtotal=price["roomSubtotal"],
                cleaning_fee=price.get("cleaningFee", 0),
                service_fee=price.get("serviceFee", 0),
                other_fee=price.get("otherFee", 0),
                discount_amount=price.get("discount", 0),
                total_amount=price["total"],
                price_type=price.get("priceType", "standard"),
                promotion_conditions=FixturePlatformAdapter._optional_text(price.get("conditions")),
                is_available=price.get("available", True),
                remaining_units=price.get("remainingUnits"),
                captured_at=price["capturedAt"],
            )
            for price in raw.get("prices", [])
        ]
        return NormalizedRoom(
            external_id=str(raw["roomId"]).strip(),
            name=str(raw["name"]).strip(),
            area_m2=raw.get("areaM2"),
            bed_type=str(raw["bedType"]).strip(),
            bed_count=raw.get("bedCount", 1),
            max_guests=raw["maxGuests"],
            is_entire_unit=raw.get("entireUnit", True),
            has_private_bathroom=raw.get("privateBathroom", True),
            view_type=FixturePlatformAdapter._optional_text(raw.get("view")),
            cancellation_policy=FixturePlatformAdapter._optional_text(
                raw.get("cancellationPolicy")
            ),
            prices=prices,
        )

    @staticmethod
    def _optional_text(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None
