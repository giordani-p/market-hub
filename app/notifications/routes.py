"""Rotas de Notification do usuario autenticado."""

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser
from app.core.errors import ResourceNotFoundError
from app.database import get_session
from app.notifications.models import Notification
from app.notifications.schemas import (
    NotificationListResponse,
    NotificationMetadata,
    NotificationResponse,
    UnreadCountResponse,
)

SessionDep = Annotated[Session, Depends(get_session)]

router = APIRouter(tags=["notifications"])


def _to_response(notification: Notification) -> NotificationResponse:
    return NotificationResponse(
        id=notification.id,
        recipient_id=notification.recipient_id,
        type=notification.notification_type,
        title=notification.title,
        message=notification.message,
        entity_type=notification.entity_type,
        entity_id=notification.entity_id,
        metadata=NotificationMetadata(
            previous_status=notification.previous_status,
            new_status=notification.new_status,
        ),
        created_at=notification.created_at,
        read_at=notification.read_at,
    )


def _owned(session: Session, notification_id: UUID, user_id: UUID) -> Notification:
    notification = session.get(Notification, notification_id)
    if notification is None or notification.recipient_id != user_id:
        raise ResourceNotFoundError("Notification not found")
    return notification


@router.get(
    "/notifications",
    response_model=NotificationListResponse,
    summary="List notifications of the authenticated user",
)
def list_notifications(
    user: CurrentUser,
    session: SessionDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> NotificationListResponse:
    filters = Notification.recipient_id == user.id
    total = session.scalar(select(func.count()).where(filters)) or 0
    rows = session.scalars(
        select(Notification)
        .where(filters)
        .order_by(Notification.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return NotificationListResponse(
        items=[_to_response(row) for row in rows],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get(
    "/notifications/unread-count",
    response_model=UnreadCountResponse,
    summary="Count unread notifications of the authenticated user",
)
def unread_count(user: CurrentUser, session: SessionDep) -> UnreadCountResponse:
    count = session.scalar(
        select(func.count()).where(
            Notification.recipient_id == user.id,
            Notification.read_at.is_(None),
        )
    )
    return UnreadCountResponse(unread_count=count or 0)


@router.patch(
    "/notifications/read-all",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Mark all notifications of the authenticated user as read",
)
def mark_all_read(user: CurrentUser, session: SessionDep) -> Response:
    session.execute(
        update(Notification)
        .where(Notification.recipient_id == user.id, Notification.read_at.is_(None))
        .values(read_at=datetime.now(UTC))
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/notifications/{notification_id}/read",
    response_model=NotificationResponse,
    summary="Mark a notification as read",
)
def mark_read(
    notification_id: UUID, user: CurrentUser, session: SessionDep
) -> NotificationResponse:
    notification = _owned(session, notification_id, user.id)
    if notification.read_at is None:
        notification.read_at = datetime.now(UTC)
    return _to_response(notification)
