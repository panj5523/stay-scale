from datetime import date, datetime

from pydantic import BaseModel, Field


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
