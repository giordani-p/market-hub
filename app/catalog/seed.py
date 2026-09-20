"""Seed de vendedores e usuarios de demonstracao."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.catalog.models import Seller
from app.database import get_session_factory

SELLER_A_ID = UUID("11111111-1111-1111-1111-111111111111")
SELLER_B_ID = UUID("22222222-2222-2222-2222-222222222222")

SEED_SELLERS = (
    Seller(id=SELLER_A_ID, name="Loja A"),
    Seller(id=SELLER_B_ID, name="Loja B"),
)


def add_if_missing(session: Session, entity: object) -> bool:
    """Insere a entidade se o id ainda nao existir. Retorna True se inseriu."""
    entity_id = entity.id
    if session.get(type(entity), entity_id) is None:
        session.add(entity)
        return True
    return False


def add_or_replace_content(session: Session, entity: Any) -> None:
    """Insere ou atualiza `content` quando o id ja existe (Message/InternalComment)."""
    existing = session.get(type(entity), entity.id)
    if existing is None:
        session.add(entity)
        return
    if existing.content != entity.content:
        existing.content = entity.content


def seed_sellers(session: Session) -> None:
    """Insere os vendedores fixos se ainda nao existirem."""
    for seller in SEED_SELLERS:
        add_if_missing(session, Seller(id=seller.id, name=seller.name))


def seed_all(session: Session, password: str | None = None) -> None:
    from app.auth.seed import seed_users

    seed_sellers(session)
    session.flush()
    seed_users(session, password)


def seed_demo(session: Session, password: str | None = None) -> None:
    """Dataset rico de marketplace. Nao e usado pelos testes de catalog_client."""
    from app.auth.seed import seed_demo_users
    from app.catalog.demo import seed_demo_catalog, seed_demo_sellers
    from app.communication.seed import seed_demo_conversations
    from app.notifications.seed import seed_demo_notifications
    from app.orders.seed import seed_demo_orders
    from app.support.seed import seed_demo_comments

    now = datetime.now(UTC)
    seed_demo_sellers(session)
    session.flush()
    seed_demo_users(session, password)
    session.flush()
    seed_demo_catalog(session)
    session.flush()
    seed_demo_orders(session, now)
    session.flush()
    seed_demo_conversations(session, now)
    session.flush()
    seed_demo_comments(session, now)
    session.flush()
    seed_demo_notifications(session, now)


def main() -> None:
    with get_session_factory()() as session:
        seed_all(session)
        seed_demo(session)
        session.commit()


if __name__ == "__main__":
    main()
