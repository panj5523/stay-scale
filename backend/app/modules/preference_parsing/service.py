from datetime import UTC, date, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.ai.preference_parser import DeepSeekPreferenceParser
from app.modules.ai.providers.deepseek import DeepSeekProvider
from app.modules.ai.schemas import AIProviderError
from app.modules.preference_parsing.models import PreferenceParseSession
from app.modules.preference_parsing.parser import (
    PARSER_NAME,
    PARSER_VERSION,
    ChinesePreferenceParser,
)
from app.modules.preference_parsing.schemas import (
    ExtractionEvidence,
    ParsedPreferences,
    PreferenceConfirmationRequest,
    PreferenceParseRequest,
    PreferenceParseResponse,
)


class PreferenceParsingService:
    def __init__(
        self,
        session: AsyncSession,
        parser: ChinesePreferenceParser | None = None,
        ai_parser: DeepSeekPreferenceParser | None = None,
    ) -> None:
        self.session = session
        self.parser = parser or ChinesePreferenceParser()
        self.ai_parser = ai_parser or self._configured_ai_parser()

    async def parse(self, request: PreferenceParseRequest) -> PreferenceParseResponse:
        parser_name = PARSER_NAME
        parser_version = PARSER_VERSION
        prompt_tokens = None
        completion_tokens = None
        total_tokens = None
        ai_error_code = None
        if self.ai_parser:
            try:
                ai_parsed = await self.ai_parser.parse(
                    request.text, request.reference_date or date.today()
                )
                result = ai_parsed.result
                parser_name = ai_parsed.completion.provider
                parser_version = ai_parsed.completion.model
                prompt_tokens = ai_parsed.completion.prompt_tokens
                completion_tokens = ai_parsed.completion.completion_tokens
                total_tokens = ai_parsed.completion.total_tokens
            except AIProviderError as error:
                result = self.parser.parse(request.text, request.reference_date)
                result.warnings.append("DeepSeek 暂时不可用，已使用本地规则完成解析。")
                ai_error_code = error.code
        else:
            result = self.parser.parse(request.text, request.reference_date)
        now = datetime.now(UTC).replace(tzinfo=None)
        model = PreferenceParseSession(
            public_id=str(uuid4()),
            original_text=request.text.strip(),
            parser_name=parser_name,
            parser_version=parser_version,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            ai_error_code=ai_error_code,
            confidence=result.confidence,
            parsed_payload=result.draft.model_dump(mode="json"),
            evidence=[item.model_dump(mode="json") for item in result.evidence],
            missing_fields=result.missing_fields,
            warnings=result.warnings,
            status="needs_confirmation",
            created_at=now,
            updated_at=now,
        )
        self.session.add(model)
        await self.session.commit()
        return self._response(model)

    @staticmethod
    def _configured_ai_parser() -> DeepSeekPreferenceParser | None:
        if not settings.deepseek_enabled or not settings.deepseek_api_key:
            return None
        provider = DeepSeekProvider(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            model=settings.deepseek_model,
            timeout_seconds=settings.ai_timeout_seconds,
        )
        return DeepSeekPreferenceParser(provider)

    async def get(self, public_id: str) -> PreferenceParseResponse | None:
        model = await self.session.scalar(
            select(PreferenceParseSession).where(PreferenceParseSession.public_id == public_id)
        )
        return self._response(model) if model else None

    async def confirm(
        self, public_id: str, request: PreferenceConfirmationRequest
    ) -> PreferenceParseResponse | None:
        model = await self.session.scalar(
            select(PreferenceParseSession).where(PreferenceParseSession.public_id == public_id)
        )
        if model is None:
            return None
        now = datetime.now(UTC).replace(tzinfo=None)
        model.confirmed_payload = request.preferences.model_dump(mode="json")
        model.status = "confirmed"
        model.missing_fields = []
        model.warnings = [
            warning
            for warning in model.warnings
            if warning != "仍有必要信息未识别，请在确认前补充。"
        ]
        model.confirmed_at = now
        model.updated_at = now
        await self.session.commit()
        return self._response(model)

    @staticmethod
    def _response(model: PreferenceParseSession) -> PreferenceParseResponse:
        payload = model.confirmed_payload or model.parsed_payload
        return PreferenceParseResponse(
            session_id=model.public_id,
            status=model.status,
            parser_name=model.parser_name,
            parser_version=model.parser_version,
            confidence=model.confidence,
            original_text=model.original_text,
            draft=ParsedPreferences.model_validate(payload),
            evidence=[ExtractionEvidence.model_validate(item) for item in model.evidence],
            missing_fields=model.missing_fields,
            warnings=model.warnings,
            created_at=model.created_at,
            confirmed_at=model.confirmed_at,
        )
