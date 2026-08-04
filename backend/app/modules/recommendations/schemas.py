from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator

TravelStyle = Literal["value", "comfort", "scenery", "family"]


class RecommendationRequest(BaseModel):
    city: str = Field(min_length=1, max_length=64)
    check_in: date
    check_out: date
    guests: int = Field(default=2, ge=1, le=20)
    budget_total: Decimal | None = Field(default=None, ge=0)
    preferred_facilities: list[str] = Field(default_factory=list, max_length=12)
    preferred_districts: list[str] = Field(default_factory=list, max_length=8)
    travel_style: TravelStyle = "value"
    top_k: int = Field(default=3, ge=1, le=10)

    @model_validator(mode="after")
    def validate_preferences(self) -> "RecommendationRequest":
        if self.check_out <= self.check_in:
            raise ValueError("check_out must be later than check_in")
        self.preferred_facilities = list(dict.fromkeys(self.preferred_facilities))
        self.preferred_districts = list(dict.fromkeys(self.preferred_districts))
        return self


class ScoreBreakdown(BaseModel):
    price: Decimal
    rating: Decimal
    facilities: Decimal
    platform_coverage: Decimal
    location: Decimal
    price_freshness: Decimal = Decimal("100.00")


class RecommendationItem(BaseModel):
    rank: int
    listing_public_id: str
    listing_name: str
    district: str
    total_amount: Decimal
    currency: str
    best_rating: Decimal | None
    platform_count: int
    total_score: Decimal
    score_breakdown: ScoreBreakdown
    reasons: list[str]
    tradeoffs: list[str] = Field(default_factory=list)
    risk_notes: list[str] = Field(default_factory=list)
    natural_explanation: str | None = Field(default=None, max_length=500)
    explanation_source: str | None = Field(default=None, max_length=32)
    price_captured_at: datetime | None = None
    price_freshness_status: Literal["fresh", "stale", "unknown"] = "unknown"
    price_age_minutes: int | None = None


class RecommendationResponse(BaseModel):
    session_id: str
    status: Literal["completed", "no_candidates"]
    algorithm_version: str
    request: RecommendationRequest
    results: list[RecommendationItem]
    generated_at: datetime
    explanation_status: Literal["not_requested", "generated", "fallback"] = "not_requested"
    explanation_provider: str | None = None
    explanation_model: str | None = None
    explanation_warning: str | None = None


class RecommendationAdjustmentRequest(BaseModel):
    feedback: str = Field(min_length=3, max_length=500)


class RecommendationAdjustmentResponse(BaseModel):
    original_session_id: str
    new_session_id: str
    feedback: str
    applied_changes: dict[str, object]
    warnings: list[str]
    recommendation: RecommendationResponse
