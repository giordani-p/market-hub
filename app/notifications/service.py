"""Transforma o Job NOTIFY_STATUS_CHANGE em Notifications in-app."""

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.jobs.models import Job
from app.notifications.channel import InAppNotificationChannel, NotificationChannel
from app.notifications.copy import build_copy
from app.notifications.models import Notification
from app.notifications.recipients import resolve_recipients

logger = logging.getLogger(__name__)


def process_notify_job(
    session: Session,
    job: Job,
    channel: NotificationChannel | None = None,
) -> None:
    params = job.params
    notification_type = _require_str(params, "notification_type")
    entity_type = _require_str(params, "entity_type")
    previous_status = _require_str(params, "previous_status")
    new_status = _require_str(params, "new_status")
    entity_id = UUID(_require_str(params, "entity_id"))
    changed_at = datetime.fromisoformat(_require_str(params, "changed_at"))

    logger.info(
        "notification job received type=%s entity_type=%s entity_id=%s",
        notification_type,
        entity_type,
        entity_id,
    )

    recipients = resolve_recipients(
        session,
        notification_type=notification_type,
        entity_id=entity_id,
        entity_type=entity_type,
    )
    if not recipients:
        logger.info(
            "notification job skipped entity_type=%s entity_id=%s reason=no_recipients",
            entity_type,
            entity_id,
        )
        return

    title, message = build_copy(
        notification_type=notification_type,
        previous_status=previous_status,
        new_status=new_status,
    )
    target = channel or InAppNotificationChannel()
    created = 0
    ignored = 0
    for recipient_id in recipients:
        notification = Notification(
            recipient_id=recipient_id,
            notification_type=notification_type,
            title=title,
            message=message,
            entity_type=entity_type,
            entity_id=entity_id,
            previous_status=previous_status,
            new_status=new_status,
            changed_at=changed_at,
        )
        if target.send(session, notification):
            created += 1
        else:
            ignored += 1
            logger.info(
                "notification ignored by idempotency type=%s entity_id=%s recipient_id=%s",
                notification_type,
                entity_id,
                recipient_id,
            )

    logger.info(
        "notification job finished type=%s entity_id=%s recipients=%s created=%s ignored=%s",
        notification_type,
        entity_id,
        len(recipients),
        created,
        ignored,
    )


def _require_str(params: dict[str, object], key: str) -> str:
    value = params.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} is required")
    return value
