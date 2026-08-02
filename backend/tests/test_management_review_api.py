from collections.abc import AsyncIterator
from datetime import datetime
from decimal import Decimal

from fastapi.testclient import TestClient

from app.db.session import get_db_session
from app.main import app
from app.modules.management_review.schemas import (
    ReviewDecisionResponse,
    ReviewQueueResponse,
    ReviewTask,
)
from app.modules.management_review.service import ManagementReviewService


async def fake_session() -> AsyncIterator[object]:
    yield object()


def _task() -> ReviewTask:
    return ReviewTask(
        record_id=12,
        batch_id=4,
        platform_code="tujia",
        external_id="TJ-REVIEW-1",
        listing_name="云栖设计师庭院",
        review_status="pending",
        match_method="weighted_similarity",
        match_score=Decimal("0.8230"),
        match_decision="review_required",
        evidence={"name_similarity": 0.88},
        normalized_payload={"city": "大理市"},
        candidate=None,
        created_at=datetime(2026, 8, 2, 2, 0, 0),
        reviewed_at=None,
    )


def test_review_queue_endpoint(monkeypatch) -> None:
    async def fake_list(_service, _params):
        return ReviewQueueResponse(items=[_task()], total=1, page=1, page_size=20)

    monkeypatch.setattr(ManagementReviewService, "list_tasks", fake_list)
    app.dependency_overrides[get_db_session] = fake_session
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/management/reviews")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["items"][0]["review_status"] == "pending"


def test_review_decision_endpoint(monkeypatch) -> None:
    async def fake_decide(_service, _record_id, request):
        return ReviewDecisionResponse(
            audit_id="audit-001",
            record_id=12,
            review_status=request.action.replace("approve", "approved").replace(
                "reject", "rejected"
            ),
            target_canonical_public_id=request.target_canonical_public_id,
            reviewer_name=request.reviewer_name,
            reason=request.reason,
            reviewed_at=datetime(2026, 8, 2, 3, 0, 0),
        )

    monkeypatch.setattr(ManagementReviewService, "decide", fake_decide)
    app.dependency_overrides[get_db_session] = fake_session
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/management/reviews/12/decision",
                json={
                    "action": "approve",
                    "reviewer_name": "项目管理员",
                    "reason": "名称和地址证据一致",
                    "target_canonical_public_id": "DL_000001",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["review_status"] == "approved"
