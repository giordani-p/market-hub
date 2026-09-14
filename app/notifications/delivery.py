"""Politica de entrega por canal. Slack/SMS plugam aqui."""

from app.notifications.models import CONVERSATION_PRIORITY_CHANGED

ALERT_PRIORITIES = frozenset({"high", "critical"})


def should_email(notification_type: str, new_status: str) -> bool:
    """True quando a prioridade efetiva vira high ou critical."""
    return notification_type == CONVERSATION_PRIORITY_CHANGED and new_status in ALERT_PRIORITIES
