from collections.abc import AsyncIterator
from datetime import date, datetime
from decimal import Decimal

from fastapi.testclient import TestClient

from app.db.session import get_db_session
from app.main import app
from app.modules.preference_parsing.schemas import (
    ParsedPreferences,
    PreferenceConfirmationRequest,
    PreferenceParseRequest,
    PreferenceParseResponse,
)
from app.modules.preference_parsing.service import PreferenceParsingService


async def fake_session() -> AsyncIterator[object]:
    yield object()


def response(status: str = "needs_confirmation") -> PreferenceParseResponse:
    return PreferenceParseResponse(
        session_id="parse-session",
        status=status,
        parser_name="local-rule-parser",
        parser_version="zh-rules-v1",
        confidence=Decimal("0.880"),
        original_text="两人去大理住三晚",
        draft=ParsedPreferences(
            city="大理市",
            check_in=date(2026, 10, 2),
            check_out=date(2026, 10, 5),
            guests=2,
            travel_style="value",
        ),
        evidence=[],
        missing_fields=[],
        warnings=[],
        created_at=datetime(2026, 8, 1, 3, 0, 0),
        confirmed_at=datetime(2026, 8, 1, 3, 1, 0) if status == "confirmed" else None,
    )


def test_create_preference_parse_returns_draft(monkeypatch) -> None:
    async def fake_parse(
        _service: PreferenceParsingService,
        _request: PreferenceParseRequest,
    ) -> PreferenceParseResponse:
        return response()

    monkeypatch.setattr(PreferenceParsingService, "parse", fake_parse)
    app.dependency_overrides[get_db_session] = fake_session
    try:
        with TestClient(app) as client:
            result = client.post(
                "/api/v1/preference-parses",
                json={"text": "两人去大理住三晚"},
            )
    finally:
        app.dependency_overrides.clear()

    assert result.status_code == 201
    assert result.json()["status"] == "needs_confirmation"


def test_confirm_preference_parse_returns_confirmed_result(monkeypatch) -> None:
    async def fake_confirm(
        _service: PreferenceParsingService,
        _session_id: str,
        _request: PreferenceConfirmationRequest,
    ) -> PreferenceParseResponse:
        return response("confirmed")

    monkeypatch.setattr(PreferenceParsingService, "confirm", fake_confirm)
    app.dependency_overrides[get_db_session] = fake_session
    try:
        with TestClient(app) as client:
            result = client.patch(
                "/api/v1/preference-parses/parse-session/confirm",
                json={
                    "preferences": {
                        "city": "大理市",
                        "check_in": "2026-10-02",
                        "check_out": "2026-10-05",
                        "guests": 2,
                        "travel_style": "value",
                    }
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert result.status_code == 200
    assert result.json()["status"] == "confirmed"


def test_confirmation_requires_complete_valid_dates() -> None:
    with TestClient(app) as client:
        result = client.patch(
            "/api/v1/preference-parses/unused/confirm",
            json={"preferences": {"city": "大理市", "guests": 2}},
        )

    assert result.status_code == 422
