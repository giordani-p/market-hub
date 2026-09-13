"""Modelos persistidos do Catalogo."""

import uuid
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Seller(Base):
    """Identidade minima do vendedor, usada apenas no relacionamento com Oferta."""

    __tablename__ = "sellers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)


class Product(Base):
    """Item comercializado. Nao carrega preco, estoque nem disponibilidade."""

    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2000))


class Offer(Base):
    """Comercializacao de um Produto por um Vendedor."""

    __tablename__ = "offers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    seller_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sellers.id", ondelete="RESTRICT"), nullable=False
    )
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False)
    available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
