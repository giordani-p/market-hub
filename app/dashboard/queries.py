"""Queries de leitura do Dashboard, agregadas no banco."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session

from app.catalog.models import Offer, Product
from app.catalog.schemas import format_price
from app.communication.models import Conversation
from app.dashboard.projection import (
    ACTIVE_ITEM_STATUSES,
    RECENT_LIMIT,
    active_order_item_count,
    buyer_order_projection_status,
    fill_priority_counts,
    fill_status_counts,
    format_order_total,
    total_order_item_count,
)
from app.dashboard.schemas import (
    BuyerDashboard,
    BuyerDashboardSummary,
    BuyerRecent,
    BuyerRecentOrder,
    BuyerRecentOrderItem,
    ConversationsByPriority,
    OpenConversationsAttention,
    OpsAttention,
    OpsDashboard,
    OpsDashboardSummary,
    OpsQueuePreviewItem,
    OpsRecent,
    OrderItemsByStatus,
    SellerDashboard,
    SellerDashboardSummary,
    SellerRecent,
    SellerRecentOrderItem,
)
from app.orders.access import seller_list_statement
from app.orders.models import Order, OrderItem
from app.orders.numbers import item_number
from app.orders.schemas import BuyerSummary, ProductSummary
from app.support.priority_ops import EffectivePriority, preview_open_queue
from app.support.schemas import OpsConversationQueueItem


def _price(value: object) -> str:
    return format_price(value) if isinstance(value, Decimal) else str(value)


def seller_dashboard(session: Session, seller_id: UUID) -> SellerDashboard:
    """Projecao do Seller: items proprios, conversations open e 5 recentes."""
    status_rows = session.execute(
        select(OrderItem.status, func.count())
        .join(Offer, OrderItem.offer_id == Offer.id)
        .where(Offer.seller_id == seller_id)
        .group_by(OrderItem.status)
    ).all()
    counts = fill_status_counts(status_rows)
    open_conversations = session.scalar(
        select(func.count())
        .select_from(Conversation)
        .join(OrderItem, Conversation.order_item_id == OrderItem.id)
        .join(Offer, OrderItem.offer_id == Offer.id)
        .where(Offer.seller_id == seller_id, Conversation.status == "open")
    )
    recent_rows = session.execute(
        seller_list_statement(seller_id).order_by(OrderItem.created_at.desc()).limit(RECENT_LIMIT)
    ).all()
    return SellerDashboard(
        role="seller",
        summary=SellerDashboardSummary(
            total_order_items=total_order_item_count(counts),
            active_order_items=active_order_item_count(counts),
            order_items_by_status=OrderItemsByStatus(**counts),
        ),
        attention=OpenConversationsAttention(open_conversations=open_conversations or 0),
        recent=SellerRecent(
            order_items=[
                SellerRecentOrderItem(
                    order_item_id=item.id,
                    number=item_number(order.number, item.line),
                    order_id=order.id,
                    product=ProductSummary(id=product.id, name=product.name),
                    buyer=BuyerSummary(id=buyer.id, name=buyer.name),
                    quantity=item.quantity,
                    purchase_price=_price(item.purchase_price),
                    status=item.status,
                    created_at=item.created_at,
                )
                for item, product, order, buyer in recent_rows
            ]
        ),
    )


def buyer_dashboard(session: Session, buyer_id: UUID) -> BuyerDashboard:
    """Projecao do Buyer: Orders ativas/concluidas, conversations open e 5 recentes."""
    has_active_item = exists(
        select(OrderItem.id).where(
            OrderItem.order_id == Order.id,
            OrderItem.status.in_(ACTIVE_ITEM_STATUSES),
        )
    )
    has_non_delivered = exists(
        select(OrderItem.id).where(
            OrderItem.order_id == Order.id,
            OrderItem.status != "delivered",
        )
    )
    has_item = exists(select(OrderItem.id).where(OrderItem.order_id == Order.id))
    active_orders = session.scalar(
        select(func.count()).select_from(Order).where(Order.buyer_id == buyer_id, has_active_item)
    )
    completed_orders = session.scalar(
        select(func.count())
        .select_from(Order)
        .where(Order.buyer_id == buyer_id, ~has_non_delivered, has_item)
    )
    open_conversations = session.scalar(
        select(func.count())
        .select_from(Conversation)
        .join(OrderItem, Conversation.order_item_id == OrderItem.id)
        .join(Order, OrderItem.order_id == Order.id)
        .where(Order.buyer_id == buyer_id, Conversation.status == "open")
    )
    orders = list(
        session.scalars(
            select(Order)
            .where(Order.buyer_id == buyer_id)
            .order_by(Order.created_at.desc())
            .limit(RECENT_LIMIT)
        ).all()
    )
    return BuyerDashboard(
        role="buyer",
        summary=BuyerDashboardSummary(
            active_orders=active_orders or 0,
            completed_orders=completed_orders or 0,
        ),
        attention=OpenConversationsAttention(open_conversations=open_conversations or 0),
        recent=BuyerRecent(orders=_buyer_recent_orders(session, orders)),
    )


def _buyer_recent_orders(session: Session, orders: list[Order]) -> list[BuyerRecentOrder]:
    if not orders:
        return []
    order_ids = [order.id for order in orders]
    rows = session.execute(
        select(OrderItem, Product)
        .join(Offer, OrderItem.offer_id == Offer.id)
        .join(Product, Offer.product_id == Product.id)
        .where(OrderItem.order_id.in_(order_ids))
        .order_by(OrderItem.created_at)
    ).all()
    grouped: dict[UUID, list[tuple[OrderItem, Product]]] = {}
    for item, product in rows:
        grouped.setdefault(item.order_id, []).append((item, product))
    recent: list[BuyerRecentOrder] = []
    for order in orders:
        pairs = grouped.get(order.id, [])
        recent.append(
            BuyerRecentOrder(
                order_id=order.id,
                number=order.number,
                created_at=order.created_at,
                status=buyer_order_projection_status([item.status for item, _ in pairs]),
                total_amount=format_order_total(
                    [(item.purchase_price, item.quantity) for item, _ in pairs]
                ),
                items=[
                    BuyerRecentOrderItem(
                        order_item_id=item.id,
                        number=item_number(order.number, item.line),
                        product=ProductSummary(id=product.id, name=product.name),
                        quantity=item.quantity,
                        status=item.status,
                    )
                    for item, product in pairs
                ],
            )
        )
    return recent


def ops_dashboard(session: Session) -> OpsDashboard:
    """Projecao da Ops: conversations open por prioridade efetiva e preview da fila."""
    effective = EffectivePriority.label("effective_priority")
    priority_rows = session.execute(
        select(effective, func.count())
        .select_from(Conversation)
        .where(Conversation.status == "open")
        .group_by(effective)
    ).all()
    counts = fill_priority_counts(priority_rows)
    return OpsDashboard(
        role="ops",
        summary=OpsDashboardSummary(
            open_conversations=sum(counts.values()),
            conversations_by_priority=ConversationsByPriority(**counts),
        ),
        attention=OpsAttention(
            priority_queue_preview=[
                _preview_item(item) for item in preview_open_queue(session, limit=RECENT_LIMIT)
            ]
        ),
        recent=OpsRecent(),
    )


def _preview_item(item: OpsConversationQueueItem) -> OpsQueuePreviewItem:
    return OpsQueuePreviewItem(
        conversation_id=item.id,
        order_item_id=item.order_item_id,
        number=item.number,
        effective_priority=item.effective_priority,
        calculated_priority=item.calculated_priority,
        ops_override=item.ops_override,
        reason=item.reason,
        last_interaction_at=item.last_interaction_at,
        seller=item.seller,
        buyer=item.buyer,
        product=item.product,
        order_item_status=item.order_item_status,
        purchase_price=item.purchase_price,
    )
