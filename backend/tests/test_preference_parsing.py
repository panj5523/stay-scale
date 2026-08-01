from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint

from app.db.metadata import Base
from app.modules.preference_parsing.parser import ChinesePreferenceParser


def test_parser_extracts_complete_explainable_preferences() -> None:
    result = ChinesePreferenceParser().parse(
        "想去大理，2026年10月2日到5日，两个人，预算1600以内，"
        "想住大理镇，要有wifi和厨房，性价比高，最好可取消。",
        date(2026, 8, 1),
    )

    assert result.draft.city == "大理市"
    assert result.draft.check_in == date(2026, 10, 2)
    assert result.draft.check_out == date(2026, 10, 5)
    assert result.draft.guests == 2
    assert result.draft.budget_total == Decimal("1600")
    assert result.draft.preferred_facilities == ["wifi", "kitchen"]
    assert result.draft.preferred_districts == ["大理镇"]
    assert result.draft.travel_style == "value"
    assert result.draft.risk_aversion == "high"
    assert result.missing_fields == []
    assert {item.field for item in result.evidence} >= {
        "city",
        "check_in",
        "check_out",
        "guests",
        "budget_total",
    }


def test_parser_uses_priority_and_reports_missing_fields() -> None:
    result = ChinesePreferenceParser().parse(
        "带老人去大理看海，希望有空调和低楼层。",
        date(2026, 8, 1),
    )

    assert result.draft.travel_style == "family"
    assert result.draft.preferred_facilities == [
        "air_conditioning",
        "sea_view",
        "ground_floor",
    ]
    assert result.missing_fields == ["check_in", "check_out", "guests"]
    assert result.warnings


def test_parser_rejects_reversed_extracted_dates_safely() -> None:
    result = ChinesePreferenceParser().parse(
        "2026年10月5日到2日，两人去大理。",
        date(2026, 8, 1),
    )

    assert result.draft.check_in is None
    assert result.draft.check_out is None
    assert "check_in" in result.missing_fields
    assert any("离店日期" in warning for warning in result.warnings)


def test_preference_parse_table_has_confidence_constraint() -> None:
    table = Base.metadata.tables["preference_parse_sessions"]
    check_names = {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert "ck_preference_parse_sessions_confidence_range" in check_names
