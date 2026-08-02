from collections.abc import AsyncIterator
from datetime import datetime

from fastapi.testclient import TestClient

from app.db.session import get_db_session
from app.main import app
from app.modules.auth.dependencies import require_admin
from app.modules.operations.schemas import (
    AIUsageMetrics,
    IngestionMetrics,
    ListingQualityMetrics,
    OperationsDashboardResponse,
    ReviewQueueMetrics,
)
from app.modules.operations.service import OperationsDashboardService


async def fake_session() -> AsyncIterator[object]:
    yield object()


async def fake_admin() -> object:
    return object()


def test_operations_dashboard_requires_admin_and_returns_metrics(monkeypatch) -> None:
    async def fake_get(_service):
        return OperationsDashboardResponse(
            generated_at=datetime(2026, 8, 2, 5, 0, 0),
            review_queue=ReviewQueueMetrics(pending=1, approved=2, rejected=0),
            ingestion=IngestionMetrics(
                batches_24h=3,
                completed_batches_24h=3,
                failed_batches_24h=0,
                records_24h=7,
            ),
            listing_quality=ListingQualityMetrics(
                active_canonical_listings=3,
                active_platform_listings=8,
                platform_coverage=[],
            ),
            ai_usage=AIUsageMetrics(
                preference_parse_count=2,
                recommendation_explanation_count=1,
                travel_plan_count=1,
                review_analysis_count=3,
                total_tokens=200,
            ),
            warnings=["还有 1 条导入记录等待人工审核。"],
        )

    monkeypatch.setattr(OperationsDashboardService, "get", fake_get)
    app.dependency_overrides[get_db_session] = fake_session
    app.dependency_overrides[require_admin] = fake_admin
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/management/dashboard")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["review_queue"]["pending"] == 1
    assert response.json()["ai_usage"]["total_tokens"] == 200
