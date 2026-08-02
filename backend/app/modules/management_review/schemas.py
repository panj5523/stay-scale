from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ReviewQueueParams(BaseModel):
    status: Literal["pending", "approved", "rejected", "all"] = "pending"
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=50)


class ReviewCandidate(BaseModel):
    public_id: str
    name: str
    city: str
    district: str
    address: str


class ReviewTask(BaseModel):
    record_id: int
    batch_id: int
    platform_code: str
    external_id: str
    listing_name: str
    review_status: str
    match_method: str
    match_score: Decimal
    match_decision: str
    evidence: dict
    normalized_payload: dict
    candidate: ReviewCandidate | None
    created_at: datetime
    reviewed_at: datetime | None


class ReviewQueueResponse(BaseModel):
    items: list[ReviewTask]
    total: int
    page: int
    page_size: int


class ReviewDecisionRequest(BaseModel):
    action: Literal["approve", "reject"]
    reviewer_name: str = Field(min_length=2, max_length=80)
    reason: str = Field(min_length=3, max_length=500)
    target_canonical_public_id: str | None = Field(default=None, max_length=32)

    @model_validator(mode="after")
    def require_target_for_approval(self) -> "ReviewDecisionRequest":
        if self.action == "approve" and not self.target_canonical_public_id:
            raise ValueError("target_canonical_public_id is required for approval")
        return self


class ReviewDecisionResponse(BaseModel):
    audit_id: str
    record_id: int
    review_status: Literal["approved", "rejected"]
    target_canonical_public_id: str | None
    reviewer_name: str
    reason: str
    reviewed_at: datetime
