"""Eventos de dominio em processo, sem bus.

Eventos sao acumulados em session.info durante a transacao e publicados
somente apos o commit. Flush ou rollback nao disparam publicacao.
"""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

PENDING_KEY = "pending_domain_events"


@dataclass(frozen=True)
class OrderCreated:
    order_id: UUID
    buyer_id: UUID


@dataclass(frozen=True)
class OrderItemStatusChanged:
    order_item_id: UUID
    from_status: str
    to_status: str


@dataclass(frozen=True)
class OrderItemCancelled:
    order_item_id: UUID
    restored_stock: bool


@dataclass(frozen=True)
class ConversationCreated:
    conversation_id: UUID
    order_item_id: UUID


@dataclass(frozen=True)
class MessageCreated:
    message_id: UUID
    conversation_id: UUID


@dataclass(frozen=True)
class ConversationClosed:
    conversation_id: UUID
    closed_by: str


class InMemoryEventPublisher:
    """Publisher de processo unico, para testes e evolucao futura."""

    def __init__(self) -> None:
        self.events: list[object] = []

    def publish(self, event: object) -> None:
        self.events.append(event)

    def clear(self) -> None:
        self.events.clear()


publisher = InMemoryEventPublisher()


def get_publisher() -> InMemoryEventPublisher:
    return publisher


def record_event(session: Session, event: object) -> None:
    """Acumula um evento para publicacao apos o commit."""
    session.info.setdefault(PENDING_KEY, []).append(event)


def publish_pending(session: Session) -> None:
    events = session.info.pop(PENDING_KEY, [])
    for event in events:
        publisher.publish(event)
