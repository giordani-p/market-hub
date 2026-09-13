from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.models import User, UserRole
from app.auth.passwords import hash_password
from app.communication.close_inactive import run_close_inactive
from app.communication.lifecycle import SYSTEM_CLOSE_MESSAGE
from app.communication.models import Conversation, Message
from app.core.events import ConversationClosed, ConversationCreated, MessageCreated, publisher
from tests.conftest import TEST_SEED_PASSWORD
from tests.integration.auth_helpers import buyer_headers, seller_a_headers, seller_b_headers


def _product(client: TestClient) -> dict:
    response = client.post("/v1/products", json={"name": "Tenis XYZ", "description": "Par"})
    assert response.status_code == 201
    return response.json()


def _offer(client: TestClient, product_id: str, headers: dict[str, str]) -> dict:
    response = client.post(
        "/v1/offers",
        json={"product_id": product_id, "price": "299.00", "stock": 50},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def _checkout_item(client: TestClient, offer_id: str) -> dict:
    response = client.post(
        "/v1/orders",
        json={"items": [{"offer_id": offer_id, "quantity": 1, "expected_price": "299.00"}]},
        headers=buyer_headers(client),
    )
    assert response.status_code == 201, response.text
    return response.json()["items"][0]


def _item(client: TestClient) -> str:
    product = _product(client)
    offer = _offer(client, product["id"], seller_a_headers(client))
    return _checkout_item(client, offer["id"])["id"]


def test_buyer_and_seller_can_open_conversation(catalog_client: TestClient) -> None:
    item_id = _item(catalog_client)
    created = catalog_client.post(
        f"/v1/order-items/{item_id}/conversation",
        json={"reason": "atraso"},
        headers=buyer_headers(catalog_client),
    )
    assert created.status_code == 201
    body = created.json()
    assert body["status"] == "open"
    assert body["reason"] == "atraso"
    assert any(isinstance(event, ConversationCreated) for event in publisher.events)

    reused = catalog_client.post(
        f"/v1/order-items/{item_id}/conversation",
        json={"reason": "troca"},
        headers=seller_a_headers(catalog_client),
    )
    assert reused.status_code == 200
    assert reused.json()["id"] == body["id"]
    assert reused.json()["reason"] == "atraso"
    assert sum(isinstance(event, ConversationCreated) for event in publisher.events) == 1


def test_reason_validation(catalog_client: TestClient) -> None:
    item_id = _item(catalog_client)
    headers = buyer_headers(catalog_client)
    missing = catalog_client.post(
        f"/v1/order-items/{item_id}/conversation", json={}, headers=headers
    )
    assert missing.status_code == 422
    invalid = catalog_client.post(
        f"/v1/order-items/{item_id}/conversation",
        json={"reason": "ATRASO"},
        headers=headers,
    )
    assert invalid.status_code == 422


def test_new_conversation_after_close(catalog_client: TestClient) -> None:
    item_id = _item(catalog_client)
    first = catalog_client.post(
        f"/v1/order-items/{item_id}/conversation",
        json={"reason": "suporte"},
        headers=buyer_headers(catalog_client),
    ).json()
    closed = catalog_client.post(
        f"/v1/conversations/{first['id']}/close",
        headers=seller_a_headers(catalog_client),
    )
    assert closed.status_code == 200
    assert closed.json()["status"] == "closed"
    assert any(
        isinstance(event, ConversationClosed) and event.closed_by == "manual"
        for event in publisher.events
    )

    second = catalog_client.post(
        f"/v1/order-items/{item_id}/conversation",
        json={"reason": "elogio"},
        headers=buyer_headers(catalog_client),
    )
    assert second.status_code == 201
    assert second.json()["id"] != first["id"]
    listed = catalog_client.get(
        f"/v1/order-items/{item_id}/conversations",
        headers=buyer_headers(catalog_client),
    ).json()
    assert [item["id"] for item in listed] == [second.json()["id"], first["id"]]


def test_buyer_cannot_close_and_closed_rejects_message(catalog_client: TestClient) -> None:
    item_id = _item(catalog_client)
    conversation_id = catalog_client.post(
        f"/v1/order-items/{item_id}/conversation",
        json={"reason": "reclamacao"},
        headers=buyer_headers(catalog_client),
    ).json()["id"]

    forbidden = catalog_client.post(
        f"/v1/conversations/{conversation_id}/close",
        headers=buyer_headers(catalog_client),
    )
    assert forbidden.status_code == 403

    catalog_client.post(
        f"/v1/conversations/{conversation_id}/close",
        headers=seller_a_headers(catalog_client),
    )
    repeated = catalog_client.post(
        f"/v1/conversations/{conversation_id}/close",
        headers=seller_a_headers(catalog_client),
    )
    assert repeated.status_code == 409
    assert repeated.json()["code"] == "invalid_transition"

    detail = catalog_client.get(
        f"/v1/conversations/{conversation_id}",
        headers=buyer_headers(catalog_client),
    )
    assert detail.status_code == 200
    assert detail.json()["status"] == "closed"

    blocked = catalog_client.post(
        f"/v1/conversations/{conversation_id}/messages",
        json={"content": "ainda aberto?"},
        headers=buyer_headers(catalog_client),
    )
    assert blocked.status_code == 409


def test_messages_and_history_window(catalog_client: TestClient, test_engine) -> None:
    item_id = _item(catalog_client)
    conversation_id = catalog_client.post(
        f"/v1/order-items/{item_id}/conversation",
        json={"reason": "outros"},
        headers=buyer_headers(catalog_client),
    ).json()["id"]

    empty = catalog_client.post(
        f"/v1/conversations/{conversation_id}/messages",
        json={"content": "   "},
        headers=buyer_headers(catalog_client),
    )
    assert empty.status_code == 422
    too_long = catalog_client.post(
        f"/v1/conversations/{conversation_id}/messages",
        json={"content": "x" * 2001},
        headers=seller_a_headers(catalog_client),
    )
    assert too_long.status_code == 422

    sent = catalog_client.post(
        f"/v1/conversations/{conversation_id}/messages",
        json={"content": "  chegou?  "},
        headers=buyer_headers(catalog_client),
    )
    assert sent.status_code == 201
    assert sent.json()["content"] == "chegou?"
    assert sent.json()["author_type"] == "buyer"
    assert any(isinstance(event, MessageCreated) for event in publisher.events)

    reply = catalog_client.post(
        f"/v1/conversations/{conversation_id}/messages",
        json={"content": "sim"},
        headers=seller_a_headers(catalog_client),
    )
    assert reply.status_code == 201
    assert reply.json()["author_type"] == "seller"

    old_id = uuid4()
    old_at = datetime.now(UTC) - timedelta(hours=30)
    with Session(test_engine) as session:
        session.add(
            Message(
                id=old_id,
                conversation_id=conversation_id,
                author_type="buyer",
                author_user_id=None,
                content="ontem",
                created_at=old_at,
            )
        )
        session.commit()

    page = catalog_client.get(
        f"/v1/conversations/{conversation_id}/messages",
        headers=buyer_headers(catalog_client),
    ).json()
    assert page["has_older"] is True
    assert [item["content"] for item in page["items"]] == ["chegou?", "sim"]

    older = catalog_client.get(
        f"/v1/conversations/{conversation_id}/messages",
        params={"before": page["from"]},
        headers=buyer_headers(catalog_client),
    ).json()
    assert any(item["id"] == str(old_id) for item in older["items"])

    naive = catalog_client.get(
        f"/v1/conversations/{conversation_id}/messages",
        params={"before": "2026-01-01T00:00:00"},
        headers=buyer_headers(catalog_client),
    )
    assert naive.status_code == 422
    future = catalog_client.get(
        f"/v1/conversations/{conversation_id}/messages",
        params={"before": "2099-01-01T00:00:00Z"},
        headers=buyer_headers(catalog_client),
    )
    assert future.status_code == 422


def test_isolation_returns_404(catalog_client: TestClient, test_engine) -> None:
    product = _product(catalog_client)
    offer_a = _offer(catalog_client, product["id"], seller_a_headers(catalog_client))
    item_id = _checkout_item(catalog_client, offer_a["id"])["id"]
    conversation_id = catalog_client.post(
        f"/v1/order-items/{item_id}/conversation",
        json={"reason": "troca"},
        headers=buyer_headers(catalog_client),
    ).json()["id"]

    assert (
        catalog_client.get(
            f"/v1/conversations/{conversation_id}",
            headers=seller_b_headers(catalog_client),
        ).status_code
        == 404
    )
    assert (
        catalog_client.post(
            f"/v1/order-items/{item_id}/conversation",
            json={"reason": "troca"},
            headers=seller_b_headers(catalog_client),
        ).status_code
        == 404
    )

    with Session(test_engine) as session:
        session.add(
            User(
                email="buyer-2@example.com",
                name="Buyer Two",
                password_hash=hash_password(TEST_SEED_PASSWORD),
                role=UserRole.BUYER,
            )
        )
        session.commit()

    token = catalog_client.post(
        "/v1/auth/login",
        json={"email": "buyer-2@example.com", "password": TEST_SEED_PASSWORD},
    ).json()["access_token"]
    other = {"Authorization": f"Bearer {token}"}
    assert (
        catalog_client.get(f"/v1/conversations/{conversation_id}", headers=other).status_code == 404
    )
    list_as_buyer = catalog_client.get("/v1/order-items", headers=buyer_headers(catalog_client))
    assert list_as_buyer.status_code == 403


def test_anonymous_is_401(catalog_client: TestClient) -> None:
    assert catalog_client.get(f"/v1/conversations/{uuid4()}").status_code == 401


def test_lazy_close_on_get(catalog_client: TestClient, test_engine) -> None:
    item_id = _item(catalog_client)
    conversation_id = catalog_client.post(
        f"/v1/order-items/{item_id}/conversation",
        json={"reason": "atraso"},
        headers=buyer_headers(catalog_client),
    ).json()["id"]
    stale = datetime.now(UTC) - timedelta(hours=121)
    with Session(test_engine) as session:
        conversation = session.get(Conversation, conversation_id)
        assert conversation is not None
        conversation.last_interaction_at = stale
        session.commit()

    publisher.clear()
    body = catalog_client.get(
        f"/v1/conversations/{conversation_id}",
        headers=buyer_headers(catalog_client),
    )
    assert body.status_code == 200
    assert body.json()["status"] == "closed"
    messages = catalog_client.get(
        f"/v1/conversations/{conversation_id}/messages",
        headers=buyer_headers(catalog_client),
    ).json()
    assert any(item["content"] == SYSTEM_CLOSE_MESSAGE for item in messages["items"])
    assert any(
        isinstance(event, ConversationClosed) and event.closed_by == "inactivity"
        for event in publisher.events
    )


def test_batch_close_is_idempotent(catalog_client: TestClient, test_engine) -> None:
    item_id = _item(catalog_client)
    conversation_id = catalog_client.post(
        f"/v1/order-items/{item_id}/conversation",
        json={"reason": "atraso"},
        headers=buyer_headers(catalog_client),
    ).json()["id"]
    stale = datetime.now(UTC) - timedelta(hours=121)
    with Session(test_engine) as session:
        conversation = session.get(Conversation, conversation_id)
        assert conversation is not None
        conversation.last_interaction_at = stale
        session.commit()

    from sqlalchemy import func, select
    from sqlalchemy.orm import sessionmaker

    from app.core.config import Settings

    factory = sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)
    settings = Settings(conversation_inactivity_hours=120, _env_file=None)
    first = run_close_inactive(factory=factory, settings=settings)
    second = run_close_inactive(factory=factory, settings=settings)
    assert first == 1
    assert second == 0
    with Session(test_engine) as session:
        system_count = session.scalar(
            select(func.count()).where(
                Message.conversation_id == conversation_id,
                Message.author_type == "system",
            )
        )
        assert system_count == 1
