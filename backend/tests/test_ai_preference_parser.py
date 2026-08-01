import asyncio
from datetime import date

import pytest

from app.modules.ai.preference_parser import DeepSeekPreferenceParser
from app.modules.ai.schemas import AICompletion, AIProviderError


class FakeProvider:
    def __init__(self, content: str) -> None:
        self.content = content

    async def complete_json(self, _system_prompt: str, _user_prompt: str) -> AICompletion:
        return AICompletion(
            content=self.content,
            provider="deepseek",
            model="deepseek-v4-flash",
            prompt_tokens=80,
            completion_tokens=40,
            total_tokens=120,
            finish_reason="stop",
        )


def test_deepseek_json_output_is_validated_and_untrusted_evidence_is_dropped() -> None:
    parser = DeepSeekPreferenceParser(
        FakeProvider(
            '{"draft":{"city":"大理市","check_in":"2026-10-02",'
            '"check_out":"2026-10-05","guests":2,"budget_total":1600,'
            '"preferred_facilities":["sea_view"],"preferred_districts":[],'
            '"travel_style":"scenery","risk_aversion":"medium"},'
            '"evidence":[{"field":"city","matched_text":"大理","normalized_value":"大理市"},'
            '{"field":"city","matched_text":"不存在的城市","normalized_value":"丽江市"}],'
            '"confidence":0.92,"warnings":[]}'
        )
    )

    result = asyncio.run(parser.parse("两个人去大理，10月2日到5日看海", date(2026, 8, 1)))

    assert result.result.draft.city == "大理市"
    assert len(result.result.evidence) == 1
    assert result.completion.total_tokens == 120


def test_deepseek_invalid_json_is_reported_for_local_fallback() -> None:
    parser = DeepSeekPreferenceParser(FakeProvider("not-json"))

    with pytest.raises(AIProviderError) as error:
        asyncio.run(parser.parse("去大理", date(2026, 8, 1)))

    assert error.value.code == "schema_validation"
