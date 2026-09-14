"""Funcoes puras de projecao do Dashboard."""

from collections.abc import Iterable
from decimal import Decimal

from app.catalog.schemas import format_price

RECENT_LIMIT = 5
ITEM_STATUSES = ("placed", "preparing", "in_transit", "delivered", "cancelled")
ACTIVE_ITEM_STATUSES = ("placed", "preparing", "in_transit")
EFFECTIVE_PRIORITIES = ("critical", "high", "medium", "low")


def fill_status_counts(rows: Iterable[tuple[str, int]]) -> dict[str, int]:
    """Preenche as cinco chaves de status, inclusive as ausentes com 0."""
    counts = {status: 0 for status in ITEM_STATUSES}
    for status, count in rows:
        if status in counts:
            counts[status] = int(count)
    return counts


def fill_priority_counts(rows: Iterable[tuple[str, int]]) -> dict[str, int]:
    """Preenche as quatro chaves de prioridade efetiva, inclusive as ausentes com 0."""
    counts = {priority: 0 for priority in EFFECTIVE_PRIORITIES}
    for priority, count in rows:
        if priority in counts:
            counts[priority] = int(count)
    return counts


def active_order_item_count(counts: dict[str, int]) -> int:
    return sum(counts[status] for status in ACTIVE_ITEM_STATUSES)


def total_order_item_count(counts: dict[str, int]) -> int:
    return sum(counts.values())


def buyer_order_projection_status(statuses: list[str]) -> str:
    """Deriva o status de apresentacao de um Order a partir dos items."""
    if any(status in ACTIVE_ITEM_STATUSES for status in statuses):
        return "in_progress"
    if statuses and all(status == "delivered" for status in statuses):
        return "completed"
    return "cancelled"


def format_order_total(items: Iterable[tuple[Decimal, int]]) -> str:
    """Soma purchase_price * quantity e serializa como Price."""
    total = sum((price * quantity for price, quantity in items), Decimal("0.00"))
    return format_price(total)
