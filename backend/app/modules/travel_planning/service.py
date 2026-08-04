import json
from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.modules.ai.providers.deepseek import DeepSeekProvider
from app.modules.ai.schemas import AIProviderError
from app.modules.recommendations.models import RecommendationSession
from app.modules.travel_planning.models import TravelPlanDraft
from app.modules.travel_planning.schemas import (
    TravelPlanDay,
    TravelPlanItem,
    TravelPlanPayload,
    TravelPlanResponse,
)

TRAVEL_PLAN_SYSTEM_PROMPT = (
    "你是旅行计划草稿助手。只根据输入的城市、日期、人数、偏好和民宿区域生成可编辑草稿。"
    "不要虚构景点开放时间、距离、价格、交通班次或预订结果；未知信息写‘待确认’。"
    "必须返回 JSON，包含 summary、days 和 warnings。days 每项包含 date、title、items；"
    "items 每项包含 time_label、activity、reason、note。每天 1 至 5 项，日期必须覆盖输入的"
    "入住日至离店日（含离店日），所有安排都是待确认草稿。不要输出 Markdown。"
)


class TravelPlanRangeError(ValueError):
    pass


class TravelPlanService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, recommendation_id: str) -> TravelPlanResponse | None:
        recommendation = await self.session.scalar(
            select(RecommendationSession)
            .where(RecommendationSession.public_id == recommendation_id)
            .options(selectinload(RecommendationSession.results))
        )
        if recommendation is None:
            return None
        if (recommendation.check_out - recommendation.check_in).days + 1 > 14:
            raise TravelPlanRangeError("Travel plan drafts support up to 14 days")
        existing = await self.session.scalar(
            select(TravelPlanDraft).where(
                TravelPlanDraft.recommendation_session_id == recommendation.id
            )
        )
        if existing is not None:
            return self._response(existing, recommendation_id)

        payload, provider, model, usage, error_code = await self._generate(recommendation)
        now = datetime.now(UTC).replace(tzinfo=None)
        draft = TravelPlanDraft(
            public_id=str(uuid4()),
            recommendation_session_id=recommendation.id,
            city=recommendation.city,
            check_in=recommendation.check_in,
            check_out=recommendation.check_out,
            guest_count=recommendation.guest_count,
            status="draft",
            provider=provider,
            model=model,
            prompt_tokens=usage[0],
            completion_tokens=usage[1],
            total_tokens=usage[2],
            error_code=error_code,
            summary=payload.summary,
            payload=payload.model_dump(mode="json"),
            created_at=now,
            updated_at=now,
        )
        self.session.add(draft)
        await self.session.commit()
        return self._response(draft, recommendation_id)

    async def history(self, user_id: int) -> list[TravelPlanResponse]:
        rows = (
            await self.session.execute(
                select(TravelPlanDraft, RecommendationSession.public_id)
                .join(
                    RecommendationSession,
                    RecommendationSession.id == TravelPlanDraft.recommendation_session_id,
                )
                .where(RecommendationSession.user_id == user_id)
                .order_by(TravelPlanDraft.created_at.desc())
                .limit(50)
            )
        ).all()
        return [self._response(draft, recommendation_id) for draft, recommendation_id in rows]

    async def _generate(
        self, recommendation: RecommendationSession
    ) -> tuple[TravelPlanPayload, str, str, tuple[int | None, int | None, int | None], str | None]:
        dates = self._dates(recommendation.check_in, recommendation.check_out)
        provider = None
        if settings.deepseek_enabled and settings.deepseek_api_key:
            provider = DeepSeekProvider(
                api_key=settings.deepseek_api_key,
                base_url=settings.deepseek_base_url,
                model=settings.deepseek_model,
                timeout_seconds=settings.ai_timeout_seconds,
            )
        if provider:
            try:
                completion = await provider.complete_json(
                    TRAVEL_PLAN_SYSTEM_PROMPT,
                    json.dumps(
                        {
                            "city": recommendation.city,
                            "check_in": recommendation.check_in.isoformat(),
                            "check_out": recommendation.check_out.isoformat(),
                            "guests": recommendation.guest_count,
                            "preferences": recommendation.request_payload,
                            "listing_districts": [
                                result.district for result in recommendation.results
                            ],
                            "required_dates": [item.isoformat() for item in dates],
                        },
                        ensure_ascii=False,
                    ),
                )
                payload = TravelPlanPayload.model_validate_json(completion.content)
                if {day.date for day in payload.days} != set(dates):
                    raise AIProviderError("date_mismatch", "Travel plan dates do not match stay")
                return (
                    payload,
                    completion.provider,
                    completion.model,
                    (
                        completion.prompt_tokens,
                        completion.completion_tokens,
                        completion.total_tokens,
                    ),
                    None,
                )
            except (AIProviderError, ValueError) as error:
                error_code = (
                    error.code if isinstance(error, AIProviderError) else "schema_validation"
                )
        else:
            error_code = "not_configured"
        return (
            self._local_payload(recommendation, dates),
            "local",
            "evidence-template-v1",
            (None, None, None),
            error_code,
        )

    @staticmethod
    def _dates(check_in: date, check_out: date) -> list[date]:
        return [
            check_in + timedelta(days=offset) for offset in range((check_out - check_in).days + 1)
        ]

    @staticmethod
    def _local_payload(
        recommendation: RecommendationSession, dates: list[date]
    ) -> TravelPlanPayload:
        days = []
        for index, current in enumerate(dates):
            if index == 0:
                title = "抵达与入住"
                activity = f"抵达{recommendation.city}，前往已选民宿办理入住"
            elif index == len(dates) - 1:
                title = "收尾与离店"
                activity = "整理行李并预留离店时间，核对退订和交通安排"
            else:
                title = "自由探索日"
                activity = f"围绕{recommendation.city}和已选民宿所在区域安排轻松探索"
            days.append(
                TravelPlanDay(
                    date=current,
                    title=title,
                    items=[
                        TravelPlanItem(
                            time_label="全天",
                            activity=activity,
                            reason="根据当前入住日期和目的地生成的基础草稿",
                            note="具体地点、开放时间和交通方式待确认",
                        )
                    ],
                )
            )
        return TravelPlanPayload(
            summary=(
                f"这是围绕{recommendation.city}住宿安排生成的 {len(dates)} 天旅行草稿，"
                "请结合实际开放时间和交通情况调整。"
            ),
            days=days,
            warnings=["当前为旅行计划草稿，景点、交通和营业时间需要出发前自行确认。"],
        )

    @staticmethod
    def _response(draft: TravelPlanDraft, recommendation_id: str) -> TravelPlanResponse:
        payload = TravelPlanPayload.model_validate(draft.payload)
        return TravelPlanResponse(
            plan_id=draft.public_id,
            recommendation_session_id=recommendation_id,
            status="draft",
            city=draft.city,
            check_in=draft.check_in,
            check_out=draft.check_out,
            guests=draft.guest_count,
            provider=draft.provider,
            model=draft.model,
            summary=payload.summary,
            days=payload.days,
            warnings=payload.warnings,
            created_at=draft.created_at,
        )
