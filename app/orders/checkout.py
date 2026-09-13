"""Finalizacao atomica da compra."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.catalog.models import Offer
from app.catalog.schemas import format_price
from app.core.errors import CheckoutRejectedError, CheckoutRejectedItem
from app.core.events import OrderCreated, record_event
from app.orders.models import Order, OrderItem
from app.orders.schemas import CheckoutItem, CheckoutRequest


def _rejection(
    item: CheckoutItem,
    reason: str,
    offer: Offer | None = None,
) -> CheckoutRejectedItem:
    current_price = format_price(offer.price) if offer is not None else None
    return CheckoutRejectedItem(
        offer_id=str(item.offer_id),
        reason=reason,
        expected_price=item.expected_price,
        current_price=current_price,
        available=None if offer is None else offer.available,
        stock=None if offer is None else offer.stock,
    )


def _validate_item(
    session: Session, item: CheckoutItem
) -> tuple[Offer | None, CheckoutRejectedItem | None]:
    offer = session.get(Offer, item.offer_id)
    if offer is None:
        return None, _rejection(item, "not_found")
    if not offer.available:
        return offer, _rejection(item, "unavailable", offer)
    if offer.stock < item.quantity:
        return offer, _rejection(item, "insufficient_stock", offer)
    if offer.price != Decimal(item.expected_price):
        return offer, _rejection(item, "price_changed", offer)
    return offer, None


def _consume_stock(session: Session, offer_id: UUID, quantity: int) -> bool:
    result = session.execute(
        update(Offer)
        .where(Offer.id == offer_id, Offer.stock >= quantity, Offer.available.is_(True))
        .values(stock=Offer.stock - quantity)
    )
    return result.rowcount == 1


def checkout(session: Session, buyer_id: UUID, payload: CheckoutRequest) -> Order:
    problems: list[CheckoutRejectedItem] = []
    valid_items: list[tuple[CheckoutItem, Offer]] = []

    for item in payload.items:
        offer, problem = _validate_item(session, item)
        if problem is not None:
            problems.append(problem)
        elif offer is not None:
            valid_items.append((item, offer))

    if problems:
        raise CheckoutRejectedError(problems)

    order = Order(buyer_id=buyer_id)
    session.add(order)
    session.flush()

    for item, offer in valid_items:
        if not _consume_stock(session, offer.id, item.quantity):
            session.refresh(offer)
            raise CheckoutRejectedError([_rejection(item, "insufficient_stock", offer)])
        session.add(
            OrderItem(
                order_id=order.id,
                offer_id=offer.id,
                quantity=item.quantity,
                purchase_price=offer.price,
                status="placed",
            )
        )

    session.flush()
    session.refresh(order, attribute_names=["items"])
    record_event(session, OrderCreated(order_id=order.id, buyer_id=buyer_id))
    return order
