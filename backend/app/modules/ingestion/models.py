from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.listings.models import CanonicalListing, PlatformListing
    from app.modules.platforms.models import Platform


class IngestionBatch(TimestampMixin, Base):
    __tablename__ = "ingestion_batches"
    __table_args__ = (
        CheckConstraint("received_count >= 0", name="received_count_non_negative"),
        CheckConstraint("imported_count >= 0", name="imported_count_non_negative"),
        CheckConstraint("failed_count >= 0", name="failed_count_non_negative"),
        Index("ix_ingestion_batches_platform_started", "platform_id", "started_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    platform_id: Mapped[int] = mapped_column(
        ForeignKey("platforms.id", ondelete="RESTRICT"), nullable=False
    )
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_label: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="running")
    received_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    imported_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime())
    error_summary: Mapped[str | None] = mapped_column(Text)

    platform: Mapped["Platform"] = relationship(back_populates="ingestion_batches")
    records: Mapped[list["IngestionRecord"]] = relationship(
        back_populates="batch",
        cascade="all, delete-orphan",
    )


class IngestionRecord(TimestampMixin, Base):
    __tablename__ = "ingestion_records"
    __table_args__ = (
        UniqueConstraint("batch_id", "external_id", name="batch_external_id"),
        Index("ix_ingestion_records_platform_listing", "platform_listing_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    batch_id: Mapped[int] = mapped_column(
        ForeignKey("ingestion_batches.id", ondelete="CASCADE"), nullable=False
    )
    external_id: Mapped[str] = mapped_column(String(128), nullable=False)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    normalized_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="received")
    error_message: Mapped[str | None] = mapped_column(Text)
    platform_listing_id: Mapped[int | None] = mapped_column(
        ForeignKey("platform_listings.id", ondelete="SET NULL")
    )
    review_status: Mapped[str] = mapped_column(String(20), nullable=False, default="not_required")
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime())

    batch: Mapped[IngestionBatch] = relationship(back_populates="records")
    platform_listing: Mapped["PlatformListing | None"] = relationship(
        back_populates="ingestion_records"
    )
    match_record: Mapped["ListingMatchRecord | None"] = relationship(
        back_populates="ingestion_record",
        cascade="all, delete-orphan",
        uselist=False,
    )


class ListingMatchRecord(TimestampMixin, Base):
    __tablename__ = "listing_match_records"
    __table_args__ = (
        CheckConstraint("score BETWEEN 0 AND 1", name="score_range"),
        Index("ix_listing_match_records_canonical", "canonical_listing_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ingestion_record_id: Mapped[int] = mapped_column(
        ForeignKey("ingestion_records.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    canonical_listing_id: Mapped[int | None] = mapped_column(
        ForeignKey("canonical_listings.id", ondelete="SET NULL")
    )
    method: Mapped[str] = mapped_column(String(32), nullable=False)
    score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    decision: Mapped[str] = mapped_column(String(24), nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    ingestion_record: Mapped[IngestionRecord] = relationship(back_populates="match_record")
    canonical_listing: Mapped["CanonicalListing | None"] = relationship(
        back_populates="match_records"
    )
