"""Notifications in-app da seed de marketplace."""

from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.auth.seed import BUYER_ID, OPS_ID, SELLER_A_USER_ID, SELLER_TECH_USER_ID
from app.catalog.seed import add_if_missing
from app.communication.seed import conversation_id
from app.notifications.copy import build_copy
from app.notifications.models import (
    CONVERSATION_PRIORITY_CHANGED,
    CONVERSATION_STATUS_CHANGED,
    ENTITY_CONVERSATION,
    ENTITY_ORDER_ITEM,
    ORDER_ITEM_STATUS_CHANGED,
    Notification,
)
from app.orders.seed import item_id


def notification_id(n: int) -> UUID:
    return UUID(f"01000008-0000-4000-8000-{n:012x}")


def _row(
    n: int,
    recipient_id: UUID,
    notification_type: str,
    entity_type: str,
    entity_id: UUID,
    previous: str,
    new: str,
    changed_at: datetime,
    read_at: datetime | None,
) -> Notification:
    title, message = build_copy(
        notification_type=notification_type,
        previous_status=previous,
        new_status=new,
    )
    return Notification(
        id=notification_id(n),
        recipient_id=recipient_id,
        notification_type=notification_type,
        title=title,
        message=message,
        entity_type=entity_type,
        entity_id=entity_id,
        previous_status=previous,
        new_status=new,
        changed_at=changed_at,
        created_at=changed_at,
        read_at=read_at,
    )


def seed_demo_notifications(session: Session, now: datetime) -> None:
    """Insere inbox lida e nao lida para Loja A, Buyer Demo, Ops e Tech Hub."""
    hour = timedelta(hours=1)
    rows = (
        _row(
            1,
            SELLER_A_USER_ID,
            ORDER_ITEM_STATUS_CHANGED,
            ENTITY_ORDER_ITEM,
            item_id(6),
            "preparing",
            "in_transit",
            now - 5 * hour,
            None,
        ),
        _row(
            2,
            BUYER_ID,
            ORDER_ITEM_STATUS_CHANGED,
            ENTITY_ORDER_ITEM,
            item_id(6),
            "preparing",
            "in_transit",
            now - 5 * hour,
            None,
        ),
        _row(
            3,
            SELLER_A_USER_ID,
            CONVERSATION_PRIORITY_CHANGED,
            ENTITY_CONVERSATION,
            conversation_id(1),
            "high",
            "critical",
            now - 2 * hour,
            None,
        ),
        _row(
            4,
            OPS_ID,
            CONVERSATION_PRIORITY_CHANGED,
            ENTITY_CONVERSATION,
            conversation_id(1),
            "high",
            "critical",
            now - 2 * hour,
            None,
        ),
        _row(
            5,
            SELLER_A_USER_ID,
            ORDER_ITEM_STATUS_CHANGED,
            ENTITY_ORDER_ITEM,
            item_id(4),
            "placed",
            "preparing",
            now - 8 * hour,
            now - 7 * hour,
        ),
        _row(
            6,
            BUYER_ID,
            CONVERSATION_STATUS_CHANGED,
            ENTITY_CONVERSATION,
            conversation_id(13),
            "open",
            "closed",
            now - 30 * hour,
            now - 20 * hour,
        ),
        _row(
            7,
            SELLER_A_USER_ID,
            CONVERSATION_STATUS_CHANGED,
            ENTITY_CONVERSATION,
            conversation_id(13),
            "open",
            "closed",
            now - 30 * hour,
            now - 20 * hour,
        ),
        _row(
            8,
            SELLER_TECH_USER_ID,
            CONVERSATION_PRIORITY_CHANGED,
            ENTITY_CONVERSATION,
            conversation_id(6),
            "medium",
            "high",
            now - 6 * hour,
            None,
        ),
        _row(
            9,
            OPS_ID,
            CONVERSATION_PRIORITY_CHANGED,
            ENTITY_CONVERSATION,
            conversation_id(6),
            "medium",
            "high",
            now - 6 * hour,
            None,
        ),
        _row(
            10,
            BUYER_ID,
            ORDER_ITEM_STATUS_CHANGED,
            ENTITY_ORDER_ITEM,
            item_id(10),
            "in_transit",
            "delivered",
            now - 50 * hour,
            now - 40 * hour,
        ),
    )
    for row in rows:
        add_if_missing(session, row)
