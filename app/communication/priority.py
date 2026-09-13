"""PriorityPolicy deterministica da Conversation."""

from datetime import datetime, timedelta
from decimal import Decimal

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


def age_weight(age: timedelta) -> Decimal:
    hours = age.total_seconds() / 3600
    if hours < 4:
        return Decimal("0.00")
    if hours < 12:
        return Decimal("0.25")
    if hours < 24:
        return Decimal("0.50")
    if hours < 48:
        return Decimal("0.75")
    return Decimal("1.00")


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
