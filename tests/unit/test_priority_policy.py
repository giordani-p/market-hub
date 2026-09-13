from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.communication.priority import (
    REASON_WEIGHTS,
    STATUS_WEIGHTS,
    age_weight,
    calculate_priority,
    classify,
    effective_priority,
    score,
    value_weight,
)

NOW = datetime(2026, 9, 13, 12, 0, tzinfo=UTC)


def _created(*, hours: float) -> datetime:
    return NOW - timedelta(hours=hours)


def test_reason_weights() -> None:
    expected = {
        "atraso": "1.00",
        "reclamacao": "0.75",
        "troca": "0.50",
        "devolucao": "0.50",
        "suporte": "0.40",
        "outros": "0.25",
        "elogio": "0.00",
    }
    assert {key: str(value) for key, value in REASON_WEIGHTS.items()} == expected


def test_status_weights() -> None:
    expected = {
        "in_transit": "1.00",
        "preparing": "0.75",
        "placed": "0.50",
        "delivered": "0.25",
        "cancelled": "0.00",
    }
    assert {key: str(value) for key, value in STATUS_WEIGHTS.items()} == expected


@pytest.mark.parametrize(
    ("hours", "expected"),
    [
        (0, "0.00"),
        (3.99, "0.00"),
        (4, "0.25"),
        (11.99, "0.25"),
        (12, "0.50"),
        (23.99, "0.50"),
        (24, "0.75"),
        (47.99, "0.75"),
        (48, "1.00"),
        (100, "1.00"),
    ],
)
def test_age_boundaries(hours: float, expected: str) -> None:
    assert str(age_weight(timedelta(hours=hours))) == expected


@pytest.mark.parametrize(
    ("price", "expected"),
    [
        ("0.00", "0.00"),
        ("99.99", "0.00"),
        ("100.00", "0.25"),
        ("499.99", "0.25"),
        ("500.00", "0.50"),
        ("999.99", "0.50"),
        ("1000.00", "0.75"),
        ("4999.99", "0.75"),
        ("5000.00", "1.00"),
    ],
)
def test_value_boundaries(price: str, expected: str) -> None:
    assert str(value_weight(Decimal(price))) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("0.00", "low"),
        ("1.00", "low"),
        ("1.01", "medium"),
        ("2.25", "medium"),
        ("2.26", "high"),
        ("4.00", "high"),
    ],
)
def test_classify_boundaries(raw: str, expected: str) -> None:
    assert classify(Decimal(raw)) == expected


def test_low_medium_high_and_max_never_critical() -> None:
    low = calculate_priority(
        reason="elogio",
        item_status="cancelled",
        created_at=_created(hours=0),
        purchase_price=Decimal("10.00"),
        now=NOW,
    )
    medium = calculate_priority(
        reason="reclamacao",
        item_status="placed",
        created_at=_created(hours=5),
        purchase_price=Decimal("100.00"),
        now=NOW,
    )
    high = calculate_priority(
        reason="atraso",
        item_status="in_transit",
        created_at=_created(hours=13),
        purchase_price=Decimal("500.00"),
        now=NOW,
    )
    maximum = score(
        reason="atraso",
        item_status="in_transit",
        created_at=_created(hours=48),
        purchase_price=Decimal("5000.00"),
        now=NOW,
    )
    assert low == "low"
    assert medium == "medium"
    assert high == "high"
    assert maximum == Decimal("4.00")
    assert classify(maximum) == "high"
    assert effective_priority("high", None) == "high"
    assert effective_priority("low", "critical") == "critical"
