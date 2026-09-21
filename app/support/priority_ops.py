"""Prioridade e fila de Conversations para Ops."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Select, case, func, literal, select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.catalog.models import Offer, Product, Seller
from app.catalog.schemas import SellerSummary, format_price
from app.communication.lifecycle import utcnow
from app.communication.models import Conversation
from app.communication.priority import apply_calculated_priority, effective_priority
from app.core.errors import InvalidTransitionError
from app.core.events import ConversationPriorityChanged, record_event
from app.orders.models import Order, OrderItem
from app.orders.numbers import apply_public_number_filter, item_number
from app.orders.schemas import BuyerSummary, ProductSummary
from app.support.access import load_ops_item
from app.support.comments import create_comment
from app.support.schemas import (
    OpsConversation,
    OpsConversationQueueItem,
    OpsConversationQueueResponse,
)

EffectivePriority = case(
    (Conversation.ops_override == "critical", literal("critical")),
    else_=Conversation.calculated_priority,
)

PriorityRank = case(
    (EffectivePriority == "critical", 0),
    (EffectivePriority == "high", 1),
    (EffectivePriority == "medium", 2),
    else_=3,
)


def _price(value: object) -> str:
    return format_price(value) if isinstance(value, Decimal) else str(value)


def to_ops_conversation(conversation: Conversation) -> OpsConversation:
    return OpsConversation(
        id=conversation.id,
        order_item_id=conversation.order_item_id,
        reason=conversation.reason,
        status=conversation.status,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        last_interaction_at=conversation.last_interaction_at,
        calculated_priority=conversation.calculated_priority,
        ops_override=conversation.ops_override,
        effective_priority=effective_priority(
            conversation.calculated_priority, conversation.ops_override
        ),
    )


def refresh_calculated_priority(
    session: Session, conversation: Conversation, *, now: datetime | None = None
) -> Conversation:
    item = load_ops_item(session, conversation.order_item_id)
    apply_calculated_priority(conversation, item, now=now or utcnow(), session=session)
    session.flush()
    return conversation


def apply_critical(
    session: Session, conversation: Conversation, user: User, justification: str
) -> Conversation:
    if conversation.ops_override == "critical":
        raise InvalidTransitionError("Conversation is already critical")
    before = effective_priority(conversation.calculated_priority, conversation.ops_override)
    create_comment(session, conversation.order_item_id, user, justification)
    conversation.ops_override = "critical"
    now = utcnow()
    conversation.updated_at = now
    after = effective_priority(conversation.calculated_priority, conversation.ops_override)
    if after != before:
        record_event(
            session,
            ConversationPriorityChanged(
                conversation_id=conversation.id,
                from_priority=before,
                to_priority=after,
                changed_at=now,
            ),
        )
    session.flush()
    return conversation


def remove_critical(session: Session, conversation: Conversation) -> Conversation:
    if conversation.ops_override is None:
        raise InvalidTransitionError("Conversation has no critical override")
    before = effective_priority(conversation.calculated_priority, conversation.ops_override)
    conversation.ops_override = None
    now = utcnow()
    conversation.updated_at = now
    after = effective_priority(conversation.calculated_priority, conversation.ops_override)
    if after != before:
        record_event(
            session,
            ConversationPriorityChanged(
                conversation_id=conversation.id,
                from_priority=before,
                to_priority=after,
                changed_at=now,
            ),
        )
    session.flush()
    return conversation


def list_item_conversations(session: Session, item_id: UUID) -> list[Conversation]:
    load_ops_item(session, item_id)
    return list(
        session.scalars(
            select(Conversation)
            .where(Conversation.order_item_id == item_id)
            .order_by(Conversation.last_interaction_at.desc())
        )
    )


def _queue_statement() -> Select[tuple[Conversation, OrderItem, Product, Order, User, Seller]]:
    return (
        select(Conversation, OrderItem, Product, Order, User, Seller)
        .join(OrderItem, Conversation.order_item_id == OrderItem.id)
        .join(Offer, OrderItem.offer_id == Offer.id)
        .join(Product, Offer.product_id == Product.id)
        .join(Order, OrderItem.order_id == Order.id)
        .join(User, Order.buyer_id == User.id)
        .join(Seller, Offer.seller_id == Seller.id)
        .where(Conversation.status == "open")
    )


def list_open_queue(
    session: Session,
    *,
    page: int,
    page_size: int,
    seller_id: UUID | None,
    order_item_id: UUID | None,
    public_number: str | None,
    effective: str | None,
) -> OpsConversationQueueResponse:
    stmt = _queue_statement()
    if seller_id is not None:
        stmt = stmt.where(Offer.seller_id == seller_id)
    if order_item_id is not None:
        stmt = stmt.where(Conversation.order_item_id == order_item_id)
    stmt = apply_public_number_filter(stmt, public_number)
    if effective is not None:
        stmt = stmt.where(EffectivePriority == effective)

    total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = session.execute(
        stmt.order_by(PriorityRank, Conversation.last_interaction_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return OpsConversationQueueResponse(
        items=[
            _queue_item(conversation, item, product, order, buyer, seller)
            for conversation, item, product, order, buyer, seller in rows
        ],
        page=page,
        page_size=page_size,
        total=total,
    )


def preview_open_queue(session: Session, *, limit: int = 5) -> list[OpsConversationQueueItem]:
    """Primeiros itens da fila OPEN, na mesma ordem da listagem Ops."""
    rows = session.execute(
        _queue_statement()
        .order_by(PriorityRank, Conversation.last_interaction_at.desc())
        .limit(limit)
    ).all()
    return [
        _queue_item(conversation, item, product, order, buyer, seller)
        for conversation, item, product, order, buyer, seller in rows
    ]


def _queue_item(
    conversation: Conversation,
    item: OrderItem,
    product: Product,
    order: Order,
    buyer: User,
    seller: Seller,
) -> OpsConversationQueueItem:
    base = to_ops_conversation(conversation)
    return OpsConversationQueueItem(
        **base.model_dump(),
        number=item_number(order.number, item.line),
        seller=SellerSummary(id=seller.id, name=seller.name),
        product=ProductSummary(id=product.id, name=product.name),
        buyer=BuyerSummary(id=buyer.id, name=buyer.name),
        order_item_status=item.status,
        purchase_price=_price(item.purchase_price),
    )
