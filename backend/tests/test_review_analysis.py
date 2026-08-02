import asyncio

import pytest

from app.modules.ai.providers.base import AIProvider
from app.modules.ai.schemas import AICompletion, AIProviderError
from app.modules.review_analysis.analyzer import DeepSeekReviewAnalyzer
from app.modules.review_analysis.schemas import ReviewAnalysisRequest
from app.modules.review_analysis.service import ReviewAnalysisService


class FakeProvider(AIProvider):
    async def complete_json(self, _system_prompt: str, _user_prompt: str) -> AICompletion:
        return AICompletion(
            content=(
                '{"summary":"评论整体认可卫生和位置，但有少量噪音反馈。",'
                '"topics":[{"code":"cleanliness","label":"卫生","sentiment":"positive",'
                '"mention_count":1,"evidence":["房间很干净"]}],'
                '"sentiment_distribution":{"positive":1,"neutral":0,"negative":0},'
                '"warnings":[]}'
            ),
            provider="deepseek",
            model="deepseek-v4-flash",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            finish_reason="stop",
        )


def test_review_analysis_validates_evidence_and_counts() -> None:
    result = asyncio.run(
        DeepSeekReviewAnalyzer(FakeProvider()).analyze(
            [{"content": "房间很干净，位置也方便", "external_id": "1"}]
        )
    )

    assert result.payload.topics[0].code == "cleanliness"
    assert result.completion.total_tokens == 150


class MismatchProvider(FakeProvider):
    async def complete_json(self, _system_prompt: str, _user_prompt: str) -> AICompletion:
        completion = await super().complete_json(_system_prompt, _user_prompt)
        return AICompletion(
            content=completion.content.replace('"positive":1', '"positive":0'),
            provider=completion.provider,
            model=completion.model,
            prompt_tokens=completion.prompt_tokens,
            completion_tokens=completion.completion_tokens,
            total_tokens=completion.total_tokens,
            finish_reason=completion.finish_reason,
        )


def test_review_analysis_rejects_sentiment_count_mismatch() -> None:
    with pytest.raises(AIProviderError, match="Sentiment counts"):
        asyncio.run(
            DeepSeekReviewAnalyzer(MismatchProvider()).analyze(
                [{"content": "房间很干净", "external_id": "1"}]
            )
        )


def test_local_review_analysis_produces_valid_internal_topics() -> None:
    request = ReviewAnalysisRequest.model_validate(
        {
            "reviews": [
                {
                    "external_id": "review-1",
                    "platform_code": "meituan",
                    "content": "房间很干净，位置也很方便",
                    "rating": 4.8,
                }
            ]
        }
    )

    result = ReviewAnalysisService._local_analysis(request)

    assert result.topics[0].code == "cleanliness"
    assert result.sentiment_distribution["positive"] == 1
