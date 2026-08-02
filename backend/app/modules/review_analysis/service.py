from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.ai.providers.deepseek import DeepSeekProvider
from app.modules.ai.schemas import AIProviderError
from app.modules.listings.models import CanonicalListing
from app.modules.review_analysis.analyzer import (
    AIReviewAnalysisPayload,
    DeepSeekReviewAnalyzer,
)
from app.modules.review_analysis.models import ListingReview, ReviewAnalysisSnapshot
from app.modules.review_analysis.schemas import (
    ReviewAnalysisRequest,
    ReviewAnalysisResponse,
    ReviewTopic,
)


class ReviewAnalysisService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def analyze(
        self, listing_public_id: str, request: ReviewAnalysisRequest
    ) -> ReviewAnalysisResponse | None:
        listing = await self.session.scalar(
            select(CanonicalListing).where(CanonicalListing.public_id == listing_public_id)
        )
        if listing is None:
            return None
        existing_reviews = await self.session.scalars(
            select(ListingReview).where(ListingReview.canonical_listing_id == listing.id)
        )
        existing_keys = {(review.platform_code, review.external_id) for review in existing_reviews}
        duplicate_count = 0
        for review in request.reviews:
            if (review.platform_code, review.external_id) in existing_keys:
                duplicate_count += 1
                continue
            self.session.add(
                ListingReview(
                    canonical_listing_id=listing.id,
                    platform_code=review.platform_code,
                    external_id=review.external_id,
                    content=review.content,
                    rating=review.rating,
                    review_date=review.review_date,
                    source_url=review.source_url,
                )
            )

        analyzer = self._configured_analyzer()
        error_code = None
        if analyzer:
            try:
                analyzed = await analyzer.analyze(
                    [item.model_dump(mode="json") for item in request.reviews]
                )
                payload = analyzed.payload
                provider = analyzed.completion.provider
                model = analyzed.completion.model
                usage = (
                    analyzed.completion.prompt_tokens,
                    analyzed.completion.completion_tokens,
                    analyzed.completion.total_tokens,
                )
            except AIProviderError as error:
                error_code = error.code
        else:
            error_code = "not_configured"

        if error_code:
            payload = self._local_analysis(request)
            provider, model, usage = "local", "keyword-v1", (None, None, None)
        if duplicate_count:
            payload.warnings.append(f"已跳过 {duplicate_count} 条已存在的重复评论来源。")
        now = datetime.now(UTC).replace(tzinfo=None)
        snapshot = ReviewAnalysisSnapshot(
            public_id=str(uuid4()),
            canonical_listing_id=listing.id,
            review_count=len(request.reviews),
            provider=provider,
            model=model,
            prompt_tokens=usage[0],
            completion_tokens=usage[1],
            total_tokens=usage[2],
            error_code=error_code,
            summary=payload.summary,
            topics=[topic.model_dump(mode="json") for topic in payload.topics],
            sentiment_distribution=payload.sentiment_distribution,
            warnings=payload.warnings,
            created_at=now,
            updated_at=now,
        )
        self.session.add(snapshot)
        await self.session.commit()
        return self._response(snapshot, listing_public_id)

    @staticmethod
    def _configured_analyzer() -> DeepSeekReviewAnalyzer | None:
        if not settings.deepseek_enabled or not settings.deepseek_api_key:
            return None
        return DeepSeekReviewAnalyzer(
            DeepSeekProvider(
                api_key=settings.deepseek_api_key,
                base_url=settings.deepseek_base_url,
                model=settings.deepseek_model,
                timeout_seconds=settings.ai_timeout_seconds,
            )
        )

    @staticmethod
    def _local_analysis(request: ReviewAnalysisRequest) -> AIReviewAnalysisPayload:
        groups = {
            "cleanliness": ("卫生", ("干净", "整洁", "卫生")),
            "location": ("位置", ("位置", "交通", "方便")),
            "service": ("服务", ("服务", "房东", "沟通")),
            "noise": ("噪音", ("噪音", "吵", "安静")),
        }
        topics = []
        positive = neutral = negative = 0
        for review in request.reviews:
            text = review.content
            if review.rating is not None:
                if review.rating >= 4:
                    positive += 1
                elif review.rating <= 2:
                    negative += 1
                else:
                    neutral += 1
            else:
                neutral += 1
            for code, (label, keywords) in groups.items():
                if any(keyword in text for keyword in keywords):
                    sentiment = (
                        "negative"
                        if any(word in text for word in ("吵", "差", "脏"))
                        else "positive"
                    )
                    topics.append(
                        ReviewTopic(
                            code=code,
                            label=label,
                            sentiment=sentiment,
                            mention_count=1,
                            evidence=[text[:80]],
                        )
                    )
        merged = {}
        for topic in topics:
            key = (topic.code, topic.sentiment)
            if key not in merged:
                merged[key] = topic
            else:
                merged[key].mention_count += topic.mention_count
                if len(merged[key].evidence) < 3:
                    merged[key].evidence.append(topic.evidence[0])
        topic_list = list(merged.values())[:8]
        return AIReviewAnalysisPayload(
            summary=(
                f"共分析 {len(request.reviews)} 条评论，当前为规则初筛结果，建议结合原评论复核。"
            ),
            topics=topic_list,
            sentiment_distribution={
                "positive": positive,
                "neutral": neutral,
                "negative": negative,
            },
            warnings=["当前为本地关键词初筛，不代表完整语义理解。"],
        )

    @staticmethod
    def _response(
        snapshot: ReviewAnalysisSnapshot, listing_public_id: str
    ) -> ReviewAnalysisResponse:
        return ReviewAnalysisResponse(
            analysis_id=snapshot.public_id,
            listing_public_id=listing_public_id,
            review_count=snapshot.review_count,
            provider=snapshot.provider,
            model=snapshot.model,
            summary=snapshot.summary,
            topics=[ReviewTopic.model_validate(topic) for topic in snapshot.topics],
            sentiment_distribution=snapshot.sentiment_distribution,
            warnings=snapshot.warnings,
            created_at=snapshot.created_at,
        )
