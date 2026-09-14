"""Schemas Pydantic do dominio de Communication."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

ConversationStatus = Literal["open", "closed"]
ConversationReason = Literal[
    "atraso",
    "troca",
    "devolucao",
    "reclamacao",
    "suporte",
    "elogio",
    "outros",
]
MessageAuthorType = Literal["buyer", "seller", "system"]


class CreateConversationRequest(BaseModel):
    reason: ConversationReason


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_item_id: UUID
    reason: str
    status: str
    created_at: datetime
    updated_at: datetime
    last_interaction_at: datetime
    effective_priority: str


class CreateMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=2000)

    @field_validator("content")
    @classmethod
    def strip_and_reject_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Message content cannot be empty")
        if len(stripped) > 2000:
            raise ValueError("Message content cannot exceed 2000 characters")
        return stripped


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    author_type: str
    author_user_id: UUID | None
    content: str
    created_at: datetime


class MessageListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[MessageResponse]
    from_: datetime = Field(alias="from")
    to: datetime
    has_older: bool
