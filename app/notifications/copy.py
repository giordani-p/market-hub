"""Title e message gerados pelo backend, prontos para apresentacao."""

from app.notifications.models import (
    CONVERSATION_PRIORITY_CHANGED,
    CONVERSATION_STATUS_CHANGED,
    ORDER_ITEM_STATUS_CHANGED,
)


def build_copy(*, notification_type: str, previous_status: str, new_status: str) -> tuple[str, str]:
    """Retorna (title, message) em ingles."""
    if notification_type == ORDER_ITEM_STATUS_CHANGED:
        return (
            "Order item status updated",
            f"Status changed from {previous_status} to {new_status}.",
        )
    if notification_type == CONVERSATION_STATUS_CHANGED:
        return (
            "Conversation closed",
            f"Conversation status changed from {previous_status} to {new_status}.",
        )
    if notification_type == CONVERSATION_PRIORITY_CHANGED:
        return (
            "Conversation priority updated",
            f"Priority changed from {previous_status} to {new_status}.",
        )
    raise ValueError(f"unknown notification type: {notification_type}")
