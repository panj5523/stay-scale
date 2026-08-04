from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    BigInteger,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.listings.models import CanonicalListing


class RecommendationSession(TimestampMixin, Base):
    __tablename__ = "recommendation_sessions"
    __table_args__ = (
        CheckConstraint("check_out > check_in", name="valid_stay_dates"),
        CheckConstraint("guest_count > 0", name="guest_count_positive"),
        CheckConstraint("budget_total IS NULL OR budget_total >= 0", name="budget_non_negative"),
        Index("ix_recommendation_sessions_city_created", "city", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("user_accounts.id", ondelete="SET NULL"))
    public_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    city: Mapped[str] = mapped_column(String(64), nullable=False)
    check_in: Mapped[date] = mapped_column(Date, nullable=False)
    check_out: Mapped[date] = mapped_column(Date, nullable=False)
    guest_count: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    travel_style: Mapped[str] = mapped_column(String(24), nullable=False)
    budget_total: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    preferred_facilities: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    preferred_districts: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    algorithm_version: Mapped[str] = mapped_column(String(32), nullable=False)
    request_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="completed")
    explanation_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="not_requested"
    )
    explanation_provider: Mapped[str | None] = mapped_column(String(32))
    explanation_model: Mapped[str | None] = mapped_column(String(64))
    explanation_prompt_tokens: Mapped[int | None] = mapped_column(Integer)
    explanation_completion_tokens: Mapped[int | None] = mapped_column(Integer)
    explanation_total_tokens: Mapped[int | None] = mapped_column(Integer)
    explanation_error_code: Mapped[str | None] = mapped_column(String(40))

    results: Mapped[list["RecommendationResult"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="RecommendationResult.rank",
    )


class RecommendationResult(TimestampMixin, Base):
    __tablename__ = "recommendation_results"
    __table_args__ = (
        UniqueConstraint("session_id", "rank", name="session_rank"),
        UniqueConstraint("session_id", "canonical_listing_id", name="session_listing"),
        CheckConstraint("`rank` > 0", name="rank_positive"),
        CheckConstraint("total_score BETWEEN 0 AND 100", name="score_range"),
        CheckConstraint("total_amount >= 0", name="total_amount_non_negative"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("recommendation_sessions.id", ondelete="CASCADE"), nullable=False
    )
    canonical_listing_id: Mapped[int | None] = mapped_column(
        ForeignKey("canonical_listings.id", ondelete="SET NULL")
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    total_score: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    score_breakdown: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    reasons: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    tradeoffs: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    risk_notes: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    listing_public_id: Mapped[str] = mapped_column(String(32), nullable=False)
    listing_name: Mapped[str] = mapped_column(String(160), nullable=False)
    district: Mapped[str] = mapped_column(String(64), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    best_rating: Mapped[Decimal | None] = mapped_column(Numeric(3, 2))
    platform_count: Mapped[int] = mapped_column(Integer, nullable=False)
    price_captured_at: Mapped[datetime | None] = mapped_column()
    price_freshness_status: Mapped[str | None] = mapped_column(String(16))
    price_age_minutes: Mapped[int | None] = mapped_column(Integer)
    natural_explanation: Mapped[str | None] = mapped_column(Text)
    explanation_source: Mapped[str | None] = mapped_column(String(32))

    session: Mapped[RecommendationSession] = relationship(back_populates="results")
    canonical_listing: Mapped["CanonicalListing | None"] = relationship(
        back_populates="recommendation_results"
    )


class RecommendationAdjustment(TimestampMixin, Base):
    __tablename__ = "recommendation_adjustments"
    __table_args__ = (
        Index("ix_recommendation_adjustments_source_created", "source_session_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    source_session_id: Mapped[int] = mapped_column(
        ForeignKey("recommendation_sessions.id", ondelete="CASCADE"), nullable=False
    )
    target_session_id: Mapped[int] = mapped_column(
        ForeignKey("recommendation_sessions.id", ondelete="CASCADE"), nullable=False
    )
    feedback_text: Mapped[str] = mapped_column(String(500), nullable=False)
    applied_changes: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    warnings: Mapped[list[str]] = mapped_column(JSON, nullable=False)
