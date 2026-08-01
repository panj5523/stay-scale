from datetime import date

from app.modules.travel_planning.schemas import TravelPlanPayload


def test_travel_plan_payload_rejects_duplicate_dates() -> None:
    day = {
        "date": date(2026, 10, 2),
        "title": "抵达与入住",
        "items": [
            {
                "time_label": "全天",
                "activity": "办理入住",
                "reason": "根据入住日期安排",
                "note": "待确认",
            }
        ],
    }

    try:
        TravelPlanPayload(summary="这是一个待确认的旅行计划草稿。", days=[day, day])
    except ValueError as error:
        assert "unique" in str(error)
    else:  # pragma: no cover - protects the schema contract
        raise AssertionError("duplicate dates should be rejected")
