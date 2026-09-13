from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.communication.lifecycle import (
    SYSTEM_CLOSE_MESSAGE,
    close_by_seller,
    close_for_inactivity,
    is_inactive,
    message_window,
    validate_before,
)
from app.communication.models import Conversation
from app.communication.schemas import CreateMessageRequest
from app.core.config import Settings
from app.core.errors import InvalidTransitionError
from app.core.events import ConversationClosed, MessageCreated, publisher


class _FakeSession:
    def __init__(self) -> None:
        self.info: dict = {}
        self.added: list[object] = []

    def add(self, obj: object) -> None:
        self.added.append(obj)

    def flush(self) -> None:
        return None


def _open_conversation(*, hours_ago: float = 0) -> Conversation:
    now = datetime.now(UTC)
    created = now - timedelta(hours=hours_ago)
    return Conversation(
        id=uuid4(),
        order_item_id=uuid4(),
        reason="atraso",
        status="open",
        created_at=created,
        updated_at=created,
        last_interaction_at=created,
    )


def test_content_is_stripped_and_blank_rejected() -> None:
    assert CreateMessageRequest(content="  hello  ").content == "hello"
    with pytest.raises(ValidationError):
        CreateMessageRequest(content="   ")
    with pytest.raises(ValidationError):
        CreateMessageRequest(content="x" * 2001)
    assert len(CreateMessageRequest(content="x" * 2000).content) == 2000


def test_inactivity_uses_last_interaction() -> None:
    settings = Settings(conversation_inactivity_hours=120, _env_file=None)
    fresh = _open_conversation(hours_ago=1)
    stale = _open_conversation(hours_ago=121)
    closed = _open_conversation(hours_ago=121)
    closed.status = "closed"
    assert not is_inactive(fresh, settings)
    assert is_inactive(stale, settings)
    assert not is_inactive(closed, settings)


def test_before_must_be_aware_and_not_future() -> None:
    now = datetime(2026, 1, 2, tzinfo=UTC)
    with pytest.raises(ValueError, match="timezone-aware"):
        validate_before(datetime(2026, 1, 1), now=now)
    with pytest.raises(ValueError, match="future"):
        validate_before(datetime(2026, 1, 3, tzinfo=UTC), now=now)
    assert validate_before(datetime(2026, 1, 1, tzinfo=UTC), now=now) is not None


def test_message_window_defaults_and_before() -> None:
    now = datetime(2026, 1, 2, 12, tzinfo=UTC)
    window_from, window_to, exclusive = message_window(before=None, now=now)
    assert exclusive is False
    assert window_to == now
    assert window_from == now - timedelta(hours=24)

    before = datetime(2026, 1, 1, 12, tzinfo=UTC)
    window_from, window_to, exclusive = message_window(before=before, now=now)
    assert exclusive is True
    assert window_to == before
    assert window_from == before - timedelta(hours=24)


def test_close_for_inactivity_is_idempotent_and_records_system_message() -> None:
    session = _FakeSession()
    conversation = _open_conversation()
    assert close_for_inactivity(session, conversation) is True  # type: ignore[arg-type]
    assert conversation.status == "closed"
    assert any(getattr(obj, "content", None) == SYSTEM_CLOSE_MESSAGE for obj in session.added)
    assert close_for_inactivity(session, conversation) is False  # type: ignore[arg-type]
    system_messages = [
        obj for obj in session.added if getattr(obj, "author_type", None) == "system"
    ]
    assert len(system_messages) == 1


def test_manual_close_does_not_add_system_message() -> None:
    session = _FakeSession()
    conversation = _open_conversation()
    settings = Settings(conversation_inactivity_hours=120, _env_file=None)
    close_by_seller(session, conversation, settings)  # type: ignore[arg-type]
    assert conversation.status == "closed"
    assert session.added == []
    with pytest.raises(InvalidTransitionError):
        close_by_seller(session, conversation, settings)  # type: ignore[arg-type]


def test_inactivity_events_are_recorded_not_published() -> None:
    from app.core.events import PENDING_KEY

    publisher.clear()
    session = _FakeSession()
    conversation = _open_conversation()
    close_for_inactivity(session, conversation)  # type: ignore[arg-type]
    assert publisher.events == []
    pending = session.info[PENDING_KEY]
    assert any(isinstance(event, MessageCreated) for event in pending)
    assert any(
        isinstance(event, ConversationClosed) and event.closed_by == "inactivity"
        for event in pending
    )
