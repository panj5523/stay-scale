from decimal import Decimal

from sqlalchemy import CheckConstraint, UniqueConstraint

from app.db.metadata import Base
from app.db.seed import PRICES

EXPECTED_TABLES = {
    "platforms",
    "canonical_listings",
    "platform_listings",
    "room_types",
    "price_snapshots",
    "facilities",
    "listing_facilities",
}


def test_core_accommodation_metadata_contains_expected_tables() -> None:
    assert EXPECTED_TABLES <= set(Base.metadata.tables)


def test_platform_listing_identity_is_unique_per_platform() -> None:
    table = Base.metadata.tables["platform_listings"]
    unique_columns = {
        tuple(column.name for column in constraint.columns)
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }

    assert ("platform_id", "external_id") in unique_columns


def test_price_snapshot_protects_query_identity_and_basic_values() -> None:
    table = Base.metadata.tables["price_snapshots"]
    unique_columns = {
        tuple(column.name for column in constraint.columns)
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    check_names = {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert (
        "room_type_id",
        "check_in",
        "check_out",
        "guest_count",
        "captured_at",
        "price_type",
    ) in unique_columns
    assert {
        "ck_price_snapshots_valid_stay_dates",
        "ck_price_snapshots_guest_count_positive",
        "ck_price_snapshots_total_amount_non_negative",
    } <= check_names


def test_demo_price_totals_include_fees_and_discounts() -> None:
    for price in PRICES:
        room_subtotal = Decimal(price[3])
        cleaning_fee = Decimal(price[4])
        service_fee = Decimal(price[5])
        other_fee = Decimal(price[6])
        discount = Decimal(price[7])
        total = Decimal(price[8])

        assert total == room_subtotal + cleaning_fee + service_fee + other_fee - discount
