from datetime import date, datetime
from decimal import Decimal
from typing import Any, Protocol

from pydantic import BaseModel, Field, model_validator


class NormalizedPrice(BaseModel):
    check_in: date
    check_out: date
    guest_count: int = Field(ge=1)
    currency: str = Field(default="CNY", min_length=3, max_length=3)
    room_subtotal: Decimal = Field(ge=0)
    cleaning_fee: Decimal = Field(default=0, ge=0)
    service_fee: Decimal = Field(default=0, ge=0)
    other_fee: Decimal = Field(default=0, ge=0)
    discount_amount: Decimal = Field(default=0, ge=0)
    total_amount: Decimal = Field(ge=0)
    price_type: str = "standard"
    promotion_conditions: str | None = None
    is_available: bool = True
    remaining_units: int | None = Field(default=None, ge=0)
    captured_at: datetime

    @model_validator(mode="after")
    def validate_price(self) -> "NormalizedPrice":
        if self.check_out <= self.check_in:
            raise ValueError("check_out must be later than check_in")
        expected = (
            self.room_subtotal
            + self.cleaning_fee
            + self.service_fee
            + self.other_fee
            - self.discount_amount
        )
        if self.total_amount != expected:
            raise ValueError("total_amount does not match the price breakdown")
        return self


class NormalizedRoom(BaseModel):
    external_id: str
    name: str
    area_m2: Decimal | None = Field(default=None, gt=0)
    bed_type: str
    bed_count: int = Field(default=1, ge=1)
    max_guests: int = Field(ge=1)
    is_entire_unit: bool = True
    has_private_bathroom: bool = True
    view_type: str | None = None
    cancellation_policy: str | None = None
    status: str = "active"
    prices: list[NormalizedPrice] = Field(default_factory=list)


class NormalizedListing(BaseModel):
    external_id: str
    name: str
    listing_type: str = "homestay"
    summary: str | None = None
    province: str
    city: str
    district: str
    address: str
    latitude: Decimal
    longitude: Decimal
    rating: Decimal | None = Field(default=None, ge=0, le=5)
    review_count: int = Field(default=0, ge=0)
    source_url: str
    status: str = "active"
    captured_at: datetime
    facility_codes: list[str] = Field(default_factory=list)
    rooms: list[NormalizedRoom] = Field(default_factory=list)


class AdapterRecord(BaseModel):
    external_id: str
    raw_payload: dict[str, Any]
    normalized: NormalizedListing


class PlatformAdapter(Protocol):
    platform_code: str
    source_label: str
    source_type: str

    async def fetch(self) -> list[AdapterRecord]: ...
