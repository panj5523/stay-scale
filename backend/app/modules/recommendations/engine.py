from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from app.modules.recommendations.schemas import RecommendationRequest, ScoreBreakdown

ALGORITHM_VERSION = "explainable-v2"

STYLE_WEIGHTS = {
    "value": {
        "price": 0.50,
        "rating": 0.20,
        "facilities": 0.15,
        "coverage": 0.10,
        "location": 0.05,
    },
    "comfort": {
        "price": 0.20,
        "rating": 0.30,
        "facilities": 0.30,
        "coverage": 0.10,
        "location": 0.10,
    },
    "scenery": {
        "price": 0.20,
        "rating": 0.20,
        "facilities": 0.35,
        "coverage": 0.10,
        "location": 0.15,
    },
    "family": {
        "price": 0.25,
        "rating": 0.20,
        "facilities": 0.35,
        "coverage": 0.10,
        "location": 0.10,
    },
}

STYLE_FACILITIES = {
    "value": set(),
    "comfort": {"wifi", "air_conditioning"},
    "scenery": {"sea_view"},
    "family": {"kitchen", "washer", "ground_floor"},
}


@dataclass(frozen=True)
class RecommendationCandidate:
    canonical_listing_id: int
    public_id: str
    name: str
    district: str
    total_amount: Decimal
    currency: str
    best_rating: Decimal | None
    platform_count: int
    facility_codes: set[str]
    price_captured_at: datetime | None = None
    price_freshness_status: str = "unknown"
    price_age_minutes: int | None = None


@dataclass(frozen=True)
class ScoredCandidate:
    candidate: RecommendationCandidate
    total_score: Decimal
    breakdown: ScoreBreakdown
    reasons: list[str]
    tradeoffs: list[str]
    risk_notes: list[str]


class RecommendationEngine:
    def rank(
        self,
        candidates: list[RecommendationCandidate],
        request: RecommendationRequest,
    ) -> list[ScoredCandidate]:
        if not candidates:
            return []
        lowest_price = min(candidate.total_amount for candidate in candidates)
        scored = [self._score(candidate, request, lowest_price) for candidate in candidates]
        return sorted(
            scored,
            key=lambda item: (
                -item.total_score,
                item.candidate.total_amount,
                item.candidate.public_id,
            ),
        )

    def _score(
        self,
        candidate: RecommendationCandidate,
        request: RecommendationRequest,
        lowest_price: Decimal,
    ) -> ScoredCandidate:
        price_score = float(lowest_price / candidate.total_amount)
        within_budget = (
            request.budget_total is None or candidate.total_amount <= request.budget_total
        )
        if request.budget_total is not None and not within_budget:
            price_score *= float(request.budget_total / candidate.total_amount)

        rating_score = float(candidate.best_rating / Decimal("5")) if candidate.best_rating else 0.6
        desired_facilities = (
            set(request.preferred_facilities) or STYLE_FACILITIES[request.travel_style]
        )
        if desired_facilities:
            matched = desired_facilities & candidate.facility_codes
            facility_score = len(matched) / len(desired_facilities)
        else:
            matched = set()
            facility_score = 0.75
        coverage_score = min(candidate.platform_count / 3, 1.0)
        district_match = (
            not request.preferred_districts or candidate.district in request.preferred_districts
        )
        location_score = 1.0 if district_match and request.preferred_districts else 0.75
        if request.preferred_districts and not district_match:
            location_score = 0.35

        components = {
            "price": price_score,
            "rating": rating_score,
            "facilities": facility_score,
            "coverage": coverage_score,
            "location": location_score,
        }
        weights = STYLE_WEIGHTS[request.travel_style]
        total = sum(components[key] * weights[key] for key in weights) * 100
        freshness_score = 0.45 if candidate.price_freshness_status == "stale" else 1.0
        if candidate.price_freshness_status == "stale":
            total *= 0.90
        breakdown = ScoreBreakdown(
            price=self._percent(price_score),
            rating=self._percent(rating_score),
            facilities=self._percent(facility_score),
            platform_coverage=self._percent(coverage_score),
            location=self._percent(location_score),
            price_freshness=self._percent(freshness_score),
        )
        reasons = self._reasons(
            candidate,
            request,
            within_budget,
            matched,
            desired_facilities,
            price_score,
        )
        tradeoffs = self._tradeoffs(candidate, request, within_budget, desired_facilities, matched)
        risk_notes = self._risk_notes(candidate, request)
        return ScoredCandidate(
            candidate=candidate,
            total_score=Decimal(str(total)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            breakdown=breakdown,
            reasons=reasons[:3],
            tradeoffs=tradeoffs[:2],
            risk_notes=risk_notes[:2],
        )

    @staticmethod
    def _tradeoffs(
        candidate: RecommendationCandidate,
        request: RecommendationRequest,
        within_budget: bool,
        desired_facilities: set[str],
        matched: set[str],
    ) -> list[str]:
        notes: list[str] = []
        if request.budget_total is not None and not within_budget:
            notes.append(f"入住总价超出预算 {candidate.total_amount - request.budget_total:.0f} 元")
        if desired_facilities and matched != desired_facilities:
            notes.append(f"未完全满足设施偏好，缺少 {len(desired_facilities - matched)} 项")
        if request.preferred_districts and candidate.district not in request.preferred_districts:
            notes.append("不在你优先考虑的区域")
        return notes

    @staticmethod
    def _risk_notes(
        candidate: RecommendationCandidate, request: RecommendationRequest
    ) -> list[str]:
        notes: list[str] = []
        if candidate.price_freshness_status == "stale":
            notes.append(
                f"最低报价已采集 {candidate.price_age_minutes or 0} 分钟，预订前需要重新确认"
            )
        if candidate.best_rating is None:
            notes.append("当前没有可用的平台评分")
        elif candidate.best_rating < Decimal("4.80"):
            notes.append(f"平台最高评分为 {candidate.best_rating}，低于 4.8")
        if candidate.platform_count < 3:
            notes.append(f"当前仅覆盖 {candidate.platform_count} 个平台，价格可比样本较少")
        return notes

    @staticmethod
    def _reasons(
        candidate: RecommendationCandidate,
        request: RecommendationRequest,
        within_budget: bool,
        matched: set[str],
        desired_facilities: set[str],
        price_score: float,
    ) -> list[str]:
        reasons: list[str] = []
        if request.budget_total is not None and within_budget:
            reasons.append("入住总价在你的预算内")
        if price_score >= 0.95:
            reasons.append("在当前可订候选中总价更有优势")
        if desired_facilities and matched == desired_facilities:
            reasons.append("完整满足你关注的设施条件")
        elif matched:
            reasons.append(f"匹配 {len(matched)} 项偏好设施")
        if candidate.best_rating is not None and candidate.best_rating >= Decimal("4.80"):
            reasons.append("平台评分达到 4.8 分以上")
        if candidate.platform_count >= 3:
            reasons.append("覆盖 3 个平台，价格可比性更充分")
        if request.preferred_districts and candidate.district in request.preferred_districts:
            reasons.append(f"位于你偏好的{candidate.district}")
        if not reasons:
            reasons.append("价格、评分和设施表现较为均衡")
        return reasons

    @staticmethod
    def _percent(value: float) -> Decimal:
        bounded = min(max(value, 0), 1) * 100
        return Decimal(str(bounded)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
