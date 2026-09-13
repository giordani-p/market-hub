"""Modelos persistidos de Conversation e Message."""

import uuid
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Conversation(Base):
    """Comunicacao entre Buyer e Seller sobre um Order Item."""

    __tablename__ = "conversations"
    __table_args__ = (
        Index(
            "uq_conversations_open_order_item",
            "order_item_id",
            unique=True,
            postgresql_where=text("status = 'open'"),
        ),
        Index("ix_conversations_last_interaction_at", "last_interaction_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    order_item_id: Mapped[UUID] = mapped_column(
        ForeignKey("order_items.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    reason: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    last_interaction_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Message(Base):
    """Texto imutavel enviado em uma Conversation."""

    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_messages_conversation_created_at", "conversation_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="RESTRICT"), nullable=False
    )
    author_type: Mapped[str] = mapped_column(String(20), nullable=False)
    author_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    content: Mapped[str] = mapped_column(String(2000), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
