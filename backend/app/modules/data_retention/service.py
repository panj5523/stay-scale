from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.ingestion.models import IngestionBatch, IngestionRecord
from app.modules.preference_parsing.models import PreferenceParseSession
from app.modules.recommendations.models import RecommendationAdjustment, RecommendationSession
from app.modules.review_analysis.models import ListingReview, ReviewAnalysisSnapshot
from app.modules.travel_planning.models import TravelPlanDraft

from .schemas import DataRetentionReport, RetentionCategory


class DataRetentionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_report(self) -> DataRetentionReport:
        today = date.today()
        now = datetime.now(UTC).replace(tzinfo=None)
        definitions = (
            (
                "recommendation_sessions",
                "推荐会话",
                RecommendationSession,
                settings.retention_recommendation_days,
            ),
            (
                "recommendation_adjustments",
                "推荐调整记录",
                RecommendationAdjustment,
                settings.retention_recommendation_days,
            ),
            ("listing_reviews", "评论原文", ListingReview, settings.retention_reviews_days),
            (
                "review_analysis_snapshots",
                "评论分析快照",
                ReviewAnalysisSnapshot,
                settings.retention_ai_snapshots_days,
            ),
            (
                "preference_parse_sessions",
                "AI 需求解析会话",
                PreferenceParseSession,
                settings.retention_ai_snapshots_days,
            ),
            (
                "travel_plan_drafts",
                "旅行计划草稿",
                TravelPlanDraft,
                settings.retention_ai_snapshots_days,
            ),
            ("ingestion_batches", "导入批次", IngestionBatch, settings.retention_ingestion_days),
            ("ingestion_records", "导入记录", IngestionRecord, settings.retention_ingestion_days),
        )
        categories: list[RetentionCategory] = []
        for key, label, model, days in definitions:
            cutoff = today - timedelta(days=days)
            total = int(await self.session.scalar(select(func.count()).select_from(model)) or 0)
            eligible = int(
                await self.session.scalar(
                    select(func.count())
                    .select_from(model)
                    .where(model.created_at < datetime.combine(cutoff, datetime.min.time()))
                )
                or 0
            )
            categories.append(
                RetentionCategory(
                    key=key,
                    label=label,
                    table=model.__tablename__,
                    retention_days=days,
                    cutoff_date=cutoff,
                    total_count=total,
                    eligible_count=eligible,
                    archive_recommended=eligible > 0,
                )
            )
        eligible_total = sum(item.eligible_count for item in categories)
        warnings = ["报告仅统计达到保留期限的数据，不会删除、覆盖或移动任何记录。"]
        if eligible_total:
            warnings.append("存在达到保留期限的数据；请确认归档策略后再执行可恢复归档。")
        return DataRetentionReport(
            generated_at=now,
            categories=categories,
            total_eligible_count=eligible_total,
            archive_recommended=eligible_total > 0,
            warnings=warnings,
        )
