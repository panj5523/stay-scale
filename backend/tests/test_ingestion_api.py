from collections.abc import AsyncIterator
from datetime import datetime

from fastapi.testclient import TestClient

from app.db.session import get_db_session
from app.main import app
from app.modules.ingestion.queries import IngestionQueryService
from app.modules.ingestion.schemas import (
    BatchListParams,
    IngestionBatchListResponse,
    IngestionBatchSummary,
)


async def fake_session() -> AsyncIterator[object]:
    yield object()


def test_ingestion_batch_list_returns_audit_summary(monkeypatch) -> None:
    async def fake_list(
        _service: IngestionQueryService,
        params: BatchListParams,
    ) -> IngestionBatchListResponse:
        return IngestionBatchListResponse(
            items=[
                IngestionBatchSummary(
                    id=2,
                    platform_code="tujia",
                    platform_name="途家",
                    source_type="fixture",
                    source_label="tujia-demo.json",
                    status="completed",
                    received_count=3,
                    imported_count=3,
                    failed_count=0,
                    started_at=datetime(2026, 8, 1, 1, 0, 0),
                    completed_at=datetime(2026, 8, 1, 1, 0, 1),
                )
            ],
            total=1,
            page=params.page,
            page_size=params.page_size,
        )

    monkeypatch.setattr(IngestionQueryService, "list_batches", fake_list)
    app.dependency_overrides[get_db_session] = fake_session
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/ingestion/batches")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["items"][0]["platform_code"] == "tujia"
    assert response.json()["items"][0]["imported_count"] == 3


def test_missing_ingestion_batch_returns_not_found(monkeypatch) -> None:
    async def fake_detail(*_args, **_kwargs):
        return None

    monkeypatch.setattr(IngestionQueryService, "get_batch", fake_detail)
    app.dependency_overrides[get_db_session] = fake_session
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/ingestion/batches/999")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "Ingestion batch not found"}
