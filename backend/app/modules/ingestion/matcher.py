import math
import re
from dataclasses import dataclass
from decimal import Decimal
from difflib import SequenceMatcher

from app.modules.ingestion.contracts import NormalizedListing

PUNCTUATION = re.compile(r"[\s·•・—_\-（）()【】\[\]，,。.]")
MARKETING_TERMS = ("设计师", "一线", "近码头", "美宿", "客栈")


@dataclass(frozen=True)
class CanonicalCandidate:
    id: int
    public_id: str
    name: str
    district: str
    address: str
    latitude: Decimal
    longitude: Decimal


@dataclass(frozen=True)
class MatchResult:
    candidate: CanonicalCandidate | None
    score: Decimal
    decision: str
    evidence: dict[str, float | str | bool]


class ListingMatcher:
    auto_match_threshold = Decimal("0.7800")
    review_threshold = Decimal("0.6200")

    def match(
        self,
        listing: NormalizedListing,
        candidates: list[CanonicalCandidate],
    ) -> MatchResult:
        scored = [(candidate, self._score(listing, candidate)) for candidate in candidates]
        if not scored:
            return MatchResult(None, Decimal("0"), "created", {"reason": "no_candidates"})

        candidate, evidence = max(scored, key=lambda item: item[1]["total_score"])
        score = Decimal(str(evidence["total_score"])).quantize(Decimal("0.0001"))
        if score >= self.auto_match_threshold:
            decision = "auto_matched"
        elif score >= self.review_threshold:
            decision = "review_required"
        else:
            decision = "created"
            candidate = None
        return MatchResult(candidate, score, decision, evidence)

    def _score(
        self,
        listing: NormalizedListing,
        candidate: CanonicalCandidate,
    ) -> dict[str, float | str | bool]:
        name_score = self._similarity(listing.name, candidate.name)
        address_score = self._similarity(listing.address, candidate.address)
        distance_m = self._distance_metres(
            float(listing.latitude),
            float(listing.longitude),
            float(candidate.latitude),
            float(candidate.longitude),
        )
        geo_score = self._geo_score(distance_m)
        district_match = listing.district == candidate.district
        total = (
            name_score * 0.45
            + address_score * 0.30
            + geo_score * 0.20
            + (0.05 if district_match else 0)
        )
        return {
            "candidate_public_id": candidate.public_id,
            "name_score": round(name_score, 4),
            "address_score": round(address_score, 4),
            "distance_metres": round(distance_m, 2),
            "geo_score": round(geo_score, 4),
            "district_match": district_match,
            "total_score": round(total, 4),
        }

    @staticmethod
    def _similarity(left: str, right: str) -> float:
        def normalize(value: str) -> str:
            normalized = PUNCTUATION.sub("", value).lower()
            for term in MARKETING_TERMS:
                normalized = normalized.replace(term, "")
            return normalized

        return SequenceMatcher(None, normalize(left), normalize(right)).ratio()

    @staticmethod
    def _geo_score(distance_metres: float) -> float:
        if distance_metres <= 100:
            return 1.0
        if distance_metres <= 300:
            return 0.9
        if distance_metres <= 1000:
            return 0.6
        if distance_metres <= 5000:
            return 0.2
        return 0.0

    @staticmethod
    def _distance_metres(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        radius = 6_371_000
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        value = (
            math.sin(delta_phi / 2) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
        )
        return radius * 2 * math.atan2(math.sqrt(value), math.sqrt(1 - value))
