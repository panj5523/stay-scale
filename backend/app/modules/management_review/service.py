from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.ingestion.models import IngestionBatch, IngestionRecord, ListingMatchRecord
from app.modules.listings.models import CanonicalListing, PlatformListing
from app.modules.management_review.models import IngestionReviewAudit
from app.modules.management_review.schemas import (
    ReviewCandidate,
    ReviewDecisionRequest,
    ReviewDecisionResponse,
    ReviewQueueParams,
    ReviewQueueResponse,
    ReviewTask,
)


class ReviewConflictError(ValueError):
    pass


class ReviewTargetNotFoundError(ValueError):
    pass


class ManagementReviewService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_tasks(self, params: ReviewQueueParams) -> ReviewQueueResponse:
        filters = []
        if params.status != "all":
            filters.append(IngestionRecord.review_status == params.status)
        statement = (
            select(IngestionRecord)
            .join(ListingMatchRecord)
            .where(*filters)
            .options(
                selectinload(IngestionRecord.batch).selectinload(IngestionBatch.platform),
                selectinload(IngestionRecord.match_record).selectinload(
                    ListingMatchRecord.canonical_listing
                ),
            )
            .order_by(IngestionRecord.id.desc())
        )
        total = int(
            await self.session.scalar(
                select(func.count())
                .select_from(IngestionRecord)
                .join(ListingMatchRecord)
                .where(*filters)
            )
            or 0
        )
        records = (
            await self.session.scalars(
                statement.limit(params.page_size).offset((params.page - 1) * params.page_size)
            )
        ).all()
        return ReviewQueueResponse(
            items=[self._task(record) for record in records],
            total=total,
            page=params.page,
            page_size=params.page_size,
        )

    async def decide(
        self, record_id: int, request: ReviewDecisionRequest
    ) -> ReviewDecisionResponse | None:
        record = await self.session.scalar(
            select(IngestionRecord)
            .where(IngestionRecord.id == record_id)
            .options(selectinload(IngestionRecord.match_record))
        )
        if record is None or record.match_record is None:
            return None
        if record.review_status != "pending":
            raise ReviewConflictError("Review task has already been decided")
        platform_listing = await self.session.get(PlatformListing, record.platform_listing_id)
        if platform_listing is None:
            raise ReviewConflictError("Imported platform listing is missing")

        match = record.match_record
        previous_decision = match.decision
        before_canonical_id = platform_listing.canonical_listing_id
        target = None
        if request.action == "approve":
            target = await self.session.scalar(
                select(CanonicalListing).where(
                    CanonicalListing.public_id == request.target_canonical_public_id,
                    CanonicalListing.status == "active",
                )
            )
            if target is None:
                raise ReviewTargetNotFoundError("Target canonical listing not found")
            platform_listing.canonical_listing_id = target.id
            platform_listing.status = "active"
            match.canonical_listing_id = target.id
            match.decision = "manually_matched"
            record.review_status = "approved"
        else:
            platform_listing.status = "rejected"
            match.decision = "rejected"
            record.review_status = "rejected"

        reviewed_at = datetime.now(UTC).replace(tzinfo=None)
        record.reviewed_at = reviewed_at
        audit = IngestionReviewAudit(
            public_id=str(uuid4()),
            ingestion_record_id=record.id,
            action=request.action,
            reviewer_name=request.reviewer_name.strip(),
            reason=request.reason.strip(),
            previous_decision=previous_decision,
            target_canonical_listing_id=target.id if target else None,
            changes={
                "review_status": {"before": "pending", "after": record.review_status},
                "match_decision": {"before": previous_decision, "after": match.decision},
                "canonical_listing_id": {
                    "before": before_canonical_id,
                    "after": platform_listing.canonical_listing_id,
                },
                "platform_listing_status": platform_listing.status,
            },
            created_at=reviewed_at,
            updated_at=reviewed_at,
        )
        self.session.add(audit)
        await self.session.commit()
        return ReviewDecisionResponse(
            audit_id=audit.public_id,
            record_id=record.id,
            review_status=record.review_status,
            target_canonical_public_id=target.public_id if target else None,
            reviewer_name=audit.reviewer_name,
            reason=audit.reason,
            reviewed_at=reviewed_at,
        )

    @staticmethod
    def _task(record: IngestionRecord) -> ReviewTask:
        match = record.match_record
        normalized = record.normalized_payload or {}
        candidate = match.canonical_listing if match else None
        return ReviewTask(
            record_id=record.id,
            batch_id=record.batch_id,
            platform_code=record.batch.platform.code,
            external_id=record.external_id,
            listing_name=normalized.get("name", record.external_id),
            review_status=record.review_status,
            match_method=match.method,
            match_score=match.score,
            match_decision=match.decision,
            evidence=match.evidence,
            normalized_payload=normalized,
            candidate=(
                ReviewCandidate(
                    public_id=candidate.public_id,
                    name=candidate.name,
                    city=candidate.city,
                    district=candidate.district,
                    address=candidate.address,
                )
                if candidate
                else None
            ),
            created_at=record.created_at,
            reviewed_at=record.reviewed_at,
        )
