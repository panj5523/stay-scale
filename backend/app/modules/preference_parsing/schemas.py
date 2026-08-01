from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.modules.recommendations.schemas import TravelStyle

RiskAversion = Literal["low", "medium", "high"]


class PreferenceParseRequest(BaseModel):
    text: str = Field(min_length=3, max_length=1000)
    reference_date: date | None = None

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 3:
            raise ValueError("text must contain at least 3 non-whitespace characters")
        return normalized


class ParsedPreferences(BaseModel):
    city: str | None = Field(default=None, max_length=64)
    check_in: date | None = None
    check_out: date | None = None
    guests: int | None = Field(default=None, ge=1, le=20)
    budget_total: Decimal | None = Field(default=None, ge=0)
    preferred_facilities: list[str] = Field(default_factory=list, max_length=12)
    preferred_districts: list[str] = Field(default_factory=list, max_length=8)
    travel_style: TravelStyle | None = None
    risk_aversion: RiskAversion = "medium"

    @model_validator(mode="after")
    def validate_dates_and_preferences(self) -> "ParsedPreferences":
        if self.check_in and self.check_out and self.check_out <= self.check_in:
            raise ValueError("check_out must be later than check_in")
        self.preferred_facilities = list(dict.fromkeys(self.preferred_facilities))
        self.preferred_districts = list(dict.fromkeys(self.preferred_districts))
        return self


class ExtractionEvidence(BaseModel):
    field: str
    matched_text: str
    normalized_value: str


class PreferenceParseResponse(BaseModel):
    session_id: str
    status: Literal["needs_confirmation", "confirmed"]
    parser_name: str
    parser_version: str
    confidence: Decimal
    original_text: str
    draft: ParsedPreferences
    evidence: list[ExtractionEvidence]
    missing_fields: list[str]
    warnings: list[str]
    created_at: datetime
    confirmed_at: datetime | None = None


class PreferenceConfirmationRequest(BaseModel):
    preferences: ParsedPreferences

    @model_validator(mode="after")
    def require_recommendation_fields(self) -> "PreferenceConfirmationRequest":
        missing = [
            field
            for field in ("city", "check_in", "check_out", "guests")
            if getattr(self.preferences, field) is None
        ]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        return self
