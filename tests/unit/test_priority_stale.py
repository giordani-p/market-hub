from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from app.communication.models import Conversation
from app.communication.priority import (
    apply_calculated_priority,
    is_stale,
)
from app.core.events import publisher
from app.orders.models import OrderItem

NOW = datetime(2026, 9, 13, 12, 0, tzinfo=UTC)


def _stale_kwargs(**overrides: object) -> dict:
    values: dict = {
        "now": NOW,
        "created_at": NOW - timedelta(hours=3),
        "last_interaction_at": NOW - timedelta(hours=2),
        "status_updated_at": NOW - timedelta(hours=3),
        "priority_calculated_at": NOW - timedelta(hours=1),
    }
    values.update(overrides)
    return values


def test_stale_when_last_interaction_is_newer() -> None:
    assert is_stale(
        **_stale_kwargs(
            last_interaction_at=NOW - timedelta(minutes=10),
            priority_calculated_at=NOW - timedelta(hours=1),
        )
    )


def test_stale_when_status_updated_is_newer() -> None:
    assert is_stale(
        **_stale_kwargs(
            status_updated_at=NOW - timedelta(minutes=5),
            priority_calculated_at=NOW - timedelta(hours=1),
        )
    )


def test_stale_when_age_bucket_changed() -> None:
    created = NOW - timedelta(hours=5)
    assert is_stale(
        **_stale_kwargs(
            created_at=created,
            last_interaction_at=created,
            status_updated_at=created,
            priority_calculated_at=created + timedelta(hours=1),
        )
    )


def test_not_stale_when_nothing_changed() -> None:
    created = NOW - timedelta(hours=2)
    calculated = created + timedelta(hours=1)
    assert not is_stale(
        **_stale_kwargs(
            created_at=created,
            last_interaction_at=calculated,
            status_updated_at=created,
            priority_calculated_at=calculated,
        )
    )


def test_stale_when_priority_calculated_at_is_missing() -> None:
    assert is_stale(**_stale_kwargs(priority_calculated_at=None))


def test_apply_uses_policy_preserves_override_and_stamps() -> None:
    created = NOW - timedelta(hours=1)
    conversation = Conversation(
        id=uuid4(),
        order_item_id=uuid4(),
        reason="elogio",
        status="open",
        created_at=created,
        updated_at=created,
        last_interaction_at=created,
        calculated_priority="high",
        ops_override="critical",
        priority_calculated_at=created,
    )
    item = OrderItem(
        id=uuid4(),
        order_id=uuid4(),
        offer_id=uuid4(),
        quantity=1,
        purchase_price=Decimal("10.00"),
        status="cancelled",
        created_at=created,
        updated_at=created,
        status_updated_at=created,
    )
    publisher.clear()
    changed = apply_calculated_priority(conversation, item, now=NOW)
    assert changed is True
    assert conversation.calculated_priority == "low"
    assert conversation.ops_override == "critical"
    assert conversation.priority_calculated_at == NOW
    assert conversation.updated_at == NOW
    assert conversation.last_interaction_at == created
    assert publisher.events == []


def test_apply_stamps_when_class_does_not_change() -> None:
    created = NOW - timedelta(hours=1)
    conversation = Conversation(
        id=uuid4(),
        order_item_id=uuid4(),
        reason="elogio",
        status="open",
        created_at=created,
        updated_at=created,
        last_interaction_at=created,
        calculated_priority="low",
        ops_override=None,
        priority_calculated_at=created,
    )
    item = OrderItem(
        id=uuid4(),
        order_id=uuid4(),
        offer_id=uuid4(),
        quantity=1,
        purchase_price=Decimal("10.00"),
        status="cancelled",
        created_at=created,
        updated_at=created,
        status_updated_at=created,
    )
    changed = apply_calculated_priority(conversation, item, now=NOW)
    assert changed is False
    assert conversation.calculated_priority == "low"
    assert conversation.updated_at == created
    assert conversation.priority_calculated_at == NOW
