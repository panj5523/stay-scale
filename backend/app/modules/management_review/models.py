from typing import Any

from sqlalchemy import JSON, BigInteger, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class IngestionReviewAudit(TimestampMixin, Base):
    __tablename__ = "ingestion_review_audits"
    __table_args__ = (
        Index("ix_ingestion_review_audits_record_created", "ingestion_record_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    ingestion_record_id: Mapped[int] = mapped_column(
        ForeignKey("ingestion_records.id", ondelete="CASCADE"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    reviewer_name: Mapped[str] = mapped_column(String(80), nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    previous_decision: Mapped[str] = mapped_column(String(24), nullable=False)
    target_canonical_listing_id: Mapped[int | None] = mapped_column(
        ForeignKey("canonical_listings.id", ondelete="SET NULL")
    )
    changes: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
