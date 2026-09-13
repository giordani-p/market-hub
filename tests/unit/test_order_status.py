import pytest

from app.auth.models import UserRole
from app.core.errors import InvalidTransitionError
from app.orders.status import assert_forward_transition, can_cancel, restores_stock_on_cancel


def test_forward_transitions() -> None:
    assert_forward_transition("placed", "preparing")
    assert_forward_transition("preparing", "in_transit")
    assert_forward_transition("in_transit", "delivered")


def test_invalid_forward_transition() -> None:
    with pytest.raises(InvalidTransitionError):
        assert_forward_transition("placed", "delivered")


def test_cancel_rules() -> None:
    assert can_cancel("placed", UserRole.BUYER)
    assert can_cancel("preparing", UserRole.BUYER)
    assert not can_cancel("in_transit", UserRole.BUYER)
    assert can_cancel("in_transit", UserRole.SELLER)
    assert not can_cancel("delivered", UserRole.SELLER)
    assert not can_cancel("cancelled", UserRole.BUYER)


def test_stock_restore_on_cancel() -> None:
    assert restores_stock_on_cancel("placed")
    assert restores_stock_on_cancel("preparing")
    assert not restores_stock_on_cancel("in_transit")
