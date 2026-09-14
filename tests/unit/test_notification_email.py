import logging
from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.jobs.models import NOTIFY_STATUS_CHANGE, Job
from app.notifications import email as email_module
from app.notifications.delivery import should_email
from app.notifications.email import ConsoleEmailSender
from app.notifications.models import (
    CONVERSATION_PRIORITY_CHANGED,
    CONVERSATION_STATUS_CHANGED,
    ENTITY_CONVERSATION,
    ENTITY_ORDER_ITEM,
    ORDER_ITEM_STATUS_CHANGED,
)
from app.notifications.recipients import merge_email_recipients
from app.notifications.service import process_notify_job


class _FakeChannel:
    def send(self, session: object, notification: object) -> bool:
        del session, notification
        return True


class _FakeEmailSender:
    def __init__(self) -> None:
        self.sent: list[dict[str, object]] = []

    def send(
        self,
        *,
        to: list[str],
        subject: str,
        body: str,
        entity_id: object,
        new_status: str,
    ) -> None:
        self.sent.append(
            {
                "to": to,
                "subject": subject,
                "body": body,
                "entity_id": entity_id,
                "new_status": new_status,
            }
        )


def _job(*, notification_type: str, new_status: str, entity_type: str = ENTITY_CONVERSATION) -> Job:
    return Job(
        job_type=NOTIFY_STATUS_CHANGE,
        params={
            "notification_type": notification_type,
            "entity_type": entity_type,
            "entity_id": str(uuid4()),
            "previous_status": "medium",
            "new_status": new_status,
            "changed_at": datetime.now(UTC).isoformat(),
        },
    )


@pytest.mark.parametrize(
    ("notification_type", "new_status", "expected"),
    [
        (CONVERSATION_PRIORITY_CHANGED, "high", True),
        (CONVERSATION_PRIORITY_CHANGED, "critical", True),
        (CONVERSATION_PRIORITY_CHANGED, "low", False),
        (CONVERSATION_PRIORITY_CHANGED, "medium", False),
        (ORDER_ITEM_STATUS_CHANGED, "high", False),
        (CONVERSATION_STATUS_CHANGED, "critical", False),
    ],
)
def test_should_email(notification_type: str, new_status: str, expected: bool) -> None:
    assert should_email(notification_type, new_status) is expected


def test_merge_email_recipients_seller_then_extra() -> None:
    assert merge_email_recipients("loja-a@example.com", "ops-alerta@example.com") == [
        "loja-a@example.com",
        "ops-alerta@example.com",
    ]


def test_merge_email_recipients_skips_empty_and_duplicate() -> None:
    assert merge_email_recipients("loja-a@example.com", "") == ["loja-a@example.com"]
    assert merge_email_recipients("loja-a@example.com", "  ") == ["loja-a@example.com"]
    assert merge_email_recipients(None, "") == []
    assert merge_email_recipients("loja-a@example.com", "loja-a@example.com") == [
        "loja-a@example.com"
    ]
    assert merge_email_recipients(None, "extra@example.com") == ["extra@example.com"]
    assert merge_email_recipients("  seller@example.com  ", " extra@example.com ") == [
        "seller@example.com",
        "extra@example.com",
    ]


def test_console_email_sender_logs_recipients() -> None:
    entity_id = uuid4()
    records: list[str] = []

    class _Handler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record.getMessage())

    logger = email_module.logger
    handler = _Handler()
    previous_level = logger.level
    previous_disabled = logger.disabled
    previous_disable = logging.root.manager.disable
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.disabled = False
    logging.disable(logging.NOTSET)
    try:
        ConsoleEmailSender().send(
            to=["loja-a@example.com", "extra@example.com"],
            subject="Conversation priority updated",
            body="Priority changed from medium to critical.",
            entity_id=entity_id,
            new_status="critical",
        )
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous_level)
        logger.disabled = previous_disabled
        logging.disable(previous_disable)
    assert records
    assert "loja-a@example.com,extra@example.com" in records[0]
    assert "Conversation priority updated" in records[0]
    assert str(entity_id) in records[0]
    assert "new_status=critical" in records[0]


def test_process_notify_job_emails_high_and_critical(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.notifications.service.resolve_recipients",
        lambda *args, **kwargs: [uuid4()],
    )
    captured: list[str] = []

    def fake_resolve_email(session: object, *, entity_id: object, entity_type: str, extra: str):
        del session, entity_id, entity_type
        captured.append(extra)
        return ["loja-a@example.com"] + ([extra] if extra else [])

    monkeypatch.setattr("app.notifications.service.resolve_email_recipients", fake_resolve_email)

    for new_status in ("high", "critical"):
        sender = _FakeEmailSender()
        process_notify_job(
            MagicMock(),
            _job(notification_type=CONVERSATION_PRIORITY_CHANGED, new_status=new_status),
            channel=_FakeChannel(),
            email_sender=sender,
            extra_email_to="alerta@example.com",
        )
        assert sender.sent[0]["to"] == ["loja-a@example.com", "alerta@example.com"]
        assert sender.sent[0]["new_status"] == new_status
        assert captured[-1] == "alerta@example.com"


def test_process_notify_job_skips_email_for_order_item(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.notifications.service.resolve_recipients",
        lambda *args, **kwargs: [uuid4()],
    )
    called = False

    def fake_resolve_email(*args: object, **kwargs: object) -> list[str]:
        del args, kwargs
        nonlocal called
        called = True
        return ["loja-a@example.com"]

    monkeypatch.setattr("app.notifications.service.resolve_email_recipients", fake_resolve_email)
    sender = _FakeEmailSender()
    process_notify_job(
        MagicMock(),
        _job(
            notification_type=ORDER_ITEM_STATUS_CHANGED,
            new_status="preparing",
            entity_type=ENTITY_ORDER_ITEM,
        ),
        channel=_FakeChannel(),
        email_sender=sender,
        extra_email_to="alerta@example.com",
    )
    assert sender.sent == []
    assert called is False


def test_process_notify_job_skips_when_no_email_recipients(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.notifications.service.resolve_recipients",
        lambda *args, **kwargs: [uuid4()],
    )
    monkeypatch.setattr(
        "app.notifications.service.resolve_email_recipients",
        lambda *args, **kwargs: [],
    )
    sender = _FakeEmailSender()
    process_notify_job(
        MagicMock(),
        _job(notification_type=CONVERSATION_PRIORITY_CHANGED, new_status="critical"),
        channel=_FakeChannel(),
        email_sender=sender,
        extra_email_to="",
    )
    assert sender.sent == []
