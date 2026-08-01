from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from app.modules.ai.providers.base import AIProvider
from app.modules.ai.schemas import AICompletion, AIProviderError
from app.modules.preference_parsing.parser import ParseResult
from app.modules.preference_parsing.schemas import ExtractionEvidence, ParsedPreferences


class AIPreferencePayload(BaseModel):
    draft: ParsedPreferences
    evidence: list[ExtractionEvidence] = Field(default_factory=list, max_length=20)
    confidence: Decimal = Field(ge=0, le=1)
    warnings: list[str] = Field(default_factory=list, max_length=8)


@dataclass(frozen=True)
class AIParsedPreferences:
    result: ParseResult
    completion: AICompletion


class DeepSeekPreferenceParser:
    SYSTEM_PROMPT = """你是旅行需求结构化解析器。只提取用户明确表达的信息，不猜测价格、日期或地点。
必须只返回一个 JSON 对象，不要 Markdown。JSON 格式：
{"draft":{"city":null,"check_in":null,"check_out":null,"guests":null,
"budget_total":null,"preferred_facilities":[],"preferred_districts":[],
"travel_style":null,"risk_aversion":"medium"},"evidence":[],"confidence":0.0,"warnings":[]}
travel_style 只能是 value、comfort、scenery、family 或 null。
risk_aversion 只能是 low、medium、high。
设施代码只能使用 wifi、air_conditioning、kitchen、washer、parking、sea_view、ground_floor。
evidence 每项包含 field、matched_text、normalized_value，matched_text 必须来自用户原文。
日期使用 YYYY-MM-DD；无法确定的字段返回 null。"""

    def __init__(self, provider: AIProvider) -> None:
        self.provider = provider

    async def parse(self, text: str, reference_date: date) -> AIParsedPreferences:
        completion = await self.provider.complete_json(
            self.SYSTEM_PROMPT,
            f"参考日期：{reference_date.isoformat()}\n用户需求：{text}\n请输出 JSON。",
        )
        try:
            payload = AIPreferencePayload.model_validate_json(completion.content)
        except ValueError as exc:
            raise AIProviderError("schema_validation", "DeepSeek JSON failed validation") from exc
        evidence = [item for item in payload.evidence if item.matched_text in text]
        required = ("city", "check_in", "check_out", "guests")
        missing = [field for field in required if getattr(payload.draft, field) is None]
        warnings = list(payload.warnings)
        if missing:
            warnings.append("仍有必要信息未识别，请在确认前补充。")
        return AIParsedPreferences(
            result=ParseResult(
                draft=payload.draft,
                evidence=evidence,
                missing_fields=missing,
                warnings=list(dict.fromkeys(warnings)),
                confidence=payload.confidence.quantize(Decimal("0.001")),
            ),
            completion=completion,
        )
