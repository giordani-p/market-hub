"""Destinatarios por tipo de Notification. Sem regra de transicao de status."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import User, UserRole
from app.catalog.models import Offer
from app.communication.models import Conversation
from app.notifications.models import (
    CONVERSATION_PRIORITY_CHANGED,
    ENTITY_CONVERSATION,
    ENTITY_ORDER_ITEM,
)
from app.orders.models import Order, OrderItem


def seller_user_id(session: Session, seller_id: UUID) -> UUID | None:
    return session.scalar(select(User.id).where(User.seller_id == seller_id))


def ops_user_ids(session: Session) -> list[UUID]:
    return list(session.scalars(select(User.id).where(User.role == UserRole.OPS)))


def buyer_and_seller_for_item(session: Session, item: OrderItem) -> list[UUID]:
    order = session.get(Order, item.order_id)
    offer = session.get(Offer, item.offer_id)
    if order is None or offer is None:
        return []
    recipients = [order.buyer_id]
    seller_id = seller_user_id(session, offer.seller_id)
    if seller_id is not None:
        recipients.append(seller_id)
    return recipients


def seller_and_ops_for_item(session: Session, item: OrderItem) -> list[UUID]:
    offer = session.get(Offer, item.offer_id)
    recipients: list[UUID] = []
    if offer is not None:
        seller_id = seller_user_id(session, offer.seller_id)
        if seller_id is not None:
            recipients.append(seller_id)
    recipients.extend(ops_user_ids(session))
    return recipients


def resolve_recipients(
    session: Session, *, notification_type: str, entity_id: UUID, entity_type: str
) -> list[UUID]:
    item = _load_item(session, entity_id=entity_id, entity_type=entity_type)
    if item is None:
        return []
    if notification_type == CONVERSATION_PRIORITY_CHANGED:
        return seller_and_ops_for_item(session, item)
    return buyer_and_seller_for_item(session, item)


def _load_item(session: Session, *, entity_id: UUID, entity_type: str) -> OrderItem | None:
    if entity_type == ENTITY_ORDER_ITEM:
        return session.get(OrderItem, entity_id)
    if entity_type != ENTITY_CONVERSATION:
        return None
    conversation = session.get(Conversation, entity_id)
    if conversation is None:
        return None
    return session.get(OrderItem, conversation.order_item_id)
