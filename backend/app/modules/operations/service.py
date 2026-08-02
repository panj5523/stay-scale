from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ingestion.models import IngestionBatch, IngestionRecord
from app.modules.listings.models import CanonicalListing, PlatformListing
from app.modules.operations.schemas import (
    AIUsageMetrics,
    IngestionMetrics,
    ListingQualityMetrics,
    OperationsDashboardResponse,
    PlatformCoverageMetric,
    ReviewQueueMetrics,
)
from app.modules.platforms.models import Platform
from app.modules.preference_parsing.models import PreferenceParseSession
from app.modules.recommendations.models import RecommendationSession
from app.modules.review_analysis.models import ReviewAnalysisSnapshot
from app.modules.travel_planning.models import TravelPlanDraft


class OperationsDashboardService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self) -> OperationsDashboardResponse:
        since = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=24)
        review_counts = {
            status: int(
                await self.session.scalar(
                    select(func.count())
                    .select_from(IngestionRecord)
                    .where(IngestionRecord.review_status == status)
                )
                or 0
            )
            for status in ("pending", "approved", "rejected")
        }
        batch_filter = IngestionBatch.created_at >= since
        ingestion = IngestionMetrics(
            batches_24h=await self._count(IngestionBatch, batch_filter),
            completed_batches_24h=await self._count(
                IngestionBatch, batch_filter, IngestionBatch.status == "completed"
            ),
            failed_batches_24h=await self._count(
                IngestionBatch,
                batch_filter,
                IngestionBatch.status.in_(("failed", "completed_with_errors")),
            ),
            records_24h=await self._count(IngestionRecord, IngestionRecord.created_at >= since),
        )
        coverage_rows = (
            await self.session.execute(
                select(
                    Platform.code,
                    Platform.name,
                    func.count(func.distinct(PlatformListing.canonical_listing_id)),
                )
                .outerjoin(PlatformListing, PlatformListing.platform_id == Platform.id)
                .where(PlatformListing.status == "active")
                .group_by(Platform.id, Platform.code, Platform.name)
                .order_by(Platform.code)
            )
        ).all()
        listing_quality = ListingQualityMetrics(
            active_canonical_listings=await self._count(
                CanonicalListing, CanonicalListing.status == "active"
            ),
            active_platform_listings=await self._count(
                PlatformListing, PlatformListing.status == "active"
            ),
            platform_coverage=[
                PlatformCoverageMetric(
                    platform_code=row[0], platform_name=row[1], active_listing_count=int(row[2])
                )
                for row in coverage_rows
            ],
        )
        preference_count, preference_tokens = await self._count_and_tokens(PreferenceParseSession)
        recommendation_count, recommendation_tokens = await self._count_and_tokens(
            RecommendationSession,
            RecommendationSession.explanation_status == "generated",
            token_column=RecommendationSession.explanation_total_tokens,
        )
        plan_count, plan_tokens = await self._count_and_tokens(TravelPlanDraft)
        review_count, review_tokens = await self._count_and_tokens(ReviewAnalysisSnapshot)
        ai_usage = AIUsageMetrics(
            preference_parse_count=preference_count,
            recommendation_explanation_count=recommendation_count,
            travel_plan_count=plan_count,
            review_analysis_count=review_count,
            total_tokens=sum(
                token or 0
                for token in (
                    preference_tokens,
                    recommendation_tokens,
                    plan_tokens,
                    review_tokens,
                )
            ),
        )
        warnings = []
        if review_counts["pending"]:
            warnings.append(f"还有 {review_counts['pending']} 条导入记录等待人工审核。")
        if ingestion.failed_batches_24h:
            warnings.append("最近 24 小时存在失败或部分失败的导入批次。")
        if not ai_usage.total_tokens:
            warnings.append("当前没有可统计的 AI Token 消耗，可能仍在使用本地降级。")
        return OperationsDashboardResponse(
            generated_at=datetime.now(UTC).replace(tzinfo=None),
            review_queue=ReviewQueueMetrics(**review_counts),
            ingestion=ingestion,
            listing_quality=listing_quality,
            ai_usage=ai_usage,
            warnings=warnings,
        )

    async def _count(self, model, *conditions) -> int:
        return int(
            await self.session.scalar(select(func.count()).select_from(model).where(*conditions))
            or 0
        )

    async def _count_and_tokens(self, model, *conditions, token_column=None) -> tuple[int, int]:
        token_column = token_column or model.total_tokens
        result = await self.session.execute(
            select(
                func.count(),
                func.coalesce(func.sum(token_column), 0),
            ).where(*conditions)
        )
        row = result.one()
        return int(row[0]), int(row[1] or 0)
