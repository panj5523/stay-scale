from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
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
    from app.modules.ingestion.models import IngestionRecord, ListingMatchRecord
    from app.modules.platforms.models import Platform
    from app.modules.pricing.models import PriceSnapshot


class CanonicalListing(TimestampMixin, Base):
    __tablename__ = "canonical_listings"
    __table_args__ = (
        CheckConstraint("latitude BETWEEN -90 AND 90", name="latitude_range"),
        CheckConstraint("longitude BETWEEN -180 AND 180", name="longitude_range"),
        Index("ix_canonical_listings_location", "city", "district"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    listing_type: Mapped[str] = mapped_column(String(32), nullable=False, default="homestay")
    summary: Mapped[str | None] = mapped_column(Text)
    province: Mapped[str] = mapped_column(String(64), nullable=False)
    city: Mapped[str] = mapped_column(String(64), nullable=False)
    district: Mapped[str] = mapped_column(String(64), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    latitude: Mapped[Decimal] = mapped_column(Numeric(10, 7), nullable=False)
    longitude: Mapped[Decimal] = mapped_column(Numeric(10, 7), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")

    platform_listings: Mapped[list["PlatformListing"]] = relationship(
        back_populates="canonical_listing"
    )
    facility_links: Mapped[list["ListingFacility"]] = relationship(
        back_populates="listing",
        cascade="all, delete-orphan",
    )
    match_records: Mapped[list["ListingMatchRecord"]] = relationship(
        back_populates="canonical_listing"
    )


class PlatformListing(TimestampMixin, Base):
    __tablename__ = "platform_listings"
    __table_args__ = (
        UniqueConstraint("platform_id", "external_id", name="platform_external_id"),
        CheckConstraint("rating IS NULL OR rating BETWEEN 0 AND 5", name="rating_range"),
        CheckConstraint("review_count >= 0", name="review_count_non_negative"),
        Index("ix_platform_listings_canonical", "canonical_listing_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    canonical_listing_id: Mapped[int | None] = mapped_column(
        ForeignKey("canonical_listings.id", ondelete="SET NULL")
    )
    platform_id: Mapped[int] = mapped_column(
        ForeignKey("platforms.id", ondelete="RESTRICT"), nullable=False
    )
    external_id: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    rating: Mapped[Decimal | None] = mapped_column(Numeric(3, 2))
    review_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime())

    canonical_listing: Mapped[CanonicalListing | None] = relationship(
        back_populates="platform_listings"
    )
    platform: Mapped["Platform"] = relationship(back_populates="listings")
    room_types: Mapped[list["RoomType"]] = relationship(
        back_populates="platform_listing",
        cascade="all, delete-orphan",
    )
    ingestion_records: Mapped[list["IngestionRecord"]] = relationship(
        back_populates="platform_listing"
    )


class RoomType(TimestampMixin, Base):
    __tablename__ = "room_types"
    __table_args__ = (
        UniqueConstraint("platform_listing_id", "external_id", name="listing_external_id"),
        CheckConstraint("area_m2 IS NULL OR area_m2 > 0", name="area_positive"),
        CheckConstraint("bed_count > 0", name="bed_count_positive"),
        CheckConstraint("max_guests > 0", name="max_guests_positive"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    platform_listing_id: Mapped[int] = mapped_column(
        ForeignKey("platform_listings.id", ondelete="CASCADE"), nullable=False
    )
    external_id: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    area_m2: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    bed_type: Mapped[str] = mapped_column(String(80), nullable=False)
    bed_count: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    max_guests: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    is_entire_unit: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    has_private_bathroom: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    view_type: Mapped[str | None] = mapped_column(String(64))
    cancellation_policy: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")

    platform_listing: Mapped[PlatformListing] = relationship(back_populates="room_types")
    price_snapshots: Mapped[list["PriceSnapshot"]] = relationship(
        back_populates="room_type",
        cascade="all, delete-orphan",
    )


class Facility(TimestampMixin, Base):
    __tablename__ = "facilities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    category: Mapped[str] = mapped_column(String(40), nullable=False)

    listing_links: Mapped[list["ListingFacility"]] = relationship(
        back_populates="facility",
        cascade="all, delete-orphan",
    )


class ListingFacility(Base):
    __tablename__ = "listing_facilities"

    canonical_listing_id: Mapped[int] = mapped_column(
        ForeignKey("canonical_listings.id", ondelete="CASCADE"), primary_key=True
    )
    facility_id: Mapped[int] = mapped_column(
        ForeignKey("facilities.id", ondelete="CASCADE"), primary_key=True
    )
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="normalized")

    listing: Mapped[CanonicalListing] = relationship(back_populates="facility_links")
    facility: Mapped[Facility] = relationship(back_populates="listing_links")
