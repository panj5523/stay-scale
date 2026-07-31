from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import CheckConstraint

from app.db.metadata import Base
from app.modules.ingestion.adapters import FixturePlatformAdapter
from app.modules.ingestion.matcher import CanonicalCandidate, ListingMatcher

FIXTURE_PATH = Path(__file__).parents[1] / "fixtures" / "ingestion" / "tujia-demo.json"


@pytest.mark.asyncio
async def test_fixture_adapter_normalizes_platform_payload() -> None:
    records = await FixturePlatformAdapter("tujia", FIXTURE_PATH).fetch()

    assert len(records) == 3
    assert records[0].normalized.external_id == "TJ-DL-2101"
    assert records[0].normalized.facility_codes == [
        "wifi",
        "kitchen",
        "washer",
        "air_conditioning",
        "projector",
    ]
    assert len(records[0].normalized.rooms) == 2
    assert records[0].normalized.rooms[0].prices[0].total_amount == Decimal("1400")


@pytest.mark.asyncio
async def test_fixture_adapter_rejects_wrong_platform() -> None:
    with pytest.raises(ValueError, match="does not match"):
        await FixturePlatformAdapter("meituan", FIXTURE_PATH).fetch()


@pytest.mark.asyncio
async def test_matcher_auto_matches_same_property_across_platform_names() -> None:
    listing = (await FixturePlatformAdapter("tujia", FIXTURE_PATH).fetch())[0].normalized
    candidate = CanonicalCandidate(
        id=1,
        public_id="DL_000001",
        name="云栖·洱海庭院民宿",
        district="大理镇",
        address="才村村委会月华路示范地址1号",
        latitude=Decimal("25.7072310"),
        longitude=Decimal("100.1798420"),
    )

    result = ListingMatcher().match(listing, [candidate])

    assert result.decision == "auto_matched"
    assert result.candidate == candidate
    assert result.score >= ListingMatcher.auto_match_threshold
    assert result.evidence["distance_metres"] == 0


@pytest.mark.asyncio
async def test_matcher_does_not_merge_unrelated_property() -> None:
    listing = (await FixturePlatformAdapter("tujia", FIXTURE_PATH).fetch())[0].normalized
    unrelated = CanonicalCandidate(
        id=9,
        public_id="HZ_000001",
        name="西湖湖畔精品酒店",
        district="西湖区",
        address="杭州市西湖区演示路88号",
        latitude=Decimal("30.2520000"),
        longitude=Decimal("120.1650000"),
    )

    result = ListingMatcher().match(listing, [unrelated])

    assert result.decision == "created"
    assert result.candidate is None
    assert result.score < ListingMatcher.review_threshold


def test_ingestion_audit_tables_and_score_constraint_exist() -> None:
    assert {
        "ingestion_batches",
        "ingestion_records",
        "listing_match_records",
    } <= set(Base.metadata.tables)
    match_table = Base.metadata.tables["listing_match_records"]
    check_names = {
        constraint.name
        for constraint in match_table.constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert "ck_listing_match_records_score_range" in check_names
