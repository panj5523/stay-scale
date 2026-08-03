import json
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.modules.ai.providers.deepseek import DeepSeekProvider
from app.modules.ai.recommendation_explainer import DeepSeekRecommendationExplainer
from app.modules.ai.schemas import AIProviderError
from app.modules.listings.repository import ListingRepository
from app.modules.listings.schemas import ListingSearchParams
from app.modules.recommendations.engine import (
    ALGORITHM_VERSION,
    RecommendationCandidate,
    RecommendationEngine,
    ScoredCandidate,
)
from app.modules.recommendations.feedback import RecommendationFeedbackInterpreter
from app.modules.recommendations.models import (
    RecommendationAdjustment,
    RecommendationResult,
    RecommendationSession,
)
from app.modules.recommendations.schemas import (
    RecommendationAdjustmentRequest,
    RecommendationAdjustmentResponse,
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
        ai_explainer: DeepSeekRecommendationExplainer | None = None,
    ) -> None:
        self.session = session
        self.engine = engine or RecommendationEngine()
        self.listings = ListingRepository(session)
        self.feedback = RecommendationFeedbackInterpreter()
        self.ai_explainer = ai_explainer or self._configured_ai_explainer()

    async def recommend(
        self, request: RecommendationRequest, user_id: int | None = None
    ) -> RecommendationResponse:
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
            user_id=user_id,
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
            explanation_status=recommendation_session.explanation_status,
            explanation_provider=recommendation_session.explanation_provider,
            explanation_model=recommendation_session.explanation_model,
            explanation_warning=self._explanation_warning(recommendation_session),
        )

    async def history(self, user_id: int) -> list[RecommendationResponse]:
        sessions = (
            (
                await self.session.execute(
                    select(RecommendationSession)
                    .where(RecommendationSession.user_id == user_id)
                    .order_by(RecommendationSession.created_at.desc())
                    .limit(50)
                )
            )
            .scalars()
            .all()
        )
        history = []
        for item in sessions:
            response = await self.get(item.public_id)
            if response is not None:
                history.append(response)
        return history

    async def explain(self, public_id: str) -> RecommendationResponse | None:
        recommendation_session = await self.session.scalar(
            select(RecommendationSession)
            .where(RecommendationSession.public_id == public_id)
            .options(selectinload(RecommendationSession.results))
        )
        if recommendation_session is None:
            return None
        if recommendation_session.explanation_status != "not_requested":
            return self._stored_response(recommendation_session)
        if not recommendation_session.results:
            return self._stored_response(recommendation_session)

        error_code = None
        if self.ai_explainer:
            evidence = [
                self._result_response(result).model_dump(mode="json")
                for result in recommendation_session.results
            ]
            try:
                generated = await self.ai_explainer.explain(
                    json.dumps(evidence, ensure_ascii=False, separators=(",", ":")),
                    {result.listing_public_id for result in recommendation_session.results},
                )
                for result in recommendation_session.results:
                    result.natural_explanation = generated.explanations[result.listing_public_id]
                    result.explanation_source = generated.completion.provider
                recommendation_session.explanation_status = "generated"
                recommendation_session.explanation_provider = generated.completion.provider
                recommendation_session.explanation_model = generated.completion.model
                recommendation_session.explanation_prompt_tokens = (
                    generated.completion.prompt_tokens
                )
                recommendation_session.explanation_completion_tokens = (
                    generated.completion.completion_tokens
                )
                recommendation_session.explanation_total_tokens = generated.completion.total_tokens
            except AIProviderError as error:
                error_code = error.code
        else:
            error_code = "not_configured"

        if error_code:
            for result in recommendation_session.results:
                result.natural_explanation = self._local_explanation(result)
                result.explanation_source = "local-evidence-template"
            recommendation_session.explanation_status = "fallback"
            recommendation_session.explanation_provider = "local"
            recommendation_session.explanation_model = "evidence-template-v1"
            recommendation_session.explanation_error_code = error_code

        await self.session.commit()
        return self._stored_response(recommendation_session)

    async def adjust(
        self,
        public_id: str,
        request: RecommendationAdjustmentRequest,
    ) -> RecommendationAdjustmentResponse | None:
        source = await self.session.scalar(
            select(RecommendationSession).where(RecommendationSession.public_id == public_id)
        )
        if source is None:
            return None
        original_request = RecommendationRequest.model_validate(source.request_payload)
        interpretation = self.feedback.interpret(request.feedback, original_request)
        recommendation = await self.recommend(interpretation.request)
        target = await self.session.scalar(
            select(RecommendationSession).where(
                RecommendationSession.public_id == recommendation.session_id
            )
        )
        if target is None:  # pragma: no cover - recommend always persists a session
            return None
        adjustment = RecommendationAdjustment(
            public_id=str(uuid4()),
            source_session_id=source.id,
            target_session_id=target.id,
            feedback_text=request.feedback.strip(),
            applied_changes=interpretation.applied_changes,
            warnings=interpretation.warnings,
        )
        self.session.add(adjustment)
        await self.session.commit()
        return RecommendationAdjustmentResponse(
            original_session_id=public_id,
            new_session_id=recommendation.session_id,
            feedback=request.feedback.strip(),
            applied_changes=interpretation.applied_changes,
            warnings=interpretation.warnings,
            recommendation=recommendation,
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
            tradeoffs=scored.tradeoffs,
            risk_notes=scored.risk_notes,
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
            tradeoffs=result.tradeoffs,
            risk_notes=result.risk_notes,
            natural_explanation=result.natural_explanation,
            explanation_source=result.explanation_source,
        )

    @staticmethod
    def _configured_ai_explainer() -> DeepSeekRecommendationExplainer | None:
        if not settings.deepseek_enabled or not settings.deepseek_api_key:
            return None
        return DeepSeekRecommendationExplainer(
            DeepSeekProvider(
                api_key=settings.deepseek_api_key,
                base_url=settings.deepseek_base_url,
                model=settings.deepseek_model,
                timeout_seconds=settings.ai_timeout_seconds,
            )
        )

    @staticmethod
    def _local_explanation(result: RecommendationResult) -> str:
        advantages = "；".join(result.reasons)
        caveats = [*result.tradeoffs, *result.risk_notes]
        if caveats:
            return f"推荐它的主要依据是：{advantages}。需要注意：{'；'.join(caveats)}。"
        return f"推荐它的主要依据是：{advantages}。最终选择前仍建议核对实时价格和退订规则。"

    @staticmethod
    def _explanation_warning(session: RecommendationSession) -> str | None:
        if session.explanation_status == "fallback":
            return "DeepSeek 暂时不可用或未配置，当前展示基于真实证据的本地说明。"
        return None

    def _stored_response(
        self, recommendation_session: RecommendationSession
    ) -> RecommendationResponse:
        request = RecommendationRequest.model_validate(recommendation_session.request_payload)
        return RecommendationResponse(
            session_id=recommendation_session.public_id,
            status=recommendation_session.status,
            algorithm_version=recommendation_session.algorithm_version,
            request=request,
            results=[self._result_response(result) for result in recommendation_session.results],
            generated_at=recommendation_session.created_at,
            explanation_status=recommendation_session.explanation_status,
            explanation_provider=recommendation_session.explanation_provider,
            explanation_model=recommendation_session.explanation_model,
            explanation_warning=self._explanation_warning(recommendation_session),
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
                    tradeoffs=scored.tradeoffs,
                    risk_notes=scored.risk_notes,
                    natural_explanation=None,
                    explanation_source=None,
                )
                for rank, scored in enumerate(ranked, start=1)
            ],
            generated_at=generated_at,
            explanation_status="not_requested",
        )
