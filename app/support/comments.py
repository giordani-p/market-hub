"""Regras de InternalComment."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import User, UserRole
from app.core.errors import ForbiddenError
from app.core.events import InternalCommentCreated, record_event
from app.support.models import InternalComment


def author_type_for(user: User) -> str:
    if user.role == UserRole.SELLER:
        return "seller"
    if user.role == UserRole.OPS:
        return "ops"
    raise ForbiddenError("Seller or Ops role required")


def create_comment(
    session: Session, order_item_id: UUID, user: User, content: str
) -> InternalComment:
    comment = InternalComment(
        order_item_id=order_item_id,
        author_id=user.id,
        author_type=author_type_for(user),
        content=content,
    )
    session.add(comment)
    session.flush()
    record_event(
        session,
        InternalCommentCreated(comment_id=comment.id, order_item_id=comment.order_item_id),
    )
    return comment


def list_comments(session: Session, order_item_id: UUID) -> list[InternalComment]:
    return list(
        session.scalars(
            select(InternalComment)
            .where(InternalComment.order_item_id == order_item_id)
            .order_by(InternalComment.created_at.asc())
        )
    )
