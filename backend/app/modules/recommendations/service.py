from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.listings.repository import ListingRepository
from app.modules.listings.schemas import ListingSearchParams
from app.modules.recommendations.engine import (
    ALGORITHM_VERSION,
    RecommendationCandidate,
    RecommendationEngine,
    ScoredCandidate,
)
from app.modules.recommendations.models import RecommendationResult, RecommendationSession
from app.modules.recommendations.schemas import (
    RecommendationItem,
    RecommendationRequest,
    RecommendationResponse,
    ScoreBreakdown,
)


class RecommendationService:
    def __init__(
        self,
        session: AsyncSession,
        engine: RecommendationEngine | None = None,
    ) -> None:
        self.session = session
        self.engine = engine or RecommendationEngine()
        self.listings = ListingRepository(session)

    async def recommend(self, request: RecommendationRequest) -> RecommendationResponse:
        rows, _ = await self.listings.search(
            ListingSearchParams(
                city=request.city,
                check_in=request.check_in,
                check_out=request.check_out,
                guests=request.guests,
                page_size=50,
            )
        )
        facility_map = await self.listings.get_facilities([int(row["id"]) for row in rows])
        candidates = [
            RecommendationCandidate(
                canonical_listing_id=int(row["id"]),
                public_id=row["public_id"],
                name=row["name"],
                district=row["district"],
                total_amount=row["lowest_total_amount"],
                currency=row["currency"],
                best_rating=row["best_rating"],
                platform_count=int(row["platform_count"]),
                facility_codes={item["code"] for item in facility_map[int(row["id"])]},
            )
            for row in rows
        ]
        ranked = self.engine.rank(candidates, request)[: request.top_k]
        generated_at = datetime.now(UTC).replace(tzinfo=None)
        recommendation_session = RecommendationSession(
            public_id=str(uuid4()),
            city=request.city,
            check_in=request.check_in,
            check_out=request.check_out,
            guest_count=request.guests,
            travel_style=request.travel_style,
            budget_total=request.budget_total,
            preferred_facilities=request.preferred_facilities,
            preferred_districts=request.preferred_districts,
            algorithm_version=ALGORITHM_VERSION,
            request_payload=request.model_dump(mode="json"),
            status="completed" if ranked else "no_candidates",
            created_at=generated_at,
            updated_at=generated_at,
        )
        self.session.add(recommendation_session)
        await self.session.flush()
        for rank, scored in enumerate(ranked, start=1):
            self.session.add(self._result_model(recommendation_session.id, rank, scored))
        await self.session.commit()
        return self._response(recommendation_session, request, ranked, generated_at)

    async def get(self, public_id: str) -> RecommendationResponse | None:
        recommendation_session = await self.session.scalar(
            select(RecommendationSession)
            .where(RecommendationSession.public_id == public_id)
            .options(selectinload(RecommendationSession.results))
        )
        if recommendation_session is None:
            return None
        request = RecommendationRequest.model_validate(recommendation_session.request_payload)
        return RecommendationResponse(
            session_id=recommendation_session.public_id,
            status=recommendation_session.status,
            algorithm_version=recommendation_session.algorithm_version,
            request=request,
            results=[self._result_response(result) for result in recommendation_session.results],
            generated_at=recommendation_session.created_at,
        )

    @staticmethod
    def _result_model(
        session_id: int,
        rank: int,
        scored: ScoredCandidate,
    ) -> RecommendationResult:
        candidate = scored.candidate
        return RecommendationResult(
            session_id=session_id,
            canonical_listing_id=candidate.canonical_listing_id,
            rank=rank,
            total_score=scored.total_score,
            score_breakdown=scored.breakdown.model_dump(mode="json"),
            reasons=scored.reasons,
            listing_public_id=candidate.public_id,
            listing_name=candidate.name,
            district=candidate.district,
            total_amount=candidate.total_amount,
            currency=candidate.currency,
            best_rating=candidate.best_rating,
            platform_count=candidate.platform_count,
        )

    @staticmethod
    def _result_response(result: RecommendationResult) -> RecommendationItem:
        return RecommendationItem(
            rank=result.rank,
            listing_public_id=result.listing_public_id,
            listing_name=result.listing_name,
            district=result.district,
            total_amount=result.total_amount,
            currency=result.currency,
            best_rating=result.best_rating,
            platform_count=result.platform_count,
            total_score=result.total_score,
            score_breakdown=ScoreBreakdown.model_validate(result.score_breakdown),
            reasons=result.reasons,
        )

    def _response(
        self,
        recommendation_session: RecommendationSession,
        request: RecommendationRequest,
        ranked: list[ScoredCandidate],
        generated_at: datetime,
    ) -> RecommendationResponse:
        return RecommendationResponse(
            session_id=recommendation_session.public_id,
            status=recommendation_session.status,
            algorithm_version=ALGORITHM_VERSION,
            request=request,
            results=[
                RecommendationItem(
                    rank=rank,
                    listing_public_id=scored.candidate.public_id,
                    listing_name=scored.candidate.name,
                    district=scored.candidate.district,
                    total_amount=scored.candidate.total_amount,
                    currency=scored.candidate.currency,
                    best_rating=scored.candidate.best_rating,
                    platform_count=scored.candidate.platform_count,
                    total_score=scored.total_score,
                    score_breakdown=scored.breakdown,
                    reasons=scored.reasons,
                )
                for rank, scored in enumerate(ranked, start=1)
            ],
            generated_at=generated_at,
        )
