from datetime import datetime

from pydantic import BaseModel


class ReviewQueueMetrics(BaseModel):
    pending: int
    approved: int
    rejected: int


class IngestionMetrics(BaseModel):
    batches_24h: int
    completed_batches_24h: int
    failed_batches_24h: int
    records_24h: int


class PlatformCoverageMetric(BaseModel):
    platform_code: str
    platform_name: str
    active_listing_count: int


class ListingQualityMetrics(BaseModel):
    active_canonical_listings: int
    active_platform_listings: int
    platform_coverage: list[PlatformCoverageMetric]


class AIUsageMetrics(BaseModel):
    preference_parse_count: int
    recommendation_explanation_count: int
    travel_plan_count: int
    review_analysis_count: int
    total_tokens: int


class OperationsDashboardResponse(BaseModel):
    generated_at: datetime
    review_queue: ReviewQueueMetrics
    ingestion: IngestionMetrics
    listing_quality: ListingQualityMetrics
    ai_usage: AIUsageMetrics
    warnings: list[str]
