"""Usuario autenticavel, com papel buyer, seller ou ops."""

import uuid
from enum import StrEnum
from uuid import UUID

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UserRole(StrEnum):
    BUYER = "buyer"
    SELLER = "seller"
    OPS = "ops"


class User(Base):
    """Identidade de login. Seller mapeia 1:1 para um registro em sellers; Ops nao."""

    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("seller_id"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    seller_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("sellers.id", ondelete="RESTRICT"), nullable=True
    )
