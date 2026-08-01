from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError
from sqlalchemy import CheckConstraint

from app.db.metadata import Base
from app.modules.recommendations.engine import RecommendationCandidate, RecommendationEngine
from app.modules.recommendations.feedback import RecommendationFeedbackInterpreter
from app.modules.recommendations.schemas import RecommendationRequest


def candidates() -> list[RecommendationCandidate]:
    return [
        RecommendationCandidate(
            canonical_listing_id=2,
            public_id="DL_000002",
            name="苍山慢居庭院",
            district="大理镇",
            total_amount=Decimal("1146.00"),
            currency="CNY",
            best_rating=Decimal("4.81"),
            platform_count=2,
            facility_codes={"wifi", "kitchen", "parking", "ground_floor"},
        ),
        RecommendationCandidate(
            canonical_listing_id=1,
            public_id="DL_000001",
            name="云栖·洱海庭院民宿",
            district="大理镇",
            total_amount=Decimal("1302.00"),
            currency="CNY",
            best_rating=Decimal("4.83"),
            platform_count=3,
            facility_codes={"wifi", "kitchen", "washer", "air_conditioning"},
        ),
        RecommendationCandidate(
            canonical_listing_id=3,
            public_id="DL_000003",
            name="月白·双廊海景民宿",
            district="双廊镇",
            total_amount=Decimal("2025.00"),
            currency="CNY",
            best_rating=Decimal("4.86"),
            platform_count=2,
            facility_codes={"wifi", "air_conditioning", "sea_view"},
        ),
    ]


def request(**overrides) -> RecommendationRequest:
    values = {
        "city": "大理市",
        "check_in": date(2026, 10, 2),
        "check_out": date(2026, 10, 5),
        "guests": 2,
    }
    values.update(overrides)
    return RecommendationRequest(**values)


def test_value_style_prioritizes_lower_total_price() -> None:
    ranked = RecommendationEngine().rank(
        candidates(),
        request(travel_style="value", budget_total=Decimal("1500")),
    )

    assert ranked[0].candidate.public_id == "DL_000002"
    assert ranked[0].total_score > ranked[1].total_score
    assert "入住总价在你的预算内" in ranked[0].reasons


def test_scenery_style_promotes_sea_view_property() -> None:
    ranked = RecommendationEngine().rank(candidates(), request(travel_style="scenery"))

    assert ranked[0].candidate.public_id == "DL_000003"
    assert ranked[0].breakdown.facilities == Decimal("100.00")
    assert "完整满足你关注的设施条件" in ranked[0].reasons


def test_explicit_district_and_facilities_are_explainable() -> None:
    ranked = RecommendationEngine().rank(
        candidates(),
        request(
            travel_style="comfort",
            preferred_districts=["大理镇"],
            preferred_facilities=["wifi", "kitchen", "washer"],
        ),
    )

    assert ranked[0].candidate.public_id == "DL_000001"
    assert "完整满足你关注的设施条件" in ranked[0].reasons


def test_recommendation_request_rejects_invalid_dates_and_deduplicates_preferences() -> None:
    with pytest.raises(ValidationError):
        request(check_in=date(2026, 10, 5), check_out=date(2026, 10, 2))

    valid = request(preferred_facilities=["wifi", "wifi", "kitchen"])
    assert valid.preferred_facilities == ["wifi", "kitchen"]


def test_recommendation_tables_and_score_constraint_exist() -> None:
    assert {"recommendation_sessions", "recommendation_results"} <= set(Base.metadata.tables)
    result_table = Base.metadata.tables["recommendation_results"]
    check_names = {
        constraint.name
        for constraint in result_table.constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert "ck_recommendation_results_score_range" in check_names


def test_explanations_include_budget_tradeoff_and_platform_risk() -> None:
    ranked = RecommendationEngine().rank(
        candidates(),
        request(travel_style="scenery", budget_total=Decimal("1600")),
    )
    sea_view = next(item for item in ranked if item.candidate.public_id == "DL_000003")

    assert any("超出预算" in note for note in sea_view.tradeoffs)
    assert any("仅覆盖 2 个平台" in note for note in sea_view.risk_notes)


def test_feedback_interpreter_changes_only_supported_preferences() -> None:
    interpretation = RecommendationFeedbackInterpreter().interpret(
        "更想看海，最好住在双廊镇",
        request(travel_style="value"),
    )

    assert interpretation.request.travel_style == "scenery"
    assert interpretation.request.preferred_facilities == ["sea_view"]
    assert interpretation.request.preferred_districts == ["双廊镇"]
    assert interpretation.applied_changes["travel_style"] == "scenery"
