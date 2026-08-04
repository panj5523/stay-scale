from datetime import datetime
from typing import Any

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class PlatformSyncSource(TimestampMixin, Base):
    __tablename__ = "platform_sync_sources"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    platform_id: Mapped[int] = mapped_column(
        ForeignKey("platforms.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    connector_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    interval_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=360)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="idle")
    is_enabled: Mapped[bool] = mapped_column(nullable=False, default=False)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime())
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime())
    last_error: Mapped[str | None] = mapped_column(String(500))
