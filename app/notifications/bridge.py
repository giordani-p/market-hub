"""Domain Event -> Job NOTIFY_STATUS_CHANGE. Falha no SQS nao desfaz o commit."""

import json
import logging
from datetime import UTC, datetime

from app.core.events import ConversationClosed, ConversationPriorityChanged, OrderItemStatusChanged
from app.jobs.models import NOTIFY_STATUS_CHANGE, Job
from app.jobs.queue import get_job_queue
from app.notifications.models import (
    CONVERSATION_PRIORITY_CHANGED,
    CONVERSATION_STATUS_CHANGED,
    ENTITY_CONVERSATION,
    ENTITY_ORDER_ITEM,
    ORDER_ITEM_STATUS_CHANGED,
)

logger = logging.getLogger(__name__)


def job_from_event(event: object, *, now: datetime | None = None) -> Job | None:
    """None quando o evento nao e notificavel."""
    moment = now or datetime.now(UTC)
    if isinstance(event, OrderItemStatusChanged):
        return Job(
            job_type=NOTIFY_STATUS_CHANGE,
            params={
                "notification_type": ORDER_ITEM_STATUS_CHANGED,
                "entity_type": ENTITY_ORDER_ITEM,
                "entity_id": str(event.order_item_id),
                "previous_status": event.from_status,
                "new_status": event.to_status,
                "changed_at": moment.isoformat(),
            },
        )
    if isinstance(event, ConversationClosed):
        return Job(
            job_type=NOTIFY_STATUS_CHANGE,
            params={
                "notification_type": CONVERSATION_STATUS_CHANGED,
                "entity_type": ENTITY_CONVERSATION,
                "entity_id": str(event.conversation_id),
                "previous_status": "open",
                "new_status": "closed",
                "changed_at": moment.isoformat(),
            },
        )
    if isinstance(event, ConversationPriorityChanged):
        return Job(
            job_type=NOTIFY_STATUS_CHANGE,
            params={
                "notification_type": CONVERSATION_PRIORITY_CHANGED,
                "entity_type": ENTITY_CONVERSATION,
                "entity_id": str(event.conversation_id),
                "previous_status": event.from_priority,
                "new_status": event.to_priority,
                "changed_at": event.changed_at.isoformat(),
            },
        )
    return None


def enqueue_notifiable(events: list[object]) -> None:
    queue = get_job_queue()
    for event in events:
        job = job_from_event(event)
        if job is None:
            continue
        payload = json.dumps({"job_type": job.job_type, "params": job.params})
        try:
            queue.send(payload)
        except Exception:
            logger.exception(
                "failed to enqueue notification job type=%s entity_id=%s",
                job.params.get("notification_type"),
                job.params.get("entity_id"),
            )
            continue
        logger.info(
            "notification job enqueued type=%s entity_type=%s entity_id=%s",
            job.params.get("notification_type"),
            job.params.get("entity_type"),
            job.params.get("entity_id"),
        )
