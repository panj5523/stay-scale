from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.modules.preference_parsing.schemas import (
    PreferenceConfirmationRequest,
    PreferenceParseRequest,
    PreferenceParseResponse,
)
from app.modules.preference_parsing.service import PreferenceParsingService

router = APIRouter()


@router.post("", response_model=PreferenceParseResponse, status_code=201)
async def parse_preferences(
    request: PreferenceParseRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> PreferenceParseResponse:
    return await PreferenceParsingService(session).parse(request)


@router.get("/{session_id}", response_model=PreferenceParseResponse)
async def get_preference_parse(
    session_id: str,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> PreferenceParseResponse:
    result = await PreferenceParsingService(session).get(session_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Preference parse session not found")
    return result


@router.patch("/{session_id}/confirm", response_model=PreferenceParseResponse)
async def confirm_preference_parse(
    session_id: str,
    request: PreferenceConfirmationRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> PreferenceParseResponse:
    result = await PreferenceParsingService(session).confirm(session_id, request)
    if result is None:
        raise HTTPException(status_code=404, detail="Preference parse session not found")
    return result
