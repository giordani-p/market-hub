"""Carga de Order Item no escopo do Seller ou do Buyer."""

from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.catalog.models import Offer, Product
from app.core.errors import ResourceNotFoundError
from app.orders.models import Order, OrderItem


def seller_item_statement(
    item_id: UUID, seller_id: UUID, *, for_update: bool
) -> Select[tuple[OrderItem]]:
    """Monta o SELECT do item no escopo do Seller."""
    stmt = (
        select(OrderItem)
        .join(Offer, OrderItem.offer_id == Offer.id)
        .where(OrderItem.id == item_id, Offer.seller_id == seller_id)
    )
    if for_update:
        stmt = stmt.with_for_update()
    return stmt


def buyer_item_statement(
    item_id: UUID, buyer_id: UUID, *, for_update: bool
) -> Select[tuple[OrderItem]]:
    """Monta o SELECT do item no escopo do Buyer."""
    stmt = (
        select(OrderItem)
        .join(Order, OrderItem.order_id == Order.id)
        .where(OrderItem.id == item_id, Order.buyer_id == buyer_id)
    )
    if for_update:
        stmt = stmt.with_for_update()
    return stmt


def load_seller_item(
    session: Session, item_id: UUID, seller_id: UUID, *, for_update: bool = False
) -> OrderItem:
    item = session.scalar(seller_item_statement(item_id, seller_id, for_update=for_update))
    if item is None:
        raise ResourceNotFoundError("Order item not found")
    return item


def load_buyer_item(
    session: Session, item_id: UUID, buyer_id: UUID, *, for_update: bool = False
) -> OrderItem:
    item = session.scalar(buyer_item_statement(item_id, buyer_id, for_update=for_update))
    if item is None:
        raise ResourceNotFoundError("Order item not found")
    return item


def seller_list_statement(seller_id: UUID) -> Select[tuple[OrderItem, Product, Order, User]]:
    """Itens do Seller com produto, pedido e buyer para a listagem."""
    return (
        select(OrderItem, Product, Order, User)
        .join(Offer, OrderItem.offer_id == Offer.id)
        .join(Product, Offer.product_id == Product.id)
        .join(Order, OrderItem.order_id == Order.id)
        .join(User, Order.buyer_id == User.id)
        .where(Offer.seller_id == seller_id)
    )


def load_seller_item_context(
    session: Session, item_id: UUID, seller_id: UUID
) -> tuple[OrderItem, Product, Order, User]:
    row = session.execute(
        select(OrderItem, Product, Order, User)
        .join(Offer, OrderItem.offer_id == Offer.id)
        .join(Product, Offer.product_id == Product.id)
        .join(Order, OrderItem.order_id == Order.id)
        .join(User, Order.buyer_id == User.id)
        .where(OrderItem.id == item_id, Offer.seller_id == seller_id)
    ).one_or_none()
    if row is None:
        raise ResourceNotFoundError("Order item not found")
    return row[0], row[1], row[2], row[3]


def load_buyer_item_context(
    session: Session, item_id: UUID, buyer_id: UUID
) -> tuple[OrderItem, Product, Order]:
    """Item do proprio Buyer, com produto e pedido -- o buyer ja e o CurrentUser."""
    row = session.execute(
        select(OrderItem, Product, Order)
        .join(Offer, OrderItem.offer_id == Offer.id)
        .join(Product, Offer.product_id == Product.id)
        .join(Order, OrderItem.order_id == Order.id)
        .where(OrderItem.id == item_id, Order.buyer_id == buyer_id)
    ).one_or_none()
    if row is None:
        raise ResourceNotFoundError("Order item not found")
    return row[0], row[1], row[2]
