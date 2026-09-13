"""Rotas de Order e Order Item."""

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload

from app.auth.dependencies import BuyerUser, SellerUser, get_current_user
from app.auth.models import User, UserRole
from app.catalog.models import Offer
from app.core.errors import ForbiddenError, InvalidTransitionError, ResourceNotFoundError
from app.core.events import OrderItemCancelled, OrderItemStatusChanged, record_event
from app.database import get_session
from app.orders.checkout import checkout
from app.orders.models import Order, OrderItem
from app.orders.schemas import (
    CheckoutRequest,
    OrderItemResponse,
    OrderItemStatusUpdate,
    OrderResponse,
)
from app.orders.status import assert_forward_transition, can_cancel, restores_stock_on_cancel

SessionDep = Annotated[Session, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]

orders_router = APIRouter(tags=["orders"])
items_router = APIRouter(tags=["order-items"])


def _touch(item: OrderItem) -> None:
    item.updated_at = datetime.now(UTC)


def _get_order_for_buyer(session: Session, order_id: UUID, buyer: User) -> Order:
    order = session.scalar(
        select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
    )
    if order is None or order.buyer_id != buyer.id:
        raise ResourceNotFoundError("Order not found")
    return order


def _load_item(session: Session, item_id: UUID) -> OrderItem | None:
    return session.scalar(select(OrderItem).where(OrderItem.id == item_id))


def _offer_seller_id(session: Session, offer_id: UUID) -> UUID | None:
    offer = session.get(Offer, offer_id)
    return None if offer is None else offer.seller_id


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
    response_model=list[OrderItemResponse],
    summary="List order items of the authenticated seller",
)
def list_order_items(seller: SellerUser, session: SessionDep) -> list[OrderItem]:
    stmt = (
        select(OrderItem)
        .join(Offer, OrderItem.offer_id == Offer.id)
        .where(Offer.seller_id == seller.seller_id)
        .order_by(OrderItem.created_at)
    )
    return list(session.scalars(stmt).all())


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
    item = _load_item(session, item_id)
    if item is None:
        raise ResourceNotFoundError("Order item not found")
    if _offer_seller_id(session, item.offer_id) != seller.seller_id:
        raise ForbiddenError("Order item does not belong to the authenticated seller")

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
    item = _load_item(session, item_id)
    if item is None:
        raise ResourceNotFoundError("Order item not found")

    if user.role == UserRole.BUYER:
        order = session.get(Order, item.order_id)
        if order is None or order.buyer_id != user.id:
            raise ResourceNotFoundError("Order item not found")
    elif user.role == UserRole.SELLER:
        if _offer_seller_id(session, item.offer_id) != user.seller_id:
            raise ForbiddenError("Order item does not belong to the authenticated seller")
    else:
        raise ForbiddenError("Cannot cancel order item")

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
