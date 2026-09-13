"""Rotas de Order e Order Item."""

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, selectinload

from app.auth.dependencies import BuyerUser, SellerUser, get_current_user
from app.auth.models import User, UserRole
from app.catalog.models import Offer, Product
from app.catalog.schemas import format_price
from app.core.errors import ForbiddenError, InvalidTransitionError, ResourceNotFoundError
from app.core.events import OrderItemCancelled, OrderItemStatusChanged, record_event
from app.database import get_session
from app.orders.access import (
    load_buyer_item,
    load_seller_item,
    load_seller_item_context,
    seller_list_statement,
)
from app.orders.checkout import checkout
from app.orders.models import Order, OrderItem
from app.orders.schemas import (
    BuyerSummary,
    CheckoutRequest,
    OrderItemDetail,
    OrderItemListItem,
    OrderItemListResponse,
    OrderItemResponse,
    OrderItemStatus,
    OrderItemStatusUpdate,
    OrderResponse,
    OrderSummary,
    ProductDetailSummary,
    ProductSummary,
)
from app.orders.status import assert_forward_transition, can_cancel, restores_stock_on_cancel

SessionDep = Annotated[Session, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]

orders_router = APIRouter(tags=["orders"])
items_router = APIRouter(tags=["order-items"])


def _touch(item: OrderItem) -> None:
    item.updated_at = datetime.now(UTC)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def _get_order_for_buyer(session: Session, order_id: UUID, buyer: User) -> Order:
    order = session.scalar(
        select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
    )
    if order is None or order.buyer_id != buyer.id:
        raise ResourceNotFoundError("Order not found")
    return order


def _price(value: object) -> str:
    from decimal import Decimal

    if isinstance(value, Decimal):
        return format_price(value)
    return str(value)


def _list_item(item: OrderItem, product: Product, order: Order, buyer: User) -> OrderItemListItem:
    return OrderItemListItem(
        order_item_id=item.id,
        product=ProductSummary(id=product.id, name=product.name),
        quantity=item.quantity,
        purchase_price=_price(item.purchase_price),
        status=item.status,
        created_at=item.created_at,
        buyer=BuyerSummary(id=buyer.id, name=buyer.name),
        order_id=order.id,
    )


def _detail(item: OrderItem, product: Product, order: Order, buyer: User) -> OrderItemDetail:
    return OrderItemDetail(
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
        order=OrderSummary(id=order.id, created_at=order.created_at),
    )


@orders_router.get(
    "/orders",
    response_model=list[OrderResponse],
    summary="List orders of the authenticated buyer",
)
def list_orders(buyer: BuyerUser, session: SessionDep) -> list[Order]:
    stmt = (
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.buyer_id == buyer.id)
        .order_by(Order.created_at)
    )
    return list(session.scalars(stmt).all())


@orders_router.post(
    "/orders",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Checkout",
)
def create_order(payload: CheckoutRequest, buyer: BuyerUser, session: SessionDep) -> Order:
    return checkout(session, buyer.id, payload)


@orders_router.get(
    "/orders/{order_id}",
    response_model=OrderResponse,
    summary="Get an order of the authenticated buyer",
)
def get_order(order_id: UUID, buyer: BuyerUser, session: SessionDep) -> Order:
    return _get_order_for_buyer(session, order_id, buyer)


@items_router.get(
    "/order-items",
    response_model=OrderItemListResponse,
    summary="List order items of the authenticated seller",
)
def list_order_items(
    seller: SellerUser,
    session: SessionDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    status_filter: Annotated[OrderItemStatus | None, Query(alias="status")] = None,
    from_: Annotated[datetime | None, Query(alias="from")] = None,
    to: datetime | None = None,
    order_item_id: UUID | None = None,
) -> OrderItemListResponse:
    assert seller.seller_id is not None
    stmt = seller_list_statement(seller.seller_id)
    if status_filter is not None:
        stmt = stmt.where(OrderItem.status == status_filter)
    if from_ is not None:
        stmt = stmt.where(OrderItem.created_at >= _as_utc(from_))
    if to is not None:
        stmt = stmt.where(OrderItem.created_at <= _as_utc(to))
    if order_item_id is not None:
        stmt = stmt.where(OrderItem.id == order_item_id)

    total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = session.execute(
        stmt.order_by(OrderItem.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return OrderItemListResponse(
        items=[_list_item(item, product, order, buyer) for item, product, order, buyer in rows],
        page=page,
        page_size=page_size,
        total=total,
    )


@items_router.get(
    "/order-items/{item_id}",
    response_model=OrderItemDetail,
    summary="Get an order item of the authenticated seller",
)
def get_order_item(item_id: UUID, seller: SellerUser, session: SessionDep) -> OrderItemDetail:
    assert seller.seller_id is not None
    item, product, order, buyer = load_seller_item_context(session, item_id, seller.seller_id)
    return _detail(item, product, order, buyer)


@items_router.patch(
    "/order-items/{item_id}",
    response_model=OrderItemResponse,
    summary="Advance the status of an order item",
)
def update_order_item_status(
    item_id: UUID,
    payload: OrderItemStatusUpdate,
    seller: SellerUser,
    session: SessionDep,
) -> OrderItem:
    assert seller.seller_id is not None
    item = load_seller_item(session, item_id, seller.seller_id, for_update=True)
    if payload.status == item.status:
        return item

    assert_forward_transition(item.status, payload.status)
    previous = item.status
    item.status = payload.status
    _touch(item)
    session.flush()
    record_event(
        session,
        OrderItemStatusChanged(order_item_id=item.id, from_status=previous, to_status=item.status),
    )
    return item


@items_router.post(
    "/order-items/{item_id}/cancel",
    response_model=OrderItemResponse,
    summary="Cancel an order item",
)
def cancel_order_item(item_id: UUID, user: CurrentUser, session: SessionDep) -> OrderItem:
    if user.role == UserRole.BUYER:
        item = load_buyer_item(session, item_id, user.id, for_update=True)
    elif user.role == UserRole.SELLER and user.seller_id is not None:
        item = load_seller_item(session, item_id, user.seller_id, for_update=True)
    else:
        raise ForbiddenError("Cannot cancel order item")

    if item.status == "cancelled":
        return item

    if not can_cancel(item.status, user.role):
        raise InvalidTransitionError("Order item cannot be cancelled")

    restore = restores_stock_on_cancel(item.status)
    previous = item.status
    item.status = "cancelled"
    _touch(item)
    if restore:
        session.execute(
            update(Offer).where(Offer.id == item.offer_id).values(stock=Offer.stock + item.quantity)
        )
    session.flush()
    record_event(session, OrderItemCancelled(order_item_id=item.id, restored_stock=restore))
    record_event(
        session,
        OrderItemStatusChanged(order_item_id=item.id, from_status=previous, to_status="cancelled"),
    )
    return item
