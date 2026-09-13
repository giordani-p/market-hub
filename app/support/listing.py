"""Listagem e detalhe operacional de Order Items para Ops."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.catalog.models import Offer, Product, Seller
from app.catalog.schemas import format_price
from app.orders.models import Order, OrderItem
from app.orders.schemas import BuyerSummary, OrderSummary, ProductDetailSummary, ProductSummary
from app.support.access import load_ops_item_context, ops_list_statement
from app.support.schemas import (
    OpsOrderItemDetail,
    OpsOrderItemListItem,
    OpsOrderItemListResponse,
    SellerSummary,
)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def _price(value: object) -> str:
    if isinstance(value, Decimal):
        return format_price(value)
    return str(value)


def _list_item(
    item: OrderItem, product: Product, order: Order, buyer: User, seller: Seller
) -> OpsOrderItemListItem:
    return OpsOrderItemListItem(
        order_item_id=item.id,
        product=ProductSummary(id=product.id, name=product.name),
        quantity=item.quantity,
        purchase_price=_price(item.purchase_price),
        status=item.status,
        created_at=item.created_at,
        buyer=BuyerSummary(id=buyer.id, name=buyer.name),
        seller=SellerSummary(id=seller.id, name=seller.name),
        order_id=order.id,
    )


def _detail(
    item: OrderItem, product: Product, order: Order, buyer: User, seller: Seller
) -> OpsOrderItemDetail:
    return OpsOrderItemDetail(
        id=item.id,
        offer_id=item.offer_id,
        quantity=item.quantity,
        purchase_price=_price(item.purchase_price),
        status=item.status,
        created_at=item.created_at,
        updated_at=item.updated_at,
        product=ProductDetailSummary(
            id=product.id,
            name=product.name,
            description=product.description,
        ),
        buyer=BuyerSummary(id=buyer.id, name=buyer.name),
        seller=SellerSummary(id=seller.id, name=seller.name),
        order=OrderSummary(id=order.id, created_at=order.created_at),
    )


def list_ops_order_items(
    session: Session,
    *,
    page: int,
    page_size: int,
    status_filter: str | None,
    from_: datetime | None,
    to: datetime | None,
    order_item_id: UUID | None,
    seller_id: UUID | None,
) -> OpsOrderItemListResponse:
    stmt = ops_list_statement()
    if status_filter is not None:
        stmt = stmt.where(OrderItem.status == status_filter)
    if from_ is not None:
        stmt = stmt.where(OrderItem.created_at >= _as_utc(from_))
    if to is not None:
        stmt = stmt.where(OrderItem.created_at <= _as_utc(to))
    if order_item_id is not None:
        stmt = stmt.where(OrderItem.id == order_item_id)
    if seller_id is not None:
        stmt = stmt.where(Offer.seller_id == seller_id)

    total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = session.execute(
        stmt.order_by(OrderItem.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return OpsOrderItemListResponse(
        items=[
            _list_item(item, product, order, buyer, seller)
            for item, product, order, buyer, seller in rows
        ],
        page=page,
        page_size=page_size,
        total=total,
    )


def get_ops_order_item(session: Session, item_id: UUID) -> OpsOrderItemDetail:
    item, product, order, buyer, seller = load_ops_item_context(session, item_id)
    return _detail(item, product, order, buyer, seller)
