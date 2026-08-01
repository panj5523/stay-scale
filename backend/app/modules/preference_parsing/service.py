from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
        self, session: AsyncSession, parser: ChinesePreferenceParser | None = None
    ) -> None:
        self.session = session
        self.parser = parser or ChinesePreferenceParser()

    async def parse(self, request: PreferenceParseRequest) -> PreferenceParseResponse:
        result = self.parser.parse(request.text, request.reference_date)
        now = datetime.now(UTC).replace(tzinfo=None)
        model = PreferenceParseSession(
            public_id=str(uuid4()),
            original_text=request.text.strip(),
            parser_name=PARSER_NAME,
            parser_version=PARSER_VERSION,
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
