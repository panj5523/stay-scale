from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.modules.listings.models import RoomType


class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"
    __table_args__ = (
        CheckConstraint("check_out > check_in", name="valid_stay_dates"),
        CheckConstraint("guest_count > 0", name="guest_count_positive"),
        CheckConstraint("room_subtotal >= 0", name="room_subtotal_non_negative"),
        CheckConstraint("cleaning_fee >= 0", name="cleaning_fee_non_negative"),
        CheckConstraint("service_fee >= 0", name="service_fee_non_negative"),
        CheckConstraint("other_fee >= 0", name="other_fee_non_negative"),
        CheckConstraint("discount_amount >= 0", name="discount_non_negative"),
        CheckConstraint("total_amount >= 0", name="total_amount_non_negative"),
        UniqueConstraint(
            "room_type_id",
            "check_in",
            "check_out",
            "guest_count",
            "captured_at",
            "price_type",
            name="room_query_capture_type",
        ),
        Index("ix_price_snapshots_search", "room_type_id", "check_in", "check_out", "guest_count"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    room_type_id: Mapped[int] = mapped_column(
        ForeignKey("room_types.id", ondelete="CASCADE"), nullable=False
    )
    check_in: Mapped[date] = mapped_column(Date, nullable=False)
    check_out: Mapped[date] = mapped_column(Date, nullable=False)
    guest_count: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="CNY")
    room_subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    cleaning_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    service_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    other_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    price_type: Mapped[str] = mapped_column(String(32), nullable=False, default="standard")
    promotion_conditions: Mapped[str | None] = mapped_column(Text)
    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    remaining_units: Mapped[int | None] = mapped_column(SmallInteger)
    captured_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False)

    room_type: Mapped["RoomType"] = relationship(back_populates="price_snapshots")
