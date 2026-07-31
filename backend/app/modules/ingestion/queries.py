from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.ingestion.models import IngestionBatch, IngestionRecord, ListingMatchRecord
from app.modules.ingestion.schemas import (
    BatchListParams,
    IngestionBatchDetail,
    IngestionBatchListResponse,
    IngestionBatchSummary,
    IngestionRecordSummary,
)
from app.modules.listings.models import CanonicalListing  # noqa: F401
from app.modules.platforms.models import Platform  # noqa: F401


class IngestionQueryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_batches(self, params: BatchListParams) -> IngestionBatchListResponse:
        total = int(
            await self.session.scalar(select(func.count()).select_from(IngestionBatch)) or 0
        )
        batches = (
            await self.session.scalars(
                select(IngestionBatch)
                .options(selectinload(IngestionBatch.platform))
                .order_by(IngestionBatch.id.desc())
                .limit(params.page_size)
                .offset((params.page - 1) * params.page_size)
            )
        ).all()
        return IngestionBatchListResponse(
            items=[self._batch_summary(batch) for batch in batches],
            total=total,
            page=params.page,
            page_size=params.page_size,
        )

    async def get_batch(self, batch_id: int) -> IngestionBatchDetail | None:
        batch = await self.session.scalar(
            select(IngestionBatch)
            .where(IngestionBatch.id == batch_id)
            .options(
                selectinload(IngestionBatch.platform),
                selectinload(IngestionBatch.records)
                .selectinload(IngestionRecord.match_record)
                .selectinload(ListingMatchRecord.canonical_listing),
            )
        )
        if batch is None:
            return None
        records = sorted(batch.records, key=lambda record: record.id)
        return IngestionBatchDetail(
            **self._batch_summary(batch).model_dump(),
            error_summary=batch.error_summary,
            records=[self._record_summary(record) for record in records],
        )

    @staticmethod
    def _batch_summary(batch: IngestionBatch) -> IngestionBatchSummary:
        return IngestionBatchSummary(
            id=batch.id,
            platform_code=batch.platform.code,
            platform_name=batch.platform.name,
            source_type=batch.source_type,
            source_label=batch.source_label,
            status=batch.status,
            received_count=batch.received_count,
            imported_count=batch.imported_count,
            failed_count=batch.failed_count,
            started_at=batch.started_at,
            completed_at=batch.completed_at,
        )

    @staticmethod
    def _record_summary(record: IngestionRecord) -> IngestionRecordSummary:
        match = record.match_record
        normalized = record.normalized_payload or {}
        return IngestionRecordSummary(
            id=record.id,
            external_id=record.external_id,
            listing_name=normalized.get("name"),
            status=record.status,
            error_message=record.error_message,
            platform_listing_id=record.platform_listing_id,
            canonical_public_id=(
                match.canonical_listing.public_id
                if match is not None and match.canonical_listing is not None
                else None
            ),
            match_method=match.method if match else None,
            match_score=match.score if match else None,
            match_decision=match.decision if match else None,
            evidence=match.evidence if match else None,
        )
