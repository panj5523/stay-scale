from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    title: str = Field(default="旅行需求对话", min_length=2, max_length=120)


class MessageCreate(BaseModel):
    content: str = Field(min_length=3, max_length=1000)


class ConversationMessageResponse(BaseModel):
    role: str
    content: str
    structured_result: dict[str, Any] | None
    created_at: datetime


class ConversationResponse(BaseModel):
    public_id: str
    title: str
    status: str
    created_at: datetime
    messages: list[ConversationMessageResponse] = Field(default_factory=list)
