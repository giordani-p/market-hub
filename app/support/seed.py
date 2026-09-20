"""Comentarios internos da seed de marketplace."""

from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.auth.seed import OPS_ID, SELLER_A_USER_ID, SELLER_ESPORTE_USER_ID, SELLER_TECH_USER_ID
from app.catalog.seed import add_or_replace_content
from app.orders.models import OrderItem
from app.orders.seed import item_id
from app.support.models import InternalComment

# n, item_n, author_id, author_type, hours_ago, content
COMMENTS: tuple[tuple[int, int, UUID, str, int, str], ...] = (
    (
        1,
        6,
        SELLER_A_USER_ID,
        "seller",
        4,
        "Comprador cobrando o flagship. Transportadora sem previsao.",
    ),
    (
        2,
        6,
        OPS_ID,
        "ops",
        2,
        "Marquei critical. Escalar para o SLA de atraso em itens acima de 5 mil.",
    ),
    (
        3,
        39,
        SELLER_ESPORTE_USER_ID,
        "seller",
        3,
        "Bicicleta em transito sem atualizacao. Rastreio parado.",
    ),
    (
        4,
        39,
        OPS_ID,
        "ops",
        1,
        "Prioridade alta pela politica. Acompanhar a transportadora ate amanha.",
    ),
    (
        5,
        45,
        SELLER_TECH_USER_ID,
        "seller",
        8,
        "Estoque divergente no notebook concorrente. Cliente ameaca cancelar.",
    ),
)


def comment_id(n: int) -> UUID:
    return UUID(f"01000007-0000-4000-8000-{n:012x}")


def seed_demo_comments(session: Session, now: datetime) -> None:
    """Insere InternalComments nos items de prioridade alta/critical."""
    for n, item_n, author_id, author_type, hours_ago, content in COMMENTS:
        item = session.get(OrderItem, item_id(item_n))
        if item is None:
            raise RuntimeError(f"Order item {item_n} must exist before comments")
        created_at = now - timedelta(hours=hours_ago)
        add_or_replace_content(
            session,
            InternalComment(
                id=comment_id(n),
                order_item_id=item.id,
                author_id=author_id,
                author_type=author_type,
                content=f"Pedido #{item.number}: {content}",
                created_at=created_at,
            ),
        )
