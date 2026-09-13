"""Fecha Conversations OPEN inativas. Uma transacao por Conversation."""

from collections.abc import Iterator
from contextlib import contextmanager
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.communication.lifecycle import close_for_inactivity, inactivity_cutoff, is_inactive
from app.communication.models import Conversation
from app.core.config import Settings, get_settings
from app.core.events import publish_pending
from app.database import get_session_factory


@contextmanager
def _transaction(factory: sessionmaker[Session]) -> Iterator[Session]:
    session = factory()
    try:
        yield session
        session.commit()
        publish_pending(session)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _eligible_ids(session: Session, settings: Settings) -> list[UUID]:
    cutoff = inactivity_cutoff(settings)
    return list(
        session.scalars(
            select(Conversation.id).where(
                Conversation.status == "open",
                Conversation.last_interaction_at <= cutoff,
            )
        )
    )


def close_one_inactive(session: Session, conversation_id: UUID, settings: Settings) -> bool:
    conversation = session.scalar(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .with_for_update(skip_locked=True)
    )
    if conversation is None or not is_inactive(conversation, settings):
        return False
    return close_for_inactivity(session, conversation)


def run_close_inactive(
    factory: sessionmaker[Session] | None = None,
    settings: Settings | None = None,
) -> int:
    """Processa cada Conversation elegivel em transacao propria."""
    factory = factory or get_session_factory()
    settings = settings or get_settings()
    with _transaction(factory) as session:
        ids = _eligible_ids(session, settings)

    closed = 0
    for conversation_id in ids:
        with _transaction(factory) as session:
            if close_one_inactive(session, conversation_id, settings):
                closed += 1
    return closed


def main() -> None:
    closed = run_close_inactive()
    print(f"Closed {closed} inactive conversation(s)")


if __name__ == "__main__":
    main()
