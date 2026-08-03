from datetime import datetime
from typing import Any

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class ArchiveRestoreRequest(TimestampMixin, Base):
    __tablename__ = "archive_restore_requests"
    __table_args__ = (Index("ix_archive_restore_requests_status_created", "status", "created_at"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    archive_id: Mapped[str] = mapped_column(String(36), nullable=False)
    requested_by: Mapped[int] = mapped_column(
        ForeignKey("admin_users.id", ondelete="RESTRICT"), nullable=False
    )
    reviewed_by: Mapped[int | None] = mapped_column(
        ForeignKey("admin_users.id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    plan_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    decision_reason: Mapped[str | None] = mapped_column(Text)
    executed_by: Mapped[int | None] = mapped_column(
        ForeignKey("admin_users.id", ondelete="SET NULL")
    )
    executed_at: Mapped[datetime | None] = mapped_column(DateTime())
    execution_summary: Mapped[dict[str, Any] | None] = mapped_column(JSON)
