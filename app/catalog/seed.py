"""Seed de vendedores. Identidade minima, sem rotas na v0."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.catalog.models import Seller
from app.database import get_session_factory

SELLER_A_ID = UUID("11111111-1111-1111-1111-111111111111")
SELLER_B_ID = UUID("22222222-2222-2222-2222-222222222222")

SEED_SELLERS = (
    Seller(id=SELLER_A_ID, name="Loja A"),
    Seller(id=SELLER_B_ID, name="Loja B"),
)


def seed_sellers(session: Session) -> None:
    """Insere os vendedores fixos se ainda nao existirem."""
    for seller in SEED_SELLERS:
        exists = session.scalar(select(Seller.id).where(Seller.id == seller.id))
        if exists is None:
            session.add(Seller(id=seller.id, name=seller.name))


def main() -> None:
    with get_session_factory()() as session:
        seed_sellers(session)


if __name__ == "__main__":
    main()
