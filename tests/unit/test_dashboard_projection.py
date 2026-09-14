from decimal import Decimal

from app.dashboard.projection import (
    active_order_item_count,
    buyer_order_projection_status,
    fill_priority_counts,
    fill_status_counts,
    format_order_total,
    total_order_item_count,
)


def test_fill_status_counts_empty_is_all_zeros() -> None:
    counts = fill_status_counts([])
    assert counts == {
        "placed": 0,
        "preparing": 0,
        "in_transit": 0,
        "delivered": 0,
        "cancelled": 0,
    }
    assert total_order_item_count(counts) == 0
    assert active_order_item_count(counts) == 0


def test_fill_status_counts_fills_missing_keys() -> None:
    counts = fill_status_counts([("placed", 2), ("delivered", 4)])
    assert counts["placed"] == 2
    assert counts["delivered"] == 4
    assert counts["preparing"] == 0
    assert counts["in_transit"] == 0
    assert counts["cancelled"] == 0
    assert total_order_item_count(counts) == 6
    assert active_order_item_count(counts) == 2


def test_fill_status_counts_ignores_unknown_status() -> None:
    counts = fill_status_counts([("mystery", 9), ("placed", 1)])
    assert counts["placed"] == 1
    assert "mystery" not in counts


def test_fill_priority_counts_empty_is_all_zeros() -> None:
    counts = fill_priority_counts([])
    assert counts == {"critical": 0, "high": 0, "medium": 0, "low": 0}


def test_fill_priority_counts_fills_missing_keys() -> None:
    counts = fill_priority_counts([("high", 3), ("critical", 1)])
    assert counts == {"critical": 1, "high": 3, "medium": 0, "low": 0}


def test_buyer_order_projection_status_variants() -> None:
    assert buyer_order_projection_status(["placed"]) == "in_progress"
    assert buyer_order_projection_status(["delivered", "delivered"]) == "completed"
    assert buyer_order_projection_status(["cancelled"]) == "cancelled"
    assert buyer_order_projection_status(["delivered", "cancelled"]) == "cancelled"
    assert buyer_order_projection_status(["delivered", "in_transit"]) == "in_progress"
    assert buyer_order_projection_status([]) == "cancelled"


def test_format_order_total_two_decimals() -> None:
    assert format_order_total([]) == "0.00"
    assert format_order_total([(Decimal("10.50"), 2), (Decimal("1.00"), 1)]) == "22.00"
