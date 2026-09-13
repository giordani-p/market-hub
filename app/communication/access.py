"""Carga de Conversation e Order Item no escopo do participante."""

from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.auth.models import User, UserRole
from app.catalog.models import Offer
from app.communication.models import Conversation
from app.core.errors import ResourceNotFoundError
from app.orders.access import load_buyer_item, load_seller_item
from app.orders.models import Order, OrderItem


def load_participant_item(
    session: Session, item_id: UUID, user: User, *, for_update: bool = False
) -> OrderItem:
    """Carrega o Order Item se o usuario for Buyer ou Seller dele."""
    if user.role == UserRole.SELLER and user.seller_id is not None:
        return load_seller_item(session, item_id, user.seller_id, for_update=for_update)
    if user.role == UserRole.BUYER:
        return load_buyer_item(session, item_id, user.id, for_update=for_update)
    raise ResourceNotFoundError("Order item not found")


def participant_conversation_statement(
    conversation_id: UUID, user: User, *, for_update: bool
) -> Select[tuple[Conversation]]:
    """Monta o SELECT da Conversation no escopo do participante."""
    stmt = (
        select(Conversation)
        .join(OrderItem, Conversation.order_item_id == OrderItem.id)
        .join(Order, OrderItem.order_id == Order.id)
        .join(Offer, OrderItem.offer_id == Offer.id)
        .where(Conversation.id == conversation_id)
    )
    if user.role == UserRole.SELLER and user.seller_id is not None:
        stmt = stmt.where(Offer.seller_id == user.seller_id)
    elif user.role == UserRole.BUYER:
        stmt = stmt.where(Order.buyer_id == user.id)
    else:
        raise ResourceNotFoundError("Conversation not found")
    if for_update:
        stmt = stmt.with_for_update(of=Conversation)
    return stmt


def load_participant_conversation(
    session: Session, conversation_id: UUID, user: User, *, for_update: bool = False
) -> Conversation:
    conversation = session.scalar(
        participant_conversation_statement(conversation_id, user, for_update=for_update)
    )
    if conversation is None:
        raise ResourceNotFoundError("Conversation not found")
    return conversation


def load_seller_conversation(
    session: Session, conversation_id: UUID, seller_id: UUID, *, for_update: bool = False
) -> Conversation:
    stmt = (
        select(Conversation)
        .join(OrderItem, Conversation.order_item_id == OrderItem.id)
        .join(Offer, OrderItem.offer_id == Offer.id)
        .where(Conversation.id == conversation_id, Offer.seller_id == seller_id)
    )
    if for_update:
        stmt = stmt.with_for_update(of=Conversation)
    conversation = session.scalar(stmt)
    if conversation is None:
        raise ResourceNotFoundError("Conversation not found")
    return conversation
