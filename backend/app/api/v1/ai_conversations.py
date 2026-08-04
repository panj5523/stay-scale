from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import rate_limit
from app.db.session import get_db_session
from app.modules.ai_conversations.schemas import (
    ConversationCreate,
    ConversationResponse,
    MessageCreate,
)
from app.modules.ai_conversations.service import AIConversationService
from app.modules.users.dependencies import require_user
from app.modules.users.models import UserAccount

router = APIRouter()


@router.post("/conversations", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    payload: ConversationCreate,
    user: Annotated[UserAccount, Depends(require_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ConversationResponse:
    return await AIConversationService(session).create(user, payload.title)


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    user: Annotated[UserAccount, Depends(require_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[ConversationResponse]:
    return await AIConversationService(session).list_conversations(user)


@router.post(
    "/conversations/{public_id}/messages",
    response_model=ConversationResponse,
    dependencies=[Depends(rate_limit("ai-message", 30))],
)
async def send_conversation_message(
    public_id: str,
    payload: MessageCreate,
    user: Annotated[UserAccount, Depends(require_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ConversationResponse:
    try:
        return await AIConversationService(session).send(user, public_id, payload.content)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
