"""Modelos persistidos de Order e Order Item."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, Sequence, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

ORDER_NUMBER_SEQ = Sequence("order_number_seq", start=1001)


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Order(Base):
    """Compra realizada por um Buyer."""

    __tablename__ = "orders"
    __table_args__ = (UniqueConstraint("number", name="uq_orders_number"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    number: Mapped[int] = mapped_column(
        Integer,
        ORDER_NUMBER_SEQ,
        nullable=False,
        server_default=ORDER_NUMBER_SEQ.next_value(),
    )
    buyer_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    items: Mapped[list["OrderItem"]] = relationship(back_populates="order")


class OrderItem(Base):
    """Ocorrencia de compra vinculada a uma Offer."""

    __tablename__ = "order_items"
    __table_args__ = (UniqueConstraint("order_id", "line", name="uq_order_items_order_id_line"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    order_id: Mapped[UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    offer_id: Mapped[UUID] = mapped_column(
        ForeignKey("offers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    line: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    purchase_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="placed")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )
    status_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    order: Mapped[Order] = relationship(back_populates="items")

    @property
    def number(self) -> str:
        """Identificador publico composto: {pedido}-{linha}."""
        return f"{self.order.number}-{self.line}"
