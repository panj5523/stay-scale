from datetime import datetime

from pydantic import BaseModel, Field


class SyncSourceUpsert(BaseModel):
    connector_type: str = Field(pattern="^(fixture|authorized_api)$")
    source_label: str = Field(min_length=1, max_length=120)
    interval_minutes: int = Field(default=360, ge=15, le=10080)
    is_enabled: bool = False


class SyncSourceResponse(BaseModel):
    public_id: str
    platform_code: str
    platform_name: str
    connector_type: str
    source_label: str
    interval_minutes: int
    status: str
    is_enabled: bool
    last_run_at: datetime | None
    last_success_at: datetime | None
    last_error: str | None
    next_run_at: datetime | None


class SyncRunResponse(BaseModel):
    platform_code: str
    batch_id: int
    status: str
    received_count: int
    imported_count: int
    failed_count: int
