"""Tipos e modelo persistido de Notification."""

import uuid
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

ORDER_ITEM_STATUS_CHANGED = "ORDER_ITEM_STATUS_CHANGED"
CONVERSATION_STATUS_CHANGED = "CONVERSATION_STATUS_CHANGED"
CONVERSATION_PRIORITY_CHANGED = "CONVERSATION_PRIORITY_CHANGED"

ENTITY_ORDER_ITEM = "ORDER_ITEM"
ENTITY_CONVERSATION = "CONVERSATION"


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Notification(Base):
    """Aviso in-app de uma transicao de estado para um destinatario."""

    __tablename__ = "notifications"
    __table_args__ = (
        UniqueConstraint(
            "recipient_id",
            "type",
            "entity_type",
            "entity_id",
            "previous_status",
            "new_status",
            "changed_at",
            name="uq_notifications_idempotency",
        ),
        Index("ix_notifications_recipient_created_at", "recipient_id", "created_at"),
        Index(
            "ix_notifications_recipient_unread",
            "recipient_id",
            postgresql_where=text("read_at IS NULL"),
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    recipient_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    notification_type: Mapped[str] = mapped_column("type", String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    entity_id: Mapped[UUID] = mapped_column(nullable=False)
    previous_status: Mapped[str] = mapped_column(String(32), nullable=False)
    new_status: Mapped[str] = mapped_column(String(32), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
