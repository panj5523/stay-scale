from dataclasses import dataclass

from pydantic import BaseModel, Field, model_validator

from app.modules.ai.providers.base import AIProvider
from app.modules.ai.schemas import AICompletion, AIProviderError


class AIRecommendationExplanation(BaseModel):
    listing_public_id: str = Field(min_length=1, max_length=32)
    explanation: str = Field(min_length=10, max_length=300)


class AIRecommendationExplanationPayload(BaseModel):
    explanations: list[AIRecommendationExplanation] = Field(min_length=1, max_length=10)

    @model_validator(mode="after")
    def reject_duplicate_listing_ids(self) -> "AIRecommendationExplanationPayload":
        ids = [item.listing_public_id for item in self.explanations]
        if len(ids) != len(set(ids)):
            raise ValueError("listing_public_id must be unique")
        return self


@dataclass(frozen=True)
class AIRecommendationExplanations:
    explanations: dict[str, str]
    completion: AICompletion


class DeepSeekRecommendationExplainer:
    SYSTEM_PROMPT = """你是民宿推荐说明编辑。输入内容全部来自后端已经计算完成的结构化证据。
只负责把证据改写成简洁、自然、克制的中文，不得修改排名，不得新增设施、位置、价格、评分、
平台、交通、景观或安全事实。必须同时说明主要优势和已提供的取舍或风险；没有提供的事实不要猜测。
只返回 JSON：{"explanations":[{"listing_public_id":"原始ID","explanation":"80至160字说明"}]}。
每个输入民宿必须且只能返回一项，listing_public_id 必须原样返回。不要输出 Markdown。"""

    def __init__(self, provider: AIProvider) -> None:
        self.provider = provider

    async def explain(
        self, evidence_json: str, expected_ids: set[str]
    ) -> AIRecommendationExplanations:
        completion = await self.provider.complete_json(
            self.SYSTEM_PROMPT,
            f"请严格根据以下 JSON 证据生成推荐说明：\n{evidence_json}",
        )
        try:
            payload = AIRecommendationExplanationPayload.model_validate_json(completion.content)
        except ValueError as exc:
            raise AIProviderError("schema_validation", "DeepSeek JSON failed validation") from exc

        returned_ids = {item.listing_public_id for item in payload.explanations}
        if returned_ids != expected_ids:
            raise AIProviderError("evidence_mismatch", "DeepSeek returned unexpected listing IDs")
        return AIRecommendationExplanations(
            explanations={
                item.listing_public_id: item.explanation for item in payload.explanations
            },
            completion=completion,
        )
