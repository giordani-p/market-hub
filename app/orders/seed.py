"""Pedidos da seed de marketplace."""

from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.auth.seed import (
    BUYER_ANA_ID,
    BUYER_BRUNO_ID,
    BUYER_CARLA_ID,
    BUYER_DIEGO_ID,
    BUYER_ELENA_ID,
    BUYER_FABIO_ID,
    BUYER_GIOVANA_ID,
    BUYER_HENRIQUE_ID,
    BUYER_ID,
    BUYER_ISABEL_ID,
    BUYER_JOAO_ID,
)
from app.catalog.demo import OFFER_BY_N, offer_base_stock, offer_id, offer_price
from app.catalog.models import Offer
from app.catalog.seed import add_if_missing
from app.orders.models import Order, OrderItem

BUYERS = {
    "demo": BUYER_ID,
    "ana": BUYER_ANA_ID,
    "bruno": BUYER_BRUNO_ID,
    "carla": BUYER_CARLA_ID,
    "diego": BUYER_DIEGO_ID,
    "elena": BUYER_ELENA_ID,
    "fabio": BUYER_FABIO_ID,
    "giovana": BUYER_GIOVANA_ID,
    "henrique": BUYER_HENRIQUE_ID,
    "isabel": BUYER_ISABEL_ID,
    "joao": BUYER_JOAO_ID,
}

# Pedido 1 → #1001. Usado no INSERT e em public_item_number para nao divergir.
DEMO_ORDER_NUMBER_OFFSET = 1000


def demo_order_number(order_n: int) -> int:
    """Numero publico do pedido de demo (order_n 1 → 1001)."""
    return DEMO_ORDER_NUMBER_OFFSET + order_n


# order_n, buyer_key, hours_ago, ((item_n, offer_n, qty, status, cancelled_from), ...)
# cancelled_from so e usado quando status=cancelled; in_transit consome estoque.
ORDERS: tuple[tuple[int, str, int, tuple[tuple[int, int, int, str, str | None], ...]], ...] = (
    (
        1,
        "demo",
        2,
        (
            (1, 1, 1, "placed", None),
            (2, 3, 1, "placed", None),
            (3, 4, 2, "placed", None),
        ),
    ),
    (
        2,
        "demo",
        8,
        (
            (4, 7, 1, "preparing", None),
            (5, 13, 1, "preparing", None),
        ),
    ),
    (3, "demo", 20, ((6, 11, 1, "in_transit", None),)),
    (
        4,
        "demo",
        36,
        (
            (7, 10, 4, "delivered", None),
            (8, 18, 1, "delivered", None),
        ),
    ),
    (5, "demo", 10, ((9, 4, 1, "cancelled", "placed"),)),
    (6, "demo", 72, ((10, 42, 10, "delivered", None),)),
    (
        7,
        "demo",
        5,
        (
            (11, 1, 1, "preparing", None),
            (12, 41, 1, "preparing", None),
            (13, 43, 1, "preparing", None),
        ),
    ),
    (
        8,
        "ana",
        3,
        (
            (14, 3, 1, "placed", None),
            (15, 7, 2, "placed", None),
            (16, 10, 1, "placed", None),
        ),
    ),
    (
        9,
        "bruno",
        12,
        (
            (17, 18, 1, "in_transit", None),
            (18, 41, 1, "in_transit", None),
            (19, 46, 1, "in_transit", None),
        ),
    ),
    (
        10,
        "carla",
        24,
        (
            (20, 1, 1, "delivered", None),
            (21, 4, 1, "delivered", None),
            (22, 11, 1, "delivered", None),
        ),
    ),
    (
        11,
        "diego",
        6,
        (
            (23, 7, 1, "cancelled", "preparing"),
            (24, 10, 1, "cancelled", "preparing"),
        ),
    ),
    (
        12,
        "elena",
        48,
        (
            (25, 42, 2, "delivered", None),
            (26, 43, 1, "delivered", None),
        ),
    ),
    (
        13,
        "fabio",
        4,
        (
            (27, 13, 2, "placed", None),
            (28, 15, 1, "placed", None),
        ),
    ),
    (14, "giovana", 15, ((29, 16, 1, "in_transit", None),)),
    (
        15,
        "henrique",
        30,
        (
            (30, 17, 1, "delivered", None),
            (31, 21, 1, "delivered", None),
            (32, 15, 1, "delivered", None),
        ),
    ),
    (16, "isabel", 2, ((33, 13, 1, "cancelled", "placed"),)),
    (
        17,
        "joao",
        9,
        (
            (34, 22, 1, "preparing", None),
            (35, 23, 1, "preparing", None),
        ),
    ),
    (18, "ana", 18, ((36, 24, 1, "delivered", None),)),
    (
        19,
        "bruno",
        40,
        (
            (37, 27, 1, "placed", None),
            (38, 28, 2, "placed", None),
        ),
    ),
    (20, "carla", 7, ((39, 30, 1, "in_transit", None),)),
    (
        21,
        "diego",
        50,
        (
            (40, 31, 1, "delivered", None),
            (41, 32, 1, "delivered", None),
        ),
    ),
    (
        22,
        "elena",
        3,
        (
            (42, 35, 1, "placed", None),
            (43, 36, 1, "placed", None),
            (44, 37, 1, "placed", None),
        ),
    ),
    (23, "fabio", 22, ((45, 2, 1, "preparing", None),)),
    (
        24,
        "giovana",
        11,
        (
            (46, 6, 1, "delivered", None),
            (47, 9, 1, "delivered", None),
        ),
    ),
    (25, "henrique", 28, ((48, 12, 1, "cancelled", "in_transit"),)),
    (
        26,
        "isabel",
        16,
        (
            (49, 5, 1, "preparing", None),
            (50, 8, 1, "preparing", None),
            (51, 39, 1, "preparing", None),
        ),
    ),
    (27, "joao", 1, ((52, 19, 1, "placed", None),)),
    (
        28,
        "demo",
        14,
        (
            (53, 13, 1, "preparing", None),
            (54, 22, 1, "preparing", None),
        ),
    ),
    (
        29,
        "ana",
        60,
        (
            (55, 25, 1, "delivered", None),
            (56, 33, 1, "delivered", None),
        ),
    ),
    (30, "bruno", 8, ((57, 40, 1, "placed", None),)),
    (
        31,
        "carla",
        33,
        (
            (58, 29, 1, "delivered", None),
            (59, 27, 1, "delivered", None),
        ),
    ),
    (
        32,
        "diego",
        4,
        (
            (60, 35, 1, "placed", None),
            (61, 38, 1, "placed", None),
            (62, 36, 1, "placed", None),
        ),
    ),
    (33, "elena", 20, ((63, 45, 1, "in_transit", None),)),
    (
        34,
        "fabio",
        70,
        (
            (64, 31, 1, "delivered", None),
            (65, 27, 1, "delivered", None),
        ),
    ),
    (
        35,
        "giovana",
        6,
        (
            (66, 22, 1, "preparing", None),
            (67, 24, 1, "preparing", None),
            (68, 25, 1, "preparing", None),
        ),
    ),
    (
        36,
        "henrique",
        12,
        (
            (69, 2, 1, "in_transit", None),
            (70, 8, 1, "in_transit", None),
        ),
    ),
)


def order_id(order_n: int) -> UUID:
    """UUID de demo determinado pelo pedido (order_n 1 → ...0001)."""
    return UUID(f"01000003-0000-4000-8000-{order_n:012x}")


def _item_placement(item_n: int) -> tuple[int, int]:
    """Posicao do item na tabela ORDERS: (order_n, line)."""
    for order_n, _buyer, _hours, items in ORDERS:
        for line, (n, _offer, _qty, _status, _cancelled) in enumerate(items, start=1):
            if n == item_n:
                return order_n, line
    raise RuntimeError(f"Order item {item_n} is not in the demo ORDERS table")


def public_item_number(item_n: int) -> str:
    """Identificador publico {pedido}-{linha} a partir da tabela ORDERS."""
    order_n, line = _item_placement(item_n)
    return f"{demo_order_number(order_n)}-{line}"


def item_id(item_n: int) -> UUID:
    """UUID de demo determinado pelo pedido e pela linha, nao pelo contador global."""
    order_n, line = _item_placement(item_n)
    return UUID(f"01000004-0000-4000-8000-{order_n:06x}{line:06x}")


def assert_unique_demo_order_ids() -> None:
    """Garante order_n, item_n, number publico e UUIDs unicos e alinhados ao pedido."""
    order_ns = [row[0] for row in ORDERS]
    if len(order_ns) != len(set(order_ns)):
        raise RuntimeError("Duplicate demo order_n")
    item_ns: list[int] = []
    public_numbers: list[str] = []
    item_uuids: list[UUID] = []
    for order_n, _buyer, _hours, items in ORDERS:
        for line, (item_n, _offer, _qty, _status, _cancelled) in enumerate(items, start=1):
            item_ns.append(item_n)
            public_numbers.append(f"{demo_order_number(order_n)}-{line}")
            item_uuids.append(item_id(item_n))
    if len(item_ns) != len(set(item_ns)):
        raise RuntimeError("Duplicate demo item_n")
    if len(public_numbers) != len(set(public_numbers)):
        raise RuntimeError("Duplicate demo public item number")
    if len(item_uuids) != len(set(item_uuids)):
        raise RuntimeError("Duplicate demo item UUID")
    if len({order_id(n) for n in order_ns}) != len(order_ns):
        raise RuntimeError("Duplicate demo order UUID")


def _consumes_stock(status: str, cancelled_from: str | None) -> bool:
    if status == "cancelled":
        return cancelled_from == "in_transit"
    return True


def consumed_by_offer() -> dict[int, int]:
    """Quantidade que permanece fora do estoque, por oferta."""
    consumed: dict[int, int] = {}
    for _order_n, _buyer, _hours, items in ORDERS:
        for _item_n, offer_n, qty, status, cancelled_from in items:
            if _consumes_stock(status, cancelled_from):
                consumed[offer_n] = consumed.get(offer_n, 0) + qty
    return consumed


def seed_demo_orders(session: Session, now: datetime) -> None:
    """Insere orders/items e grava o estoque restante das ofertas."""
    assert_unique_demo_order_ids()
    for order_n, buyer_key, hours_ago, _items in ORDERS:
        created = now - timedelta(hours=hours_ago)
        add_if_missing(
            session,
            Order(
                id=order_id(order_n),
                number=demo_order_number(order_n),
                buyer_id=BUYERS[buyer_key],
                created_at=created,
                updated_at=created,
            ),
        )
    session.flush()
    for order_n, _buyer_key, hours_ago, items in ORDERS:
        created = now - timedelta(hours=hours_ago)
        for line, (item_n, offer_n, qty, status, _cancelled_from) in enumerate(items, start=1):
            add_if_missing(
                session,
                OrderItem(
                    id=item_id(item_n),
                    order_id=order_id(order_n),
                    offer_id=offer_id(offer_n),
                    line=line,
                    quantity=qty,
                    purchase_price=offer_price(offer_n),
                    status=status,
                    created_at=created,
                    updated_at=created,
                    status_updated_at=created,
                ),
            )
    session.flush()
    max_number = session.scalar(select(func.max(Order.number))) or DEMO_ORDER_NUMBER_OFFSET
    session.execute(text("SELECT setval('order_number_seq', :value)"), {"value": max_number})
    consumed = consumed_by_offer()
    for offer_n in OFFER_BY_N:
        offer = session.get(Offer, offer_id(offer_n))
        if offer is not None:
            remaining = offer_base_stock(offer_n) - consumed.get(offer_n, 0)
            if remaining < 0:
                raise RuntimeError(f"Offer {offer_n} stock would be negative")
            offer.stock = remaining
