"""Schemas Pydantic do dominio de Notification."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class NotificationMetadata(BaseModel):
    previous_status: str
    new_status: str


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    recipient_id: UUID
    type: str
    title: str
    message: str
    entity_type: str
    entity_id: UUID
    metadata: NotificationMetadata
    created_at: datetime
    read_at: datetime | None


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    page: int
    page_size: int
    total: int


class UnreadCountResponse(BaseModel):
    unread_count: int = Field(ge=0)
