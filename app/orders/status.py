"""Regras de transicao de status do Order Item."""

from app.auth.models import UserRole
from app.core.errors import InvalidTransitionError

FORWARD = {
    "placed": "preparing",
    "preparing": "in_transit",
    "in_transit": "delivered",
}

BUYER_CANCEL_STATUSES = frozenset({"placed", "preparing"})
SELLER_CANCEL_STATUSES = frozenset({"placed", "preparing", "in_transit"})
STOCK_RESTORE_STATUSES = frozenset({"placed", "preparing"})


def assert_forward_transition(current: str, target: str) -> None:
    if FORWARD.get(current) != target:
        raise InvalidTransitionError("Invalid status transition")


def can_cancel(current: str, role: str) -> bool:
    if role == UserRole.BUYER:
        return current in BUYER_CANCEL_STATUSES
    if role == UserRole.SELLER:
        return current in SELLER_CANCEL_STATUSES
    return False


def restores_stock_on_cancel(current: str) -> bool:
    return current in STOCK_RESTORE_STATUSES
