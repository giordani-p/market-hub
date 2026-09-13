"""Reconcilia calculated_priority de Conversations OPEN stale."""

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, and_, case, func, literal, or_, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.sql import ColumnElement

from app.communication.lifecycle import utcnow
from app.communication.models import Conversation
from app.communication.priority import AGE_BUCKET_HOURS, apply_calculated_priority
from app.core.config import Settings, get_settings
from app.database import get_session_factory, session_transaction
from app.orders.models import OrderItem


@dataclass(frozen=True)
class ReconcileResult:
    found: int
    processed: int
    updated: int
    unchanged: int


def _hours(start: ColumnElement[datetime], end: ColumnElement[datetime]) -> ColumnElement[float]:
    return func.extract("epoch", end - start) / 3600.0


def _bucket_rank(hours: ColumnElement[float]) -> ColumnElement[int]:
    whens = [(hours < boundary, literal(index)) for index, boundary in enumerate(AGE_BUCKET_HOURS)]
    return case(*whens, else_=literal(len(AGE_BUCKET_HOURS)))


def stale_clause(now: datetime) -> ColumnElement[bool]:
    """Predicado SQL equivalente a is_stale. now vem da aplicacao, nao now() do banco."""
    calculated_at = Conversation.priority_calculated_at
    return or_(
        calculated_at.is_(None),
        Conversation.last_interaction_at > calculated_at,
        OrderItem.status_updated_at > calculated_at,
        and_(
            calculated_at.is_not(None),
            _bucket_rank(_hours(Conversation.created_at, literal(now)))
            != _bucket_rank(_hours(Conversation.created_at, calculated_at)),
        ),
    )


def stale_statement(now: datetime) -> Select[tuple[Conversation, OrderItem]]:
    return (
        select(Conversation, OrderItem)
        .join(OrderItem, Conversation.order_item_id == OrderItem.id)
        .where(Conversation.status == "open", stale_clause(now))
        .order_by(Conversation.id)
    )


def list_stale_page(
    session: Session,
    *,
    now: datetime,
    page_size: int,
    after_id: UUID | None = None,
) -> Sequence[tuple[Conversation, OrderItem]]:
    stmt = stale_statement(now)
    if after_id is not None:
        stmt = stmt.where(Conversation.id > after_id)
    return session.execute(stmt.limit(page_size)).all()


@contextmanager
def _transaction(factory: sessionmaker[Session]) -> Iterator[Session]:
    yield from session_transaction(factory)


def run_reconcile(
    factory: sessionmaker[Session] | None = None,
    settings: Settings | None = None,
    *,
    now: datetime | None = None,
    page_size: int | None = None,
) -> ReconcileResult:
    factory = factory or get_session_factory()
    settings = settings or get_settings()
    moment = now or utcnow()
    size = page_size or settings.reconcile_page_size
    after_id: UUID | None = None
    found = 0
    processed = 0
    updated = 0
    unchanged = 0

    while True:
        with _transaction(factory) as session:
            rows = list_stale_page(session, now=moment, page_size=size, after_id=after_id)
            if not rows:
                break
            found += len(rows)
            for conversation, item in rows:
                if apply_calculated_priority(conversation, item, now=moment, session=session):
                    updated += 1
                else:
                    unchanged += 1
                processed += 1
            after_id = rows[-1][0].id

    return ReconcileResult(
        found=found,
        processed=processed,
        updated=updated,
        unchanged=unchanged,
    )
