from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.communication.models import Conversation
from app.communication.priority import is_stale
from app.communication.reconcile import list_stale_page, run_reconcile, stale_statement
from app.core.config import Settings
from app.orders.models import OrderItem
from tests.integration.auth_helpers import (
    buyer_headers,
    ops_headers,
    seller_a_headers,
)
from tests.integration.test_priority import _checkout, _offer, _open, _product


def _factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def _load(session: Session, conversation_id: UUID) -> tuple[Conversation, OrderItem]:
    conversation = session.get(Conversation, conversation_id)
    assert conversation is not None
    item = session.get(OrderItem, conversation.order_item_id)
    assert item is not None
    return conversation, item


def test_create_and_refresh_stamp_priority_calculated_at(
    catalog_client: TestClient, test_engine: Engine
) -> None:
    product = _product(catalog_client)
    offer = _offer(catalog_client, product["id"], seller_a_headers(catalog_client), "299.00")
    item = _checkout(catalog_client, offer["id"], "299.00")
    created = _open(catalog_client, item["id"], "atraso", buyer_headers(catalog_client))
    seller = seller_a_headers(catalog_client)
    with _factory(test_engine)() as session:
        conversation, order_item = _load(session, UUID(created["id"]))
        assert conversation.priority_calculated_at is not None
        first_stamp = conversation.priority_calculated_at
        assert order_item.status_updated_at is not None

    same = catalog_client.patch(
        f"/v1/order-items/{item['id']}", json={"status": "placed"}, headers=seller
    )
    assert same.status_code == 200
    with _factory(test_engine)() as session:
        _, order_item = _load(session, UUID(created["id"]))
        unchanged_status_at = order_item.status_updated_at

    preparing = catalog_client.patch(
        f"/v1/order-items/{item['id']}", json={"status": "preparing"}, headers=seller
    )
    assert preparing.status_code == 200
    with _factory(test_engine)() as session:
        _, order_item = _load(session, UUID(created["id"]))
        assert order_item.status_updated_at > unchanged_status_at

    ops = ops_headers(catalog_client)
    refresh = catalog_client.post(
        f"/v1/ops/conversations/{created['id']}/priority/refresh", headers=ops
    )
    assert refresh.status_code == 200
    with _factory(test_engine)() as session:
        conversation, _ = _load(session, UUID(created["id"]))
        assert conversation.priority_calculated_at is not None
        assert conversation.priority_calculated_at >= first_stamp


def test_reconcile_pages_open_only_and_is_idempotent(
    catalog_client: TestClient, test_engine: Engine
) -> None:
    seller = seller_a_headers(catalog_client)
    buyer = buyer_headers(catalog_client)
    ids: list[UUID] = []
    for index in range(3):
        product = _product(catalog_client, name=f"Item {index}")
        offer = _offer(catalog_client, product["id"], seller, "299.00")
        item = _checkout(catalog_client, offer["id"], "299.00")
        created = _open(catalog_client, item["id"], "atraso", buyer)
        ids.append(UUID(created["id"]))

    closed = catalog_client.post(f"/v1/conversations/{ids[0]}/close", headers=seller)
    assert closed.status_code == 200

    factory = _factory(test_engine)
    with factory() as session:
        conversations = list(session.scalars(select(Conversation).where(Conversation.id.in_(ids))))
        for conversation in conversations:
            conversation.priority_calculated_at = None
        session.commit()

    now = datetime.now(UTC)
    result = run_reconcile(factory, Settings(_env_file=None), now=now, page_size=1)
    assert result.found == 2
    assert result.processed == 2

    with factory() as session:
        open_one = session.get(Conversation, ids[1])
        closed_one = session.get(Conversation, ids[0])
        assert open_one is not None
        assert closed_one is not None
        assert open_one.priority_calculated_at is not None
        assert closed_one.priority_calculated_at is None
        stamped = open_one.priority_calculated_at
        calculated = open_one.calculated_priority

    second = run_reconcile(factory, Settings(_env_file=None), now=now, page_size=1)
    assert second.found == 0
    assert second.updated == 0
    with factory() as session:
        open_one = session.get(Conversation, ids[1])
        assert open_one is not None
        assert open_one.calculated_priority == calculated
        assert open_one.priority_calculated_at == stamped


def test_stale_sql_matches_python(catalog_client: TestClient, test_engine: Engine) -> None:
    now = datetime(2026, 9, 13, 18, 0, tzinfo=UTC)
    seller = seller_a_headers(catalog_client)
    buyer = buyer_headers(catalog_client)
    product = _product(catalog_client)
    offer = _offer(catalog_client, product["id"], seller, "299.00")
    item = _checkout(catalog_client, offer["id"], "299.00")
    created = _open(catalog_client, item["id"], "atraso", buyer)
    conversation_id = UUID(created["id"])

    factory = _factory(test_engine)
    with factory() as session:
        conversation, order_item = _load(session, conversation_id)
        conversation.created_at = now - timedelta(hours=5)
        conversation.last_interaction_at = now - timedelta(hours=5)
        conversation.priority_calculated_at = now - timedelta(hours=4)
        order_item.status_updated_at = now - timedelta(hours=5)
        session.commit()

    with factory() as session:
        conversation, order_item = _load(session, conversation_id)
        python_stale = is_stale(
            now=now,
            created_at=conversation.created_at,
            last_interaction_at=conversation.last_interaction_at,
            status_updated_at=order_item.status_updated_at,
            priority_calculated_at=conversation.priority_calculated_at,
        )
        sql_ids = {row[0].id for row in session.execute(stale_statement(now)).all()}
        page = list_stale_page(session, now=now, page_size=50)
        assert python_stale is True
        assert conversation_id in sql_ids
        assert conversation_id in {row[0].id for row in page}
