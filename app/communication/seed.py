"""Conversas e mensagens da seed de marketplace."""

from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.catalog.models import Offer
from app.catalog.seed import add_if_missing, add_or_replace_content
from app.communication.models import Conversation, Message
from app.communication.priority import calculate_priority
from app.orders.models import Order, OrderItem
from app.orders.seed import item_id

# conv_n, item_n, reason, status, created_hours, last_hours, ops_override
CONVERSATIONS: tuple[tuple[int, int, str, str, int, int, str | None], ...] = (
    (1, 6, "atraso", "open", 60, 3, "critical"),
    (2, 39, "atraso", "open", 7, 2, None),
    (3, 17, "reclamacao", "open", 12, 4, None),
    (4, 29, "suporte", "open", 15, 5, None),
    (5, 1, "atraso", "open", 2, 1, None),
    (6, 45, "reclamacao", "open", 22, 6, None),
    (7, 14, "suporte", "open", 3, 1, None),
    (8, 42, "outros", "open", 3, 2, None),
    (9, 52, "elogio", "open", 1, 1, None),
    (10, 34, "troca", "open", 9, 3, None),
    (11, 27, "devolucao", "open", 4, 2, None),
    (12, 63, "atraso", "open", 20, 8, None),
    (13, 7, "elogio", "closed", 36, 30, None),
    (14, 20, "troca", "closed", 24, 20, None),
    (15, 36, "suporte", "closed", 18, 16, None),
    (16, 40, "reclamacao", "closed", 50, 40, None),
)

# msg_n, conv_n, author (buyer|seller), hours_ago, content
MESSAGES: tuple[tuple[int, int, str, int, str], ...] = (
    (1, 1, "buyer", 60, "O smartphone ainda nao foi coletado pela transportadora."),
    (2, 1, "seller", 48, "Ha atraso no centro de distribuicao. Vamos priorizar."),
    (3, 1, "buyer", 3, "Ja passou de dois dias. Preciso do aparelho nesta semana."),
    (4, 2, "buyer", 7, "A bicicleta saiu para entrega? O rastreio nao atualiza."),
    (5, 2, "seller", 2, "A transportadora confirmou a saida hoje pela manha."),
    (6, 3, "buyer", 12, "O tenis chegou com o solado descascando."),
    (7, 3, "seller", 6, "Pode enviar fotos? Abrimos a analise de qualidade."),
    (8, 3, "buyer", 4, "Enviei as fotos no e-mail. Quero troca do par."),
    (9, 4, "buyer", 15, "A jaqueta veio em tamanho P e pedi M."),
    (10, 4, "seller", 5, "Vamos emitir a etiqueta de troca ainda hoje."),
    (11, 5, "buyer", 2, "O notebook consta como realizado ha horas. Tem previsao?"),
    (12, 5, "seller", 1, "Acabou de entrar na fila de separacao."),
    (13, 6, "buyer", 22, "Paguei o notebook mais barato e o status parou em preparacao."),
    (14, 6, "seller", 10, "Houve divergencia de estoque. Estamos regularizando."),
    (15, 6, "buyer", 6, "Se nao sair hoje, vou cancelar."),
    (16, 7, "buyer", 3, "O monitor veio sem cabo HDMI. Conseguem enviar um?"),
    (17, 8, "buyer", 3, "Os blocos vieram com uma peca diferente da caixa."),
    (18, 8, "seller", 2, "Pode fotografar a peca extra? Trocamos sem custo."),
    (19, 9, "buyer", 1, "O vestido chegou rapido e a estampa e linda. Obrigado!"),
    (20, 10, "buyer", 9, "A panela antiaderente ja esta descascando na primeira semana."),
    (21, 10, "seller", 3, "Separando um jogo novo para envio de troca."),
    (22, 11, "buyer", 4, "Quero devolver a camiseta; o tecido e mais fino do que a foto."),
    (23, 11, "seller", 2, "A devolucao esta autorizada. Etiqueta no e-mail."),
    (24, 12, "buyer", 20, "A jaqueta da Moda Urban esta parada em transito."),
    (25, 12, "seller", 12, "Abrimos chamado na transportadora."),
    (26, 12, "buyer", 8, "Ainda sem atualizacao. Podem cobrar eles?"),
    (27, 13, "buyer", 36, "O carregador chegou antes do prazo. Excelente."),
    (28, 13, "seller", 30, "Que bom! Qualquer coisa estamos por aqui."),
    (29, 14, "buyer", 24, "Quero trocar o notebook por outro com mais memoria."),
    (30, 14, "seller", 20, "A troca foi concluida. Encerramos por aqui."),
    (31, 15, "buyer", 18, "A luminaria nao liga na tomada."),
    (32, 15, "seller", 16, "Enviamos a peca de reposicao. Conversa encerrada."),
    (33, 16, "buyer", 50, "O livro de receitas veio com paginas repetidas."),
    (34, 16, "seller", 40, "Reenvio feito. Caso persista, abra outra conversa."),
)


def conversation_id(n: int) -> UUID:
    return UUID(f"01000005-0000-4000-8000-{n:012x}")


def message_id(n: int) -> UUID:
    return UUID(f"01000006-0000-4000-8000-{n:012x}")


def _seller_user_id(session: Session, seller_id: UUID) -> UUID:
    user_id = session.scalar(select(User.id).where(User.seller_id == seller_id))
    if user_id is None:
        raise RuntimeError(f"Seller user missing for {seller_id}")
    return user_id


def _authors(session: Session, item: OrderItem) -> tuple[UUID, UUID]:
    order = session.get(Order, item.order_id)
    offer = session.get(Offer, item.offer_id)
    if order is None or offer is None:
        raise RuntimeError(f"Order or offer missing for item {item.id}")
    return order.buyer_id, _seller_user_id(session, offer.seller_id)


def seed_demo_conversations(session: Session, now: datetime) -> None:
    """Insere conversations OPEN/CLOSED com prioridade da policy."""
    item_ns = [row[1] for row in CONVERSATIONS]
    if len(item_ns) != len(set(item_ns)):
        raise RuntimeError("Duplicate demo conversation item_n")
    for conv_n, item_n, reason, status, created_hours, last_hours, override in CONVERSATIONS:
        item = session.get(OrderItem, item_id(item_n))
        if item is None:
            raise RuntimeError(f"Order item {item_n} must exist before conversations")
        created_at = now - timedelta(hours=created_hours)
        last_at = now - timedelta(hours=last_hours)
        calculated = calculate_priority(
            reason=reason,
            item_status=item.status,
            created_at=created_at,
            purchase_price=item.purchase_price,
            now=now,
        )
        add_if_missing(
            session,
            Conversation(
                id=conversation_id(conv_n),
                order_item_id=item.id,
                reason=reason,
                status=status,
                created_at=created_at,
                updated_at=last_at,
                last_interaction_at=last_at,
                calculated_priority=calculated,
                ops_override=override,
                priority_calculated_at=now,
            ),
        )
    session.flush()
    prefixed: set[int] = set()
    for msg_n, conv_n, author, hours_ago, content in MESSAGES:
        conversation = session.get(Conversation, conversation_id(conv_n))
        if conversation is None:
            raise RuntimeError(f"Conversation {conv_n} must exist before messages")
        item = session.get(OrderItem, conversation.order_item_id)
        if item is None:
            raise RuntimeError(f"Order item missing for conversation {conv_n}")
        buyer_id, seller_id = _authors(session, item)
        author_id = buyer_id if author == "buyer" else seller_id
        created_at = now - timedelta(hours=hours_ago)
        body = content
        if conv_n not in prefixed:
            body = f"Pedido #{item.number}: {content}"
            prefixed.add(conv_n)
        add_or_replace_content(
            session,
            Message(
                id=message_id(msg_n),
                conversation_id=conversation.id,
                author_type=author,
                author_user_id=author_id,
                content=body,
                created_at=created_at,
            ),
        )
