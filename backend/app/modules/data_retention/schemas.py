from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class RetentionCategory(BaseModel):
    key: str
    label: str
    table: str
    retention_days: int = Field(ge=1)
    cutoff_date: date
    total_count: int = Field(ge=0)
    eligible_count: int = Field(ge=0)
    archive_recommended: bool


class DataRetentionReport(BaseModel):
    generated_at: datetime
    categories: list[RetentionCategory]
    total_eligible_count: int = Field(ge=0)
    archive_recommended: bool
    warnings: list[str]


class ArchiveRequest(BaseModel):
    confirm: bool = False


class ArchiveResponse(BaseModel):
    archive_id: str
    file_name: str
    file_path: str
    sha256: str
    counts: dict[str, int]
    generated_at: datetime
    deletion_performed: bool
    warnings: list[str]


class ArchiveFileInfo(BaseModel):
    archive_id: str
    file_name: str
    size_bytes: int
    created_at: datetime
    sha256: str | None = None
    integrity_status: str = "not_checked"


class ArchiveListResponse(BaseModel):
    archives: list[ArchiveFileInfo]
    total: int


class RestorePreviewResponse(BaseModel):
    archive_id: str
    file_name: str
    integrity_status: str
    manifest_found: bool
    tables_found: list[str]
    missing_tables: list[str]
    record_counts: dict[str, int]
    total_records: int
    restore_performed: bool = False
    warnings: list[str]


class RestoreTablePlan(BaseModel):
    table: str
    archive_records: int
    insert_candidates: int
    existing_conflicts: int
    invalid_records: int


class RestorePlanResponse(BaseModel):
    archive_id: str
    execution_order: list[str]
    tables: list[RestoreTablePlan]
    total_insert_candidates: int
    total_conflicts: int
    can_restore_safely: bool
    restore_performed: bool = False
    blockers: list[str]


class RestoreRequestCreate(BaseModel):
    archive_id: str


class RestoreRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: str
    archive_id: str
    requested_by: int
    reviewed_by: int | None
    executed_by: int | None
    executed_at: datetime | None
    execution_summary: dict | None
    status: str
    plan_snapshot: dict
    decision_reason: str | None
    created_at: datetime
    updated_at: datetime


class RestoreRequestDecision(BaseModel):
    action: str
    reason: str = ""


class RestoreExecutionReadiness(BaseModel):
    request_public_id: str
    archive_id: str
    approved: bool
    archive_integrity_valid: bool
    archive_unchanged: bool
    plan_unchanged: bool
    no_conflicts: bool
    ready_to_execute: bool
    execution_performed: bool = False
    blockers: list[str]


class RestoreExecuteRequest(BaseModel):
    confirmation: str


class RestoreExecuteResponse(BaseModel):
    request_public_id: str
    archive_id: str
    status: str
    inserted_counts: dict[str, int]
    total_inserted: int
    overwrite_performed: bool = False
    deletion_performed: bool = False
