from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.preference_parsing.schemas import PreferenceParseRequest
from app.modules.preference_parsing.service import PreferenceParsingService
from app.modules.users.models import UserAccount

from .models import AIConversation, AIConversationMessage
from .schemas import ConversationMessageResponse, ConversationResponse


class AIConversationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, user: UserAccount, title: str) -> ConversationResponse:
        conversation = AIConversation(public_id=str(uuid4()), user_id=user.id, title=title.strip())
        self.session.add(conversation)
        await self.session.commit()
        await self.session.refresh(conversation)
        return self._response(conversation, [])

    async def list_conversations(self, user: UserAccount) -> list[ConversationResponse]:
        conversations = (
            (
                await self.session.execute(
                    select(AIConversation)
                    .where(AIConversation.user_id == user.id)
                    .order_by(AIConversation.created_at.desc())
                    .limit(50)
                )
            )
            .scalars()
            .all()
        )
        return [self._response(item, []) for item in conversations]

    async def send(self, user: UserAccount, public_id: str, content: str) -> ConversationResponse:
        conversation = await self.session.scalar(
            select(AIConversation).where(
                AIConversation.public_id == public_id,
                AIConversation.user_id == user.id,
                AIConversation.status == "active",
            )
        )
        if conversation is None:
            raise FileNotFoundError("Conversation not found")
        user_message = AIConversationMessage(
            conversation_id=conversation.id, role="user", content=content.strip()
        )
        self.session.add(user_message)
        parsed = await PreferenceParsingService(self.session).parse(
            PreferenceParseRequest(text=content)
        )
        assistant_content = "我已经整理了你的旅行需求，请确认日期、人数和预算后生成推荐。"
        assistant_message = AIConversationMessage(
            conversation_id=conversation.id,
            role="assistant",
            content=assistant_content,
            structured_result=parsed.draft.model_dump(mode="json"),
        )
        self.session.add(assistant_message)
        await self.session.commit()
        await self.session.refresh(conversation)
        messages = (
            (
                await self.session.execute(
                    select(AIConversationMessage)
                    .where(AIConversationMessage.conversation_id == conversation.id)
                    .order_by(AIConversationMessage.created_at, AIConversationMessage.id)
                )
            )
            .scalars()
            .all()
        )
        return self._response(conversation, messages)

    @staticmethod
    def _response(
        conversation: AIConversation, messages: list[AIConversationMessage]
    ) -> ConversationResponse:
        return ConversationResponse(
            public_id=conversation.public_id,
            title=conversation.title,
            status=conversation.status,
            created_at=conversation.created_at,
            messages=[
                ConversationMessageResponse(
                    role=item.role,
                    content=item.content,
                    structured_result=item.structured_result,
                    created_at=item.created_at,
                )
                for item in messages
            ],
        )
