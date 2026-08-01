from collections.abc import AsyncIterator
from datetime import date, datetime

from fastapi.testclient import TestClient

from app.db.session import get_db_session
from app.main import app
from app.modules.recommendations.schemas import RecommendationRequest, RecommendationResponse
from app.modules.recommendations.service import RecommendationService


async def fake_session() -> AsyncIterator[object]:
    yield object()


def test_create_recommendation_returns_created_session(monkeypatch) -> None:
    async def fake_recommend(
        _service: RecommendationService,
        request: RecommendationRequest,
    ) -> RecommendationResponse:
        return RecommendationResponse(
            session_id="demo-session",
            status="completed",
            algorithm_version="explainable-v1",
            request=request,
            results=[],
            generated_at=datetime(2026, 8, 1, 2, 0, 0),
        )

    monkeypatch.setattr(RecommendationService, "recommend", fake_recommend)
    app.dependency_overrides[get_db_session] = fake_session
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/recommendations",
                json={
                    "city": "大理市",
                    "check_in": "2026-10-02",
                    "check_out": "2026-10-05",
                    "travel_style": "value",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["session_id"] == "demo-session"


def test_missing_recommendation_session_returns_not_found(monkeypatch) -> None:
    async def fake_get(*_args, **_kwargs):
        return None

    monkeypatch.setattr(RecommendationService, "get", fake_get)
    app.dependency_overrides[get_db_session] = fake_session
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/recommendations/missing")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "Recommendation session not found"}


def test_recommendation_endpoint_validates_dates() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/recommendations",
            json={
                "city": "大理市",
                "check_in": str(date(2026, 10, 5)),
                "check_out": str(date(2026, 10, 2)),
            },
        )

    assert response.status_code == 422
