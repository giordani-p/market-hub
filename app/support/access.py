"""Carga de Order Item no escopo de Ops."""

from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.catalog.models import Offer, Product, Seller
from app.communication.models import Conversation
from app.core.errors import ResourceNotFoundError
from app.orders.models import Order, OrderItem


def load_ops_item(session: Session, item_id: UUID) -> OrderItem:
    """Carrega qualquer Order Item existente."""
    item = session.get(OrderItem, item_id)
    if item is None:
        raise ResourceNotFoundError("Order item not found")
    return item


def ops_list_statement() -> Select[tuple[OrderItem, Product, Order, User, Seller]]:
    """Itens de todos os Sellers, com produto, pedido, buyer e seller."""
    return (
        select(OrderItem, Product, Order, User, Seller)
        .join(Offer, OrderItem.offer_id == Offer.id)
        .join(Product, Offer.product_id == Product.id)
        .join(Order, OrderItem.order_id == Order.id)
        .join(User, Order.buyer_id == User.id)
        .join(Seller, Offer.seller_id == Seller.id)
    )


def load_ops_item_context(
    session: Session, item_id: UUID
) -> tuple[OrderItem, Product, Order, User, Seller]:
    row = session.execute(
        select(OrderItem, Product, Order, User, Seller)
        .join(Offer, OrderItem.offer_id == Offer.id)
        .join(Product, Offer.product_id == Product.id)
        .join(Order, OrderItem.order_id == Order.id)
        .join(User, Order.buyer_id == User.id)
        .join(Seller, Offer.seller_id == Seller.id)
        .where(OrderItem.id == item_id)
    ).one_or_none()
    if row is None:
        raise ResourceNotFoundError("Order item not found")
    return row[0], row[1], row[2], row[3], row[4]


def load_ops_conversation(
    session: Session, conversation_id: UUID, *, for_update: bool = False
) -> Conversation:
    stmt = select(Conversation).where(Conversation.id == conversation_id)
    if for_update:
        stmt = stmt.with_for_update()
    conversation = session.scalar(stmt)
    if conversation is None:
        raise ResourceNotFoundError("Conversation not found")
    return conversation
