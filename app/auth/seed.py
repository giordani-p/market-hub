"""Usuarios de demonstracao associados aos vendedores do catalogo."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import User, UserRole
from app.auth.passwords import hash_password
from app.catalog.models import Seller
from app.catalog.seed import SELLER_A_ID, SELLER_B_ID
from app.core.config import get_settings

SELLER_A_USER_ID = UUID("aaaaaaaa-1111-1111-1111-111111111111")
SELLER_B_USER_ID = UUID("bbbbbbbb-2222-2222-2222-222222222222")
BUYER_ID = UUID("33333333-3333-3333-3333-333333333333")
OPS_ID = UUID("44444444-4444-4444-4444-444444444444")

SELLER_A_EMAIL = "loja-a@example.com"
SELLER_B_EMAIL = "loja-b@example.com"
BUYER_EMAIL = "buyer@example.com"
OPS_EMAIL = "ops@example.com"


def seed_users(session: Session, password: str | None = None) -> None:
    """Insere users de demo se ainda nao existirem. Senha vem de SEED_PASSWORD."""
    password = password or get_settings().seed_password
    if not password:
        raise RuntimeError("SEED_PASSWORD is not set")

    password_hash = hash_password(password)
    users = (
        User(
            id=SELLER_A_USER_ID,
            email=SELLER_A_EMAIL,
            name="Loja A",
            password_hash=password_hash,
            role=UserRole.SELLER,
            seller_id=SELLER_A_ID,
        ),
        User(
            id=SELLER_B_USER_ID,
            email=SELLER_B_EMAIL,
            name="Loja B",
            password_hash=password_hash,
            role=UserRole.SELLER,
            seller_id=SELLER_B_ID,
        ),
        User(
            id=BUYER_ID,
            email=BUYER_EMAIL,
            name="Buyer Demo",
            password_hash=password_hash,
            role=UserRole.BUYER,
            seller_id=None,
        ),
        User(
            id=OPS_ID,
            email=OPS_EMAIL,
            name="Ops Demo",
            password_hash=password_hash,
            role=UserRole.OPS,
            seller_id=None,
        ),
    )
    for user in users:
        exists = session.scalar(select(User.id).where(User.id == user.id))
        if exists is None:
            if user.seller_id is not None and session.get(Seller, user.seller_id) is None:
                raise RuntimeError(f"Seller {user.seller_id} must be seeded before users")
            session.add(user)
