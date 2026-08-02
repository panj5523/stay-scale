from collections.abc import AsyncIterator
from datetime import datetime

from fastapi.testclient import TestClient

from app.db.session import get_db_session
from app.main import app
from app.modules.review_analysis.schemas import ReviewAnalysisResponse
from app.modules.review_analysis.service import ReviewAnalysisService


async def fake_session() -> AsyncIterator[object]:
    yield object()


def test_review_analysis_endpoint_returns_snapshot(monkeypatch) -> None:
    async def fake_analyze(_service, listing_id, _request):
        return ReviewAnalysisResponse(
            analysis_id="analysis-001",
            listing_public_id=listing_id,
            review_count=1,
            provider="local",
            model="keyword-v1",
            summary="评论整体较为积极，但仍需结合原文复核。",
            topics=[],
            sentiment_distribution={"positive": 1, "neutral": 0, "negative": 0},
            warnings=["当前为本地规则初筛。"],
            created_at=datetime(2026, 8, 1, 5, 0, 0),
        )

    monkeypatch.setattr(ReviewAnalysisService, "analyze", fake_analyze)
    app.dependency_overrides[get_db_session] = fake_session
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/listings/DL_000001/review-analysis",
                json={
                    "reviews": [
                        {
                            "external_id": "review-1",
                            "platform_code": "meituan",
                            "content": "房间很干净",
                        }
                    ]
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["provider"] == "local"
