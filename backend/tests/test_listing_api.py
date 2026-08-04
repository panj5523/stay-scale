from collections.abc import AsyncIterator
from datetime import datetime
from decimal import Decimal

from fastapi.testclient import TestClient

from app.db.session import get_db_session
from app.main import app
from app.modules.listings.schemas import (
    ListingSearchParams,
    ListingSearchResponse,
    ListingSummaryResponse,
)
from app.modules.listings.service import ListingService


async def fake_session() -> AsyncIterator[object]:
    yield object()


def test_search_listings_returns_paginated_comparison(monkeypatch) -> None:
    async def fake_search(
        _service: ListingService,
        params: ListingSearchParams,
    ) -> ListingSearchResponse:
        assert params.city == "大理市"
        assert params.facility == ["wifi"]
        return ListingSearchResponse(
            items=[
                ListingSummaryResponse(
                    public_id="DL_000001",
                    name="云栖·洱海庭院民宿",
                    listing_type="homestay",
                    summary="安静庭院",
                    city="大理市",
                    district="大理镇",
                    address="演示地址",
                    latitude=Decimal("25.7072310"),
                    longitude=Decimal("100.1798420"),
                    facilities=[],
                    platform_count=3,
                    offer_count=4,
                    lowest_total_amount=Decimal("1302.00"),
                    currency="CNY",
                    best_rating=Decimal("4.83"),
                    oldest_price_captured_at=datetime(2026, 8, 1, 2, 0),
                    freshness_status="fresh",
                    age_minutes=30,
                )
            ],
            total=1,
            page=params.page,
            page_size=params.page_size,
        )

    monkeypatch.setattr(ListingService, "search", fake_search)
    app.dependency_overrides[get_db_session] = fake_session
    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/v1/listings",
                params=[
                    ("city", "大理市"),
                    ("check_in", "2026-10-02"),
                    ("check_out", "2026-10-05"),
                    ("facility", "wifi"),
                    ("facility", "wifi"),
                ],
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["lowest_total_amount"] == "1302.00"


def test_search_listings_rejects_invalid_stay_dates() -> None:
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/listings",
            params={
                "city": "大理市",
                "check_in": "2026-10-05",
                "check_out": "2026-10-02",
            },
        )

    assert response.status_code == 422


def test_listing_detail_returns_not_found(monkeypatch) -> None:
    async def fake_detail(*_args, **_kwargs):
        return None

    monkeypatch.setattr(ListingService, "detail", fake_detail)
    app.dependency_overrides[get_db_session] = fake_session
    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/v1/listings/UNKNOWN",
                params={"check_in": "2026-10-02", "check_out": "2026-10-05"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "Listing not found"}
