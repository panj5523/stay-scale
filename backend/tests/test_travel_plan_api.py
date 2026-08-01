from collections.abc import AsyncIterator
from datetime import date, datetime

from fastapi.testclient import TestClient

from app.db.session import get_db_session
from app.main import app
from app.modules.travel_planning.schemas import TravelPlanResponse
from app.modules.travel_planning.service import TravelPlanService


async def fake_session() -> AsyncIterator[object]:
    yield object()


def test_create_travel_plan_returns_draft(monkeypatch) -> None:
    async def fake_create(_service: TravelPlanService, _session_id: str) -> TravelPlanResponse:
        return TravelPlanResponse(
            plan_id="plan-001",
            recommendation_session_id="session-001",
            status="draft",
            city="大理市",
            check_in=date(2026, 10, 2),
            check_out=date(2026, 10, 5),
            guests=2,
            provider="local",
            model="evidence-template-v1",
            summary="这是一个需要用户确认和编辑的旅行计划草稿。",
            days=[
                {
                    "date": date(2026, 10, 2),
                    "title": "抵达与入住",
                    "items": [
                        {
                            "time_label": "全天",
                            "activity": "前往已选民宿办理入住",
                            "reason": "根据入住日期安排",
                            "note": "交通方式待确认",
                        }
                    ],
                }
            ],
            warnings=["当前为草稿。"],
            created_at=datetime(2026, 8, 1, 4, 0, 0),
        )

    monkeypatch.setattr(TravelPlanService, "create", fake_create)
    app.dependency_overrides[get_db_session] = fake_session
    try:
        with TestClient(app) as client:
            response = client.post("/api/v1/recommendations/session-001/travel-plan")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "draft"
    assert response.json()["provider"] == "local"


def test_missing_recommendation_returns_not_found(monkeypatch) -> None:
    async def fake_create(*_args, **_kwargs):
        return None

    monkeypatch.setattr(TravelPlanService, "create", fake_create)
    app.dependency_overrides[get_db_session] = fake_session
    try:
        with TestClient(app) as client:
            response = client.post("/api/v1/recommendations/missing/travel-plan")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
