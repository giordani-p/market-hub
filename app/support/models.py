"""Modelos persistidos de Support/Ops."""

import uuid
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class InternalComment(Base):
    """Comunicacao operacional imutavel entre Seller e Ops sobre um Order Item."""

    __tablename__ = "internal_comments"
    __table_args__ = (Index("ix_internal_comments_item_created_at", "order_item_id", "created_at"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    order_item_id: Mapped[UUID] = mapped_column(
        ForeignKey("order_items.id", ondelete="RESTRICT"), nullable=False
    )
    author_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    author_type: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(String(2000), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
