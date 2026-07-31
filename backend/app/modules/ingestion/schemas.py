from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class BatchListParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=50)


class IngestionBatchSummary(BaseModel):
    id: int
    platform_code: str
    platform_name: str
    source_type: str
    source_label: str
    status: str
    received_count: int
    imported_count: int
    failed_count: int
    started_at: datetime
    completed_at: datetime | None


class IngestionBatchListResponse(BaseModel):
    items: list[IngestionBatchSummary]
    total: int
    page: int
    page_size: int


class IngestionRecordSummary(BaseModel):
    id: int
    external_id: str
    listing_name: str | None
    status: str
    error_message: str | None
    platform_listing_id: int | None
    canonical_public_id: str | None
    match_method: str | None
    match_score: Decimal | None
    match_decision: str | None
    evidence: dict | None


class IngestionBatchDetail(IngestionBatchSummary):
    error_summary: str | None
    records: list[IngestionRecordSummary]
