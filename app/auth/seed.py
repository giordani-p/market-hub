"""Usuarios de demonstracao associados aos vendedores do catalogo."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.auth.models import User, UserRole
from app.auth.passwords import hash_password
from app.catalog.models import Seller
from app.catalog.seed import SELLER_A_ID, SELLER_B_ID, add_if_missing
from app.core.config import get_settings

SELLER_A_USER_ID = UUID("aaaaaaaa-1111-1111-1111-111111111111")
SELLER_B_USER_ID = UUID("bbbbbbbb-2222-2222-2222-222222222222")
BUYER_ID = UUID("33333333-3333-3333-3333-333333333333")
OPS_ID = UUID("44444444-4444-4444-4444-444444444444")

SELLER_A_EMAIL = "loja-a@example.com"
SELLER_B_EMAIL = "loja-b@example.com"
BUYER_EMAIL = "buyer@example.com"
OPS_EMAIL = "ops@example.com"

SELLER_TECH_USER_ID = UUID("aaaaaaaa-5555-5555-5555-555555555551")
SELLER_CASA_USER_ID = UUID("aaaaaaaa-5555-5555-5555-555555555552")
SELLER_ESPORTE_USER_ID = UUID("aaaaaaaa-5555-5555-5555-555555555553")
SELLER_LIVROS_USER_ID = UUID("aaaaaaaa-5555-5555-5555-555555555554")
SELLER_MODA_USER_ID = UUID("aaaaaaaa-5555-5555-5555-555555555555")
SELLER_KIDS_USER_ID = UUID("aaaaaaaa-5555-5555-5555-555555555556")

BUYER_ANA_ID = UUID("66666666-6666-6666-6666-666666666661")
BUYER_BRUNO_ID = UUID("66666666-6666-6666-6666-666666666662")
BUYER_CARLA_ID = UUID("66666666-6666-6666-6666-666666666663")
BUYER_DIEGO_ID = UUID("66666666-6666-6666-6666-666666666664")
BUYER_ELENA_ID = UUID("66666666-6666-6666-6666-666666666665")
BUYER_FABIO_ID = UUID("66666666-6666-6666-6666-666666666666")
BUYER_GIOVANA_ID = UUID("66666666-6666-6666-6666-666666666667")
BUYER_HENRIQUE_ID = UUID("66666666-6666-6666-6666-666666666668")
BUYER_ISABEL_ID = UUID("66666666-6666-6666-6666-666666666669")
BUYER_JOAO_ID = UUID("66666666-6666-6666-6666-66666666666a")


def _require_password(password: str | None) -> str:
    secret = password or get_settings().seed_password
    if not secret:
        raise RuntimeError("SEED_PASSWORD is not set")
    return secret


def _add_user(session: Session, user: User) -> None:
    if user.seller_id is not None and session.get(Seller, user.seller_id) is None:
        raise RuntimeError(f"Seller {user.seller_id} must be seeded before users")
    add_if_missing(session, user)


def seed_users(session: Session, password: str | None = None) -> None:
    """Insere users de identidade se ainda nao existirem. Senha vem de SEED_PASSWORD."""
    password_hash = hash_password(_require_password(password))
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
        _add_user(session, user)


def seed_demo_users(session: Session, password: str | None = None) -> None:
    """Insere sellers e buyers extras da demonstracao."""
    from app.catalog.demo import (
        SELLER_CASA_ID,
        SELLER_ESPORTE_ID,
        SELLER_KIDS_ID,
        SELLER_LIVROS_ID,
        SELLER_MODA_ID,
        SELLER_TECH_ID,
    )

    password_hash = hash_password(_require_password(password))
    users = (
        User(
            id=SELLER_TECH_USER_ID,
            email="techhub@example.com",
            name="Tech Hub",
            password_hash=password_hash,
            role=UserRole.SELLER,
            seller_id=SELLER_TECH_ID,
        ),
        User(
            id=SELLER_CASA_USER_ID,
            email="casa-viva@example.com",
            name="Casa Viva",
            password_hash=password_hash,
            role=UserRole.SELLER,
            seller_id=SELLER_CASA_ID,
        ),
        User(
            id=SELLER_ESPORTE_USER_ID,
            email="esporte-total@example.com",
            name="Esporte Total",
            password_hash=password_hash,
            role=UserRole.SELLER,
            seller_id=SELLER_ESPORTE_ID,
        ),
        User(
            id=SELLER_LIVROS_USER_ID,
            email="livraria-norte@example.com",
            name="Livraria Norte",
            password_hash=password_hash,
            role=UserRole.SELLER,
            seller_id=SELLER_LIVROS_ID,
        ),
        User(
            id=SELLER_MODA_USER_ID,
            email="moda-urban@example.com",
            name="Moda Urban",
            password_hash=password_hash,
            role=UserRole.SELLER,
            seller_id=SELLER_MODA_ID,
        ),
        User(
            id=SELLER_KIDS_USER_ID,
            email="kids-world@example.com",
            name="Kids World",
            password_hash=password_hash,
            role=UserRole.SELLER,
            seller_id=SELLER_KIDS_ID,
        ),
        User(
            id=BUYER_ANA_ID,
            email="ana.silva@example.com",
            name="Ana Silva",
            password_hash=password_hash,
            role=UserRole.BUYER,
            seller_id=None,
        ),
        User(
            id=BUYER_BRUNO_ID,
            email="bruno.costa@example.com",
            name="Bruno Costa",
            password_hash=password_hash,
            role=UserRole.BUYER,
            seller_id=None,
        ),
        User(
            id=BUYER_CARLA_ID,
            email="carla.mendes@example.com",
            name="Carla Mendes",
            password_hash=password_hash,
            role=UserRole.BUYER,
            seller_id=None,
        ),
        User(
            id=BUYER_DIEGO_ID,
            email="diego.alves@example.com",
            name="Diego Alves",
            password_hash=password_hash,
            role=UserRole.BUYER,
            seller_id=None,
        ),
        User(
            id=BUYER_ELENA_ID,
            email="elena.rocha@example.com",
            name="Elena Rocha",
            password_hash=password_hash,
            role=UserRole.BUYER,
            seller_id=None,
        ),
        User(
            id=BUYER_FABIO_ID,
            email="fabio.nunes@example.com",
            name="Fabio Nunes",
            password_hash=password_hash,
            role=UserRole.BUYER,
            seller_id=None,
        ),
        User(
            id=BUYER_GIOVANA_ID,
            email="giovana.dias@example.com",
            name="Giovana Dias",
            password_hash=password_hash,
            role=UserRole.BUYER,
            seller_id=None,
        ),
        User(
            id=BUYER_HENRIQUE_ID,
            email="henrique.lima@example.com",
            name="Henrique Lima",
            password_hash=password_hash,
            role=UserRole.BUYER,
            seller_id=None,
        ),
        User(
            id=BUYER_ISABEL_ID,
            email="isabel.freitas@example.com",
            name="Isabel Freitas",
            password_hash=password_hash,
            role=UserRole.BUYER,
            seller_id=None,
        ),
        User(
            id=BUYER_JOAO_ID,
            email="joao.martins@example.com",
            name="Joao Martins",
            password_hash=password_hash,
            role=UserRole.BUYER,
            seller_id=None,
        ),
    )
    for user in users:
        _add_user(session, user)
