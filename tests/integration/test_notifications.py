from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.auth.seed import BUYER_ID, OPS_ID, SELLER_A_USER_ID
from app.jobs.handlers import default_registry
from app.jobs.worker import process_once
from app.notifications.models import (
    CONVERSATION_PRIORITY_CHANGED,
    CONVERSATION_STATUS_CHANGED,
    ORDER_ITEM_STATUS_CHANGED,
    Notification,
)
from tests.fakes import InMemoryJobQueue
from tests.integration.auth_helpers import (
    buyer_headers,
    ops_headers,
    seller_a_headers,
    seller_b_headers,
)
from tests.integration.test_priority import _checkout, _offer, _open, _product


def _drain(queue: InMemoryJobQueue) -> None:
    registry = default_registry()
    for _ in list(queue.pending):
        process_once(queue, registry)


def _factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def test_empty_inbox_and_unread_count(catalog_client: TestClient) -> None:
    headers = buyer_headers(catalog_client)
    listed = catalog_client.get("/v1/notifications", headers=headers)
    assert listed.status_code == 200
    assert listed.json() == {"items": [], "page": 1, "page_size": 20, "total": 0}
    count = catalog_client.get("/v1/notifications/unread-count", headers=headers)
    assert count.status_code == 200
    assert count.json() == {"unread_count": 0}
    marked = catalog_client.patch("/v1/notifications/read-all", headers=headers)
    assert marked.status_code == 204


def test_notifications_require_auth(catalog_client: TestClient) -> None:
    assert catalog_client.get("/v1/notifications").status_code == 401
    assert catalog_client.get("/v1/notifications/unread-count").status_code == 401


def test_order_item_status_notifies_buyer_and_seller_not_ops(
    catalog_client: TestClient, job_queue: InMemoryJobQueue
) -> None:
    product = _product(catalog_client)
    offer = _offer(catalog_client, product["id"], seller_a_headers(catalog_client), "299.00")
    item = _checkout(catalog_client, offer["id"], "299.00")
    job_queue.pending.clear()
    patched = catalog_client.patch(
        f"/v1/order-items/{item['id']}",
        json={"status": "preparing"},
        headers=seller_a_headers(catalog_client),
    )
    assert patched.status_code == 200
    assert len(job_queue.pending) == 1
    _drain(job_queue)

    buyer = catalog_client.get("/v1/notifications", headers=buyer_headers(catalog_client)).json()
    seller_headers = seller_a_headers(catalog_client)
    seller = catalog_client.get("/v1/notifications", headers=seller_headers).json()
    ops = catalog_client.get("/v1/notifications", headers=ops_headers(catalog_client)).json()
    assert buyer["total"] == 1
    assert seller["total"] == 1
    assert ops["total"] == 0
    body = buyer["items"][0]
    assert body["type"] == ORDER_ITEM_STATUS_CHANGED
    assert body["entity_type"] == "ORDER_ITEM"
    assert body["entity_id"] == item["id"]
    assert body["metadata"] == {"previous_status": "placed", "new_status": "preparing"}
    assert body["read_at"] is None
    assert "placed" in body["message"]
    assert seller["items"][0]["recipient_id"] == str(SELLER_A_USER_ID)
    assert buyer["items"][0]["recipient_id"] == str(BUYER_ID)


def test_message_created_does_not_enqueue_notification(
    catalog_client: TestClient, job_queue: InMemoryJobQueue
) -> None:
    product = _product(catalog_client)
    offer = _offer(catalog_client, product["id"], seller_a_headers(catalog_client), "299.00")
    item = _checkout(catalog_client, offer["id"], "299.00")
    opened = _open(catalog_client, item["id"], "suporte", buyer_headers(catalog_client))
    assert job_queue.pending == []
    posted = catalog_client.post(
        f"/v1/conversations/{opened['id']}/messages",
        json={"content": "Onde esta o pedido?"},
        headers=buyer_headers(catalog_client),
    )
    assert posted.status_code == 201
    assert job_queue.pending == []


def test_conversation_close_notifies_buyer_and_seller(
    catalog_client: TestClient, job_queue: InMemoryJobQueue
) -> None:
    product = _product(catalog_client)
    offer = _offer(catalog_client, product["id"], seller_a_headers(catalog_client), "299.00")
    item = _checkout(catalog_client, offer["id"], "299.00")
    opened = _open(catalog_client, item["id"], "suporte", buyer_headers(catalog_client))
    job_queue.pending.clear()
    closed = catalog_client.post(
        f"/v1/conversations/{opened['id']}/close",
        headers=seller_a_headers(catalog_client),
    )
    assert closed.status_code == 200
    _drain(job_queue)
    buyer = catalog_client.get("/v1/notifications", headers=buyer_headers(catalog_client)).json()
    assert buyer["total"] == 1
    assert buyer["items"][0]["type"] == CONVERSATION_STATUS_CHANGED
    assert buyer["items"][0]["metadata"] == {"previous_status": "open", "new_status": "closed"}
    ops = catalog_client.get("/v1/notifications", headers=ops_headers(catalog_client)).json()
    assert ops["total"] == 0


def test_priority_notifies_seller_and_ops_not_buyer(
    catalog_client: TestClient, job_queue: InMemoryJobQueue
) -> None:
    product = _product(catalog_client)
    offer = _offer(catalog_client, product["id"], seller_a_headers(catalog_client), "299.00")
    item = _checkout(catalog_client, offer["id"], "299.00")
    opened = _open(catalog_client, item["id"], "atraso", buyer_headers(catalog_client))
    job_queue.pending.clear()
    critical = catalog_client.post(
        f"/v1/ops/conversations/{opened['id']}/critical",
        json={"justification": "Cliente em risco, precisa de tratativa imediata."},
        headers=ops_headers(catalog_client),
    )
    assert critical.status_code == 200, critical.text
    _drain(job_queue)

    seller_headers = seller_a_headers(catalog_client)
    seller = catalog_client.get("/v1/notifications", headers=seller_headers).json()
    ops = catalog_client.get("/v1/notifications", headers=ops_headers(catalog_client)).json()
    buyer = catalog_client.get("/v1/notifications", headers=buyer_headers(catalog_client)).json()
    assert seller["total"] == 1
    assert ops["total"] == 1
    assert buyer["total"] == 0
    assert seller["items"][0]["type"] == CONVERSATION_PRIORITY_CHANGED
    assert seller["items"][0]["metadata"]["new_status"] == "critical"
    assert ops["items"][0]["recipient_id"] == str(OPS_ID)


def test_idempotent_job_creates_one_notification_per_recipient(
    catalog_client: TestClient, job_queue: InMemoryJobQueue, test_engine: Engine
) -> None:
    product = _product(catalog_client)
    offer = _offer(catalog_client, product["id"], seller_a_headers(catalog_client), "299.00")
    item = _checkout(catalog_client, offer["id"], "299.00")
    job_queue.pending.clear()
    catalog_client.patch(
        f"/v1/order-items/{item['id']}",
        json={"status": "preparing"},
        headers=seller_a_headers(catalog_client),
    )
    assert len(job_queue.pending) == 1
    body = job_queue.pending[0][1]
    _drain(job_queue)
    job_queue.send(body)
    _drain(job_queue)

    with _factory(test_engine)() as session:
        rows = list(session.scalars(select(Notification)))
    assert len(rows) == 2
    recipients = {row.recipient_id for row in rows}
    assert recipients == {BUYER_ID, SELLER_A_USER_ID}


def test_list_pagination_unread_and_mark_read(
    catalog_client: TestClient, job_queue: InMemoryJobQueue
) -> None:
    product = _product(catalog_client)
    offer = _offer(catalog_client, product["id"], seller_a_headers(catalog_client), "299.00")
    item = _checkout(catalog_client, offer["id"], "299.00")
    job_queue.pending.clear()
    catalog_client.patch(
        f"/v1/order-items/{item['id']}",
        json={"status": "preparing"},
        headers=seller_a_headers(catalog_client),
    )
    catalog_client.patch(
        f"/v1/order-items/{item['id']}",
        json={"status": "in_transit"},
        headers=seller_a_headers(catalog_client),
    )
    _drain(job_queue)

    headers = buyer_headers(catalog_client)
    page = catalog_client.get("/v1/notifications?page=1&page_size=1", headers=headers)
    assert page.status_code == 200
    body = page.json()
    assert body["total"] == 2
    assert body["page_size"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["metadata"]["new_status"] == "in_transit"

    too_big = catalog_client.get("/v1/notifications?page_size=101", headers=headers)
    assert too_big.status_code == 422

    count = catalog_client.get("/v1/notifications/unread-count", headers=headers).json()
    assert count["unread_count"] == 2
    first_id = body["items"][0]["id"]
    marked = catalog_client.patch(f"/v1/notifications/{first_id}/read", headers=headers)
    assert marked.status_code == 200
    assert marked.json()["read_at"] is not None
    again = catalog_client.patch(f"/v1/notifications/{first_id}/read", headers=headers)
    assert again.status_code == 200
    assert again.json()["read_at"] == marked.json()["read_at"]

    after_one = catalog_client.get("/v1/notifications/unread-count", headers=headers).json()
    assert after_one["unread_count"] == 1
    catalog_client.patch("/v1/notifications/read-all", headers=headers)
    catalog_client.patch("/v1/notifications/read-all", headers=headers)
    empty = catalog_client.get("/v1/notifications/unread-count", headers=headers).json()
    assert empty["unread_count"] == 0


def test_cannot_read_another_users_notification(
    catalog_client: TestClient, job_queue: InMemoryJobQueue
) -> None:
    product = _product(catalog_client)
    offer = _offer(catalog_client, product["id"], seller_a_headers(catalog_client), "299.00")
    item = _checkout(catalog_client, offer["id"], "299.00")
    job_queue.pending.clear()
    catalog_client.patch(
        f"/v1/order-items/{item['id']}",
        json={"status": "preparing"},
        headers=seller_a_headers(catalog_client),
    )
    _drain(job_queue)
    seller_inbox = catalog_client.get(
        "/v1/notifications", headers=seller_a_headers(catalog_client)
    ).json()
    notification_id = seller_inbox["items"][0]["id"]
    other = catalog_client.patch(
        f"/v1/notifications/{notification_id}/read",
        headers=seller_b_headers(catalog_client),
    )
    assert other.status_code == 404
    missing = catalog_client.patch(
        f"/v1/notifications/{notification_id}/read",
        headers=buyer_headers(catalog_client),
    )
    assert missing.status_code == 404


def test_same_status_patch_does_not_enqueue(
    catalog_client: TestClient, job_queue: InMemoryJobQueue
) -> None:
    product = _product(catalog_client)
    offer = _offer(catalog_client, product["id"], seller_a_headers(catalog_client), "299.00")
    item = _checkout(catalog_client, offer["id"], "299.00")
    job_queue.pending.clear()
    catalog_client.patch(
        f"/v1/order-items/{item['id']}",
        json={"status": "placed"},
        headers=seller_a_headers(catalog_client),
    )
    assert job_queue.pending == []
