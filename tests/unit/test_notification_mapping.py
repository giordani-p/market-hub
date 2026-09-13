from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from app.communication.models import Conversation
from app.communication.priority import apply_calculated_priority
from app.core.events import (
    PENDING_KEY,
    ConversationClosed,
    ConversationCreated,
    ConversationPriorityChanged,
    MessageCreated,
    OrderCreated,
    OrderItemStatusChanged,
)
from app.jobs.models import NOTIFY_STATUS_CHANGE
from app.notifications.bridge import job_from_event
from app.notifications.copy import build_copy
from app.notifications.models import (
    CONVERSATION_PRIORITY_CHANGED,
    CONVERSATION_STATUS_CHANGED,
    ENTITY_CONVERSATION,
    ENTITY_ORDER_ITEM,
    ORDER_ITEM_STATUS_CHANGED,
)
from app.orders.models import OrderItem

NOW = datetime(2026, 9, 13, 18, 0, tzinfo=UTC)


class _FakeSession:
    def __init__(self) -> None:
        self.info: dict = {}


def test_job_from_order_item_status_changed() -> None:
    event = OrderItemStatusChanged(
        order_item_id=uuid4(), from_status="placed", to_status="preparing"
    )
    job = job_from_event(event, now=NOW)
    assert job is not None
    assert job.job_type == NOTIFY_STATUS_CHANGE
    assert job.params["notification_type"] == ORDER_ITEM_STATUS_CHANGED
    assert job.params["entity_type"] == ENTITY_ORDER_ITEM
    assert job.params["previous_status"] == "placed"
    assert job.params["new_status"] == "preparing"
    assert job.params["changed_at"] == NOW.isoformat()


def test_job_from_conversation_closed() -> None:
    event = ConversationClosed(conversation_id=uuid4(), closed_by="manual")
    job = job_from_event(event, now=NOW)
    assert job is not None
    assert job.params["notification_type"] == CONVERSATION_STATUS_CHANGED
    assert job.params["entity_type"] == ENTITY_CONVERSATION
    assert job.params["previous_status"] == "open"
    assert job.params["new_status"] == "closed"


def test_job_from_priority_changed_uses_event_timestamp() -> None:
    event = ConversationPriorityChanged(
        conversation_id=uuid4(),
        from_priority="medium",
        to_priority="high",
        changed_at=NOW,
    )
    job = job_from_event(event)
    assert job is not None
    assert job.params["notification_type"] == CONVERSATION_PRIORITY_CHANGED
    assert job.params["previous_status"] == "medium"
    assert job.params["new_status"] == "high"
    assert job.params["changed_at"] == NOW.isoformat()


def test_message_created_and_conversation_created_are_not_notifiable() -> None:
    assert job_from_event(MessageCreated(message_id=uuid4(), conversation_id=uuid4())) is None
    created = ConversationCreated(conversation_id=uuid4(), order_item_id=uuid4())
    assert job_from_event(created) is None
    assert job_from_event(OrderCreated(order_id=uuid4(), buyer_id=uuid4())) is None


def test_copy_for_each_notification_type() -> None:
    title, message = build_copy(
        notification_type=ORDER_ITEM_STATUS_CHANGED,
        previous_status="placed",
        new_status="preparing",
    )
    assert "placed" in message
    assert "preparing" in message
    assert title
    title, message = build_copy(
        notification_type=CONVERSATION_STATUS_CHANGED,
        previous_status="open",
        new_status="closed",
    )
    assert "closed" in message
    title, message = build_copy(
        notification_type=CONVERSATION_PRIORITY_CHANGED,
        previous_status="low",
        new_status="critical",
    )
    assert "low" in message
    assert "critical" in message


def test_apply_records_priority_event_only_when_effective_changes() -> None:
    created = NOW - timedelta(hours=50)
    conversation = Conversation(
        id=uuid4(),
        order_item_id=uuid4(),
        reason="atraso",
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
        purchase_price=Decimal("5000.00"),
        status="in_transit",
        created_at=created,
        updated_at=created,
        status_updated_at=created,
    )
    session = _FakeSession()
    changed = apply_calculated_priority(conversation, item, now=NOW, session=session)
    assert changed is True
    events = session.info[PENDING_KEY]
    assert len(events) == 1
    event = events[0]
    assert isinstance(event, ConversationPriorityChanged)
    assert event.from_priority == "low"
    assert event.to_priority == "high"


def test_apply_does_not_record_when_override_keeps_effective() -> None:
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
    session = _FakeSession()
    changed = apply_calculated_priority(conversation, item, now=NOW, session=session)
    assert changed is True
    assert conversation.calculated_priority == "low"
    assert PENDING_KEY not in session.info
