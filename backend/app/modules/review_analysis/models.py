from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class ListingReview(TimestampMixin, Base):
    __tablename__ = "listing_reviews"
    __table_args__ = (
        UniqueConstraint(
            "canonical_listing_id", "platform_code", "external_id", name="review_source_identity"
        ),
        Index("ix_listing_reviews_listing_date", "canonical_listing_id", "review_date"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    canonical_listing_id: Mapped[int] = mapped_column(
        ForeignKey("canonical_listings.id", ondelete="CASCADE"), nullable=False
    )
    platform_code: Mapped[str] = mapped_column(String(32), nullable=False)
    external_id: Mapped[str] = mapped_column(String(128), nullable=False)
    content: Mapped[str] = mapped_column(String(2000), nullable=False)
    rating: Mapped[Decimal | None] = mapped_column(Numeric(3, 2))
    review_date: Mapped[date | None] = mapped_column(Date)
    source_url: Mapped[str | None] = mapped_column(String(1024))
    language: Mapped[str] = mapped_column(String(16), nullable=False, default="zh-CN")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")


class ReviewAnalysisSnapshot(TimestampMixin, Base):
    __tablename__ = "review_analysis_snapshots"
    __table_args__ = (
        Index("ix_review_analysis_listing_created", "canonical_listing_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    canonical_listing_id: Mapped[int] = mapped_column(
        ForeignKey("canonical_listings.id", ondelete="CASCADE"), nullable=False
    )
    review_count: Mapped[int] = mapped_column(Integer, nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt_tokens: Mapped[int | None] = mapped_column(Integer)
    completion_tokens: Mapped[int | None] = mapped_column(Integer)
    total_tokens: Mapped[int | None] = mapped_column(Integer)
    error_code: Mapped[str | None] = mapped_column(String(40))
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    topics: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    sentiment_distribution: Mapped[dict[str, int]] = mapped_column(JSON, nullable=False)
    warnings: Mapped[list[str]] = mapped_column(JSON, nullable=False)
