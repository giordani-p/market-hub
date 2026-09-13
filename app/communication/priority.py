"""PriorityPolicy deterministica da Conversation."""

from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.communication.models import Conversation
from app.core.events import ConversationPriorityChanged, record_event
from app.orders.models import OrderItem

REASON_WEIGHTS: dict[str, Decimal] = {
    "atraso": Decimal("1.00"),
    "reclamacao": Decimal("0.75"),
    "troca": Decimal("0.50"),
    "devolucao": Decimal("0.50"),
    "suporte": Decimal("0.40"),
    "outros": Decimal("0.25"),
    "elogio": Decimal("0.00"),
}

STATUS_WEIGHTS: dict[str, Decimal] = {
    "in_transit": Decimal("1.00"),
    "preparing": Decimal("0.75"),
    "placed": Decimal("0.50"),
    "delivered": Decimal("0.25"),
    "cancelled": Decimal("0.00"),
}

AGE_BUCKET_HOURS: tuple[int, ...] = (4, 12, 24, 48)
AGE_BUCKET_WEIGHTS: tuple[Decimal, ...] = (
    Decimal("0.00"),
    Decimal("0.25"),
    Decimal("0.50"),
    Decimal("0.75"),
    Decimal("1.00"),
)


def age_bucket_rank(age: timedelta) -> int:
    hours = age.total_seconds() / 3600
    for index, boundary in enumerate(AGE_BUCKET_HOURS):
        if hours < boundary:
            return index
    return len(AGE_BUCKET_HOURS)


def age_bucket(age: timedelta) -> str:
    labels = ("<4h", "4-12h", "12-24h", "24-48h", ">48h")
    return labels[age_bucket_rank(age)]


def age_weight(age: timedelta) -> Decimal:
    return AGE_BUCKET_WEIGHTS[age_bucket_rank(age)]


def value_weight(purchase_price: Decimal) -> Decimal:
    if purchase_price < Decimal("100"):
        return Decimal("0.00")
    if purchase_price < Decimal("500"):
        return Decimal("0.25")
    if purchase_price < Decimal("1000"):
        return Decimal("0.50")
    if purchase_price < Decimal("5000"):
        return Decimal("0.75")
    return Decimal("1.00")


def classify(score: Decimal) -> str:
    if score <= Decimal("1.00"):
        return "low"
    if score <= Decimal("2.25"):
        return "medium"
    return "high"


def score(
    *,
    reason: str,
    item_status: str,
    created_at: datetime,
    purchase_price: Decimal,
    now: datetime,
) -> Decimal:
    return (
        REASON_WEIGHTS[reason]
        + STATUS_WEIGHTS[item_status]
        + age_weight(now - created_at)
        + value_weight(purchase_price)
    )


def calculate_priority(
    *,
    reason: str,
    item_status: str,
    created_at: datetime,
    purchase_price: Decimal,
    now: datetime,
) -> str:
    return classify(
        score(
            reason=reason,
            item_status=item_status,
            created_at=created_at,
            purchase_price=purchase_price,
            now=now,
        )
    )


def effective_priority(calculated_priority: str, ops_override: str | None) -> str:
    return ops_override if ops_override else calculated_priority


def is_stale(
    *,
    now: datetime,
    created_at: datetime,
    last_interaction_at: datetime,
    status_updated_at: datetime | None,
    priority_calculated_at: datetime | None,
) -> bool:
    if priority_calculated_at is None:
        return True
    if last_interaction_at > priority_calculated_at:
        return True
    if status_updated_at is not None and status_updated_at > priority_calculated_at:
        return True
    return age_bucket(now - created_at) != age_bucket(priority_calculated_at - created_at)


def apply_calculated_priority(
    conversation: Conversation,
    item: OrderItem,
    *,
    now: datetime,
    session: Session | None = None,
) -> bool:
    """Recalcula a prioridade persistida. Nao mexe em ops_override.

    Emite ConversationPriorityChanged somente quando effective_priority muda
    e uma session e fornecida.
    """
    before = effective_priority(conversation.calculated_priority, conversation.ops_override)
    calculated = calculate_priority(
        reason=conversation.reason,
        item_status=item.status,
        created_at=conversation.created_at,
        purchase_price=item.purchase_price,
        now=now,
    )
    changed = calculated != conversation.calculated_priority
    if changed:
        conversation.calculated_priority = calculated
        conversation.updated_at = now
    conversation.priority_calculated_at = now
    after = effective_priority(conversation.calculated_priority, conversation.ops_override)
    if session is not None and after != before:
        record_event(
            session,
            ConversationPriorityChanged(
                conversation_id=conversation.id,
                from_priority=before,
                to_priority=after,
                changed_at=now,
            ),
        )
    return changed
