"""Regras de criacao, mensagens e encerramento de Conversation."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.models import User, UserRole
from app.communication.models import Conversation, Message
from app.core.config import Settings
from app.core.errors import InvalidTransitionError
from app.core.events import ConversationClosed, ConversationCreated, MessageCreated, record_event

SYSTEM_CLOSE_MESSAGE = (
    "Esta conversa foi encerrada automaticamente após 5 dias sem novas mensagens. "
    "Se precisar de ajuda novamente, inicie uma nova conversa."
)
MESSAGE_WINDOW = timedelta(hours=24)


def utcnow() -> datetime:
    return datetime.now(UTC)


def inactivity_cutoff(settings: Settings, *, now: datetime | None = None) -> datetime:
    moment = now or utcnow()
    return moment - timedelta(hours=settings.conversation_inactivity_hours)


def is_inactive(
    conversation: Conversation, settings: Settings, *, now: datetime | None = None
) -> bool:
    if conversation.status != "open":
        return False
    return conversation.last_interaction_at <= inactivity_cutoff(settings, now=now)


def _touch(conversation: Conversation, *, now: datetime) -> None:
    conversation.updated_at = now
    conversation.last_interaction_at = now


def _open_for_item(session: Session, order_item_id: UUID) -> Conversation | None:
    return session.scalar(
        select(Conversation).where(
            Conversation.order_item_id == order_item_id,
            Conversation.status == "open",
        )
    )


def get_or_create_conversation(
    session: Session, order_item_id: UUID, reason: str
) -> tuple[Conversation, bool]:
    """Reusa a OPEN existente ou cria uma nova. created=True apenas na insercao."""
    existing = _open_for_item(session, order_item_id)
    if existing is not None:
        return existing, False

    now = utcnow()
    conversation = Conversation(
        order_item_id=order_item_id,
        reason=reason,
        status="open",
        created_at=now,
        updated_at=now,
        last_interaction_at=now,
    )
    try:
        with session.begin_nested():
            session.add(conversation)
            session.flush()
    except IntegrityError:
        existing = _open_for_item(session, order_item_id)
        if existing is None:
            raise
        return existing, False

    record_event(
        session,
        ConversationCreated(conversation_id=conversation.id, order_item_id=order_item_id),
    )
    return conversation, True


def close_for_inactivity(session: Session, conversation: Conversation) -> bool:
    """Fecha por inatividade. False se ja estiver closed (idempotente)."""
    if conversation.status != "open":
        return False

    now = utcnow()
    message = Message(
        conversation_id=conversation.id,
        author_type="system",
        author_user_id=None,
        content=SYSTEM_CLOSE_MESSAGE,
        created_at=now,
    )
    session.add(message)
    session.flush()
    conversation.status = "closed"
    _touch(conversation, now=now)
    record_event(session, MessageCreated(message_id=message.id, conversation_id=conversation.id))
    record_event(
        session,
        ConversationClosed(conversation_id=conversation.id, closed_by="inactivity"),
    )
    return True


def maybe_close_inactive(
    session: Session, conversation: Conversation, settings: Settings
) -> Conversation:
    """Fecha se a OPEN estiver inativa. Assume lock FOR UPDATE quando for persistir."""
    if not is_inactive(conversation, settings):
        return conversation
    close_for_inactivity(session, conversation)
    return conversation


def close_by_seller(
    session: Session, conversation: Conversation, settings: Settings
) -> Conversation:
    maybe_close_inactive(session, conversation, settings)
    if conversation.status != "open":
        raise InvalidTransitionError("Conversation is already closed")
    now = utcnow()
    conversation.status = "closed"
    conversation.updated_at = now
    record_event(
        session,
        ConversationClosed(conversation_id=conversation.id, closed_by="manual"),
    )
    return conversation


def author_type_for(user: User) -> str:
    if user.role == UserRole.SELLER:
        return "seller"
    return "buyer"


def add_message(
    session: Session, conversation: Conversation, user: User, content: str, settings: Settings
) -> Message:
    maybe_close_inactive(session, conversation, settings)
    if conversation.status != "open":
        raise InvalidTransitionError("Conversation is closed")

    now = utcnow()
    message = Message(
        conversation_id=conversation.id,
        author_type=author_type_for(user),
        author_user_id=user.id,
        content=content,
        created_at=now,
    )
    session.add(message)
    session.flush()
    _touch(conversation, now=now)
    record_event(session, MessageCreated(message_id=message.id, conversation_id=conversation.id))
    return message


def message_window(
    *, before: datetime | None, now: datetime | None = None
) -> tuple[datetime, datetime, bool]:
    """Retorna (from, to, exclusive_to). exclusive_to e True quando before foi informado."""
    moment = now or utcnow()
    if before is None:
        window_to = moment
        return window_to - MESSAGE_WINDOW, window_to, False
    return before - MESSAGE_WINDOW, before, True


def validate_before(before: datetime | None, *, now: datetime | None = None) -> datetime | None:
    if before is None:
        return None
    if before.tzinfo is None:
        raise ValueError("before must be timezone-aware")
    moment = now or utcnow()
    if before > moment:
        raise ValueError("before cannot be in the future")
    return before
