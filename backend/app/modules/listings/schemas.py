from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ListingSearchParams(BaseModel):
    city: str = Field(min_length=1, max_length=64)
    check_in: date
    check_out: date
    guests: int = Field(default=2, ge=1, le=20)
    district: str | None = Field(default=None, max_length=64)
    keyword: str | None = Field(default=None, max_length=80)
    facility: list[str] = Field(default_factory=list)
    min_price: Decimal | None = Field(default=None, ge=0)
    max_price: Decimal | None = Field(default=None, ge=0)
    sort: Literal["price_asc", "price_desc", "rating_desc"] = "price_asc"
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=50)

    @model_validator(mode="after")
    def validate_search_range(self) -> "ListingSearchParams":
        if self.check_out <= self.check_in:
            raise ValueError("check_out must be later than check_in")
        if self.min_price is not None and self.max_price is not None:
            if self.max_price < self.min_price:
                raise ValueError("max_price must be greater than or equal to min_price")
        self.facility = list(dict.fromkeys(self.facility))
        return self


class ListingQuoteParams(BaseModel):
    check_in: date
    check_out: date
    guests: int = Field(default=2, ge=1, le=20)

    @model_validator(mode="after")
    def validate_stay_range(self) -> "ListingQuoteParams":
        if self.check_out <= self.check_in:
            raise ValueError("check_out must be later than check_in")
        return self


class FacilityResponse(BaseModel):
    code: str
    name: str
    category: str


class ListingSummaryResponse(BaseModel):
    public_id: str
    name: str
    listing_type: str
    summary: str | None
    city: str
    district: str
    address: str
    latitude: Decimal
    longitude: Decimal
    facilities: list[FacilityResponse]
    platform_count: int
    offer_count: int
    lowest_total_amount: Decimal
    currency: str
    best_rating: Decimal | None
    oldest_price_captured_at: datetime
    freshness_status: Literal["fresh", "stale"]
    age_minutes: int


class ListingSearchResponse(BaseModel):
    items: list[ListingSummaryResponse]
    total: int
    page: int
    page_size: int


class PlatformOfferResponse(BaseModel):
    platform_code: str
    platform_name: str
    platform_listing_name: str
    external_id: str
    rating: Decimal | None
    review_count: int
    source_url: str
    room_name: str
    room_external_id: str
    bed_type: str
    max_guests: int
    cancellation_policy: str | None
    check_in: date
    check_out: date
    currency: str
    room_subtotal: Decimal
    cleaning_fee: Decimal
    service_fee: Decimal
    other_fee: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    price_type: str
    promotion_conditions: str | None
    remaining_units: int | None
    captured_at: datetime
    freshness_status: str = "fresh"
    age_minutes: int = 0


class ListingDetailResponse(BaseModel):
    public_id: str
    name: str
    listing_type: str
    summary: str | None
    province: str
    city: str
    district: str
    address: str
    latitude: Decimal
    longitude: Decimal
    facilities: list[FacilityResponse]
    offers: list[PlatformOfferResponse]
