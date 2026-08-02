import json
from dataclasses import dataclass

from pydantic import BaseModel, Field, model_validator

from app.modules.ai.providers.base import AIProvider
from app.modules.ai.schemas import AICompletion, AIProviderError


class AIReviewTopic(BaseModel):
    code: str = Field(min_length=1, max_length=32)
    label: str = Field(min_length=1, max_length=40)
    sentiment: str
    mention_count: int = Field(ge=1, le=50)
    evidence: list[str] = Field(min_length=1, max_length=3)


class AIReviewAnalysisPayload(BaseModel):
    summary: str = Field(min_length=10, max_length=500)
    topics: list[AIReviewTopic] = Field(max_length=8)
    sentiment_distribution: dict[str, int]
    warnings: list[str] = Field(default_factory=list, max_length=8)

    @model_validator(mode="after")
    def validate_sentiment_distribution(self) -> "AIReviewAnalysisPayload":
        allowed = {"positive", "neutral", "negative"}
        if set(self.sentiment_distribution) - allowed:
            raise ValueError("unsupported sentiment label")
        if any(value < 0 for value in self.sentiment_distribution.values()):
            raise ValueError("sentiment counts cannot be negative")
        for topic in self.topics:
            if topic.sentiment not in allowed:
                raise ValueError("unsupported topic sentiment")
        return self


@dataclass(frozen=True)
class AIReviewAnalysis:
    payload: AIReviewAnalysisPayload
    completion: AICompletion


class DeepSeekReviewAnalyzer:
    SYSTEM_PROMPT = (
        "你是民宿评论分析器。只分析输入的原始评论，不补充评论中没有的事实。"
        "请提取最多 8 个高频主题，判断正面、中性或负面，并引用原评论中的短语作为 evidence。"
        "mention_count 是涉及该主题的评论数量，不要把同一条评论重复计数。"
        "只返回 JSON，包含 summary、topics、sentiment_distribution、warnings，不要输出 Markdown。"
    )

    def __init__(self, provider: AIProvider) -> None:
        self.provider = provider

    async def analyze(self, reviews: list[dict[str, object]]) -> AIReviewAnalysis:
        completion = await self.provider.complete_json(
            self.SYSTEM_PROMPT,
            json.dumps({"reviews": reviews}, ensure_ascii=False, separators=(",", ":")),
        )
        try:
            payload = AIReviewAnalysisPayload.model_validate_json(completion.content)
        except ValueError as exc:
            raise AIProviderError(
                "schema_validation", "DeepSeek review JSON failed validation"
            ) from exc
        payload.sentiment_distribution = {
            label: payload.sentiment_distribution.get(label, 0)
            for label in ("positive", "neutral", "negative")
        }
        review_count = len(reviews)
        if sum(payload.sentiment_distribution.values()) != review_count:
            raise AIProviderError("count_mismatch", "Sentiment counts do not match review count")
        for topic in payload.topics:
            review_texts = [str(item.get("content", "")) for item in reviews]
            if any(
                all(evidence not in text for text in review_texts) for evidence in topic.evidence
            ):
                raise AIProviderError(
                    "evidence_mismatch", "Topic evidence is not present in reviews"
                )
        return AIReviewAnalysis(payload=payload, completion=completion)
