"""Canal in-app: persiste a Notification no PostgreSQL."""

from typing import Protocol

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.notifications.models import Notification


class NotificationChannel(Protocol):
    def send(self, session: Session, notification: Notification) -> bool:
        """True se inseriu; False se a unique de idempotencia ignorou."""
        ...


class InAppNotificationChannel:
    """Unico canal desta fase. Sem Email/Slack/WhatsApp."""

    def send(self, session: Session, notification: Notification) -> bool:
        try:
            with session.begin_nested():
                session.add(notification)
                session.flush()
        except IntegrityError:
            return False
        return True
