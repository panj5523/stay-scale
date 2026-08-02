from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ReviewInput(BaseModel):
    external_id: str = Field(min_length=1, max_length=128)
    platform_code: str = Field(min_length=1, max_length=32)
    content: str = Field(min_length=2, max_length=2000)
    rating: Decimal | None = Field(default=None, ge=0, le=5)
    review_date: date | None = None
    source_url: str | None = Field(default=None, max_length=1024)

    @model_validator(mode="after")
    def normalize_content(self) -> "ReviewInput":
        self.content = self.content.strip()
        if len(self.content) < 2:
            raise ValueError("content must contain at least 2 non-whitespace characters")
        return self


class ReviewAnalysisRequest(BaseModel):
    reviews: list[ReviewInput] = Field(min_length=1, max_length=50)

    @model_validator(mode="after")
    def reject_duplicate_ids(self) -> "ReviewAnalysisRequest":
        identities = [(item.platform_code, item.external_id) for item in self.reviews]
        if len(identities) != len(set(identities)):
            raise ValueError("review source identities must be unique")
        return self


class ReviewTopic(BaseModel):
    code: str = Field(min_length=1, max_length=32)
    label: str = Field(min_length=1, max_length=40)
    sentiment: Literal["positive", "neutral", "negative"]
    mention_count: int = Field(ge=1, le=50)
    evidence: list[str] = Field(min_length=1, max_length=3)


class ReviewAnalysisResponse(BaseModel):
    analysis_id: str
    listing_public_id: str
    review_count: int = Field(ge=1, le=50)
    provider: str
    model: str
    summary: str = Field(max_length=500)
    topics: list[ReviewTopic] = Field(max_length=8)
    sentiment_distribution: dict[str, int]
    warnings: list[str]
    created_at: datetime
