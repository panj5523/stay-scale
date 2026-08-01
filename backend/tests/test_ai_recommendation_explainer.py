import asyncio

import pytest

from app.modules.ai.recommendation_explainer import DeepSeekRecommendationExplainer
from app.modules.ai.schemas import AICompletion, AIProviderError


class FakeProvider:
    def __init__(self, content: str) -> None:
        self.content = content

    async def complete_json(self, _system_prompt: str, _user_prompt: str) -> AICompletion:
        return AICompletion(
            content=self.content,
            provider="deepseek",
            model="deepseek-v4-flash",
            prompt_tokens=120,
            completion_tokens=60,
            total_tokens=180,
            finish_reason="stop",
        )


def test_explanations_require_exact_listing_ids() -> None:
    explainer = DeepSeekRecommendationExplainer(
        FakeProvider(
            '{"explanations":['
            '{"listing_public_id":"DL_1","explanation":"价格在预算范围内，但可比平台数量较少。"},'
            '{"listing_public_id":"DL_2","explanation":"评分表现较好，但没有完全满足设施偏好。"}'
            "]}"
        )
    )

    result = asyncio.run(explainer.explain("[]", {"DL_1", "DL_2"}))

    assert set(result.explanations) == {"DL_1", "DL_2"}
    assert result.completion.total_tokens == 180


def test_unexpected_listing_id_is_rejected_for_fallback() -> None:
    explainer = DeepSeekRecommendationExplainer(
        FakeProvider(
            '{"explanations":['
            '{"listing_public_id":"UNKNOWN","explanation":"这是一段不能关联到证据的推荐说明。"}'
            "]}"
        )
    )

    with pytest.raises(AIProviderError) as error:
        asyncio.run(explainer.explain("[]", {"DL_1"}))

    assert error.value.code == "evidence_mismatch"
