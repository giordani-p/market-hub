from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.catalog.seed import SELLER_A_ID, SELLER_B_ID
from app.communication.models import Conversation
from tests.integration.auth_helpers import (
    buyer_headers,
    ops_headers,
    seller_a_headers,
    seller_b_headers,
)


def _product(client: TestClient, name: str = "Tenis XYZ") -> dict:
    response = client.post("/v1/products", json={"name": name, "description": "Par"})
    assert response.status_code == 201
    return response.json()


def _offer(client: TestClient, product_id: str, headers: dict[str, str], price: str) -> dict:
    response = client.post(
        "/v1/offers",
        json={"product_id": product_id, "price": price, "stock": 50},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def _checkout(client: TestClient, offer_id: str, price: str) -> dict:
    response = client.post(
        "/v1/orders",
        json={"items": [{"offer_id": offer_id, "quantity": 1, "expected_price": price}]},
        headers=buyer_headers(client),
    )
    assert response.status_code == 201, response.text
    return response.json()["items"][0]


def _open(client: TestClient, item_id: str, reason: str, headers: dict[str, str]) -> dict:
    response = client.post(
        f"/v1/order-items/{item_id}/conversation",
        json={"reason": reason},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_create_exposes_effective_priority_but_hides_calculated(
    catalog_client: TestClient,
) -> None:
    """Buyer/Seller veem so o resultado (effective_priority), nunca o
    breakdown interno (calculated_priority/ops_override) que so a Ops le.
    """
    product = _product(catalog_client)
    offer = _offer(catalog_client, product["id"], seller_a_headers(catalog_client), "299.00")
    item = _checkout(catalog_client, offer["id"], "299.00")
    created = _open(catalog_client, item["id"], "atraso", buyer_headers(catalog_client))
    assert "calculated_priority" not in created
    assert "ops_override" not in created
    assert created["effective_priority"] in {"low", "medium", "high", "critical"}

    ops = ops_headers(catalog_client)
    detail = catalog_client.get(f"/v1/ops/conversations/{created['id']}", headers=ops)
    assert detail.status_code == 200
    body = detail.json()
    assert body["calculated_priority"] in {"low", "medium", "high"}
    assert body["ops_override"] is None
    assert body["effective_priority"] == body["calculated_priority"]
    assert body["effective_priority"] == created["effective_priority"]

    participant = catalog_client.get(
        f"/v1/conversations/{created['id']}", headers=buyer_headers(catalog_client)
    )
    assert "calculated_priority" not in participant.json()
    assert "ops_override" not in participant.json()
    assert participant.json()["effective_priority"] == body["effective_priority"]


def _advance_item_to_in_transit(client: TestClient, item_id: str, headers: dict[str, str]) -> None:
    preparing = client.patch(
        f"/v1/order-items/{item_id}", json={"status": "preparing"}, headers=headers
    )
    assert preparing.status_code == 200, preparing.text
    in_transit = client.patch(
        f"/v1/order-items/{item_id}", json={"status": "in_transit"}, headers=headers
    )
    assert in_transit.status_code == 200, in_transit.text


def test_ops_item_conversations_and_queue_order(catalog_client: TestClient) -> None:
    product = _product(catalog_client)
    offer_a = _offer(catalog_client, product["id"], seller_a_headers(catalog_client), "80.00")
    offer_b = _offer(catalog_client, product["id"], seller_b_headers(catalog_client), "80.00")
    offer_high = _offer(catalog_client, product["id"], seller_b_headers(catalog_client), "500.00")
    item_a = _checkout(catalog_client, offer_a["id"], "80.00")
    item_b = _checkout(catalog_client, offer_b["id"], "80.00")
    item_high = _checkout(catalog_client, offer_high["id"], "500.00")
    low = _open(catalog_client, item_a["id"], "elogio", buyer_headers(catalog_client))
    medium = _open(catalog_client, item_b["id"], "reclamacao", buyer_headers(catalog_client))
    high = _open(catalog_client, item_high["id"], "atraso", buyer_headers(catalog_client))
    _advance_item_to_in_transit(catalog_client, item_high["id"], seller_b_headers(catalog_client))

    ops = ops_headers(catalog_client)
    snapshot_before_refresh = catalog_client.get("/v1/ops/conversations", headers=ops).json()
    high_row = next(row for row in snapshot_before_refresh["items"] if row["id"] == high["id"])
    assert high_row["calculated_priority"] != "high"
    refreshed = catalog_client.post(
        f"/v1/ops/conversations/{high['id']}/priority/refresh", headers=ops
    )
    assert refreshed.status_code == 200
    assert refreshed.json()["calculated_priority"] == "high"

    ranked = catalog_client.get("/v1/ops/conversations", headers=ops).json()
    assert [row["id"] for row in ranked["items"]] == [high["id"], medium["id"], low["id"]]
    assert [row["effective_priority"] for row in ranked["items"]] == ["high", "medium", "low"]

    catalog_client.post(
        f"/v1/ops/conversations/{medium['id']}/critical",
        json={"justification": "Cliente precisa receber amanha"},
        headers=ops,
    )
    queue = catalog_client.get("/v1/ops/conversations", headers=ops).json()
    assert queue["total"] == 3
    assert [row["id"] for row in queue["items"]] == [medium["id"], high["id"], low["id"]]
    assert queue["items"][0]["effective_priority"] == "critical"
    assert queue["items"][0]["seller"]["id"] == str(SELLER_B_ID)
    assert queue["items"][0]["seller"]["name"] == "Loja B"
    assert queue["items"][0]["buyer"]["name"] == "Buyer Demo"
    assert queue["items"][0]["product"]["name"] == "Tenis XYZ"
    assert queue["items"][0]["order_item_status"] == "placed"
    assert queue["items"][0]["purchase_price"] == "80.00"
    assert "messages" not in queue["items"][0]
    assert queue["items"][0]["number"]

    catalog_client.post(
        f"/v1/conversations/{medium['id']}/close",
        headers=seller_b_headers(catalog_client),
    )
    after_close = catalog_client.get("/v1/ops/conversations", headers=ops).json()
    assert [row["id"] for row in after_close["items"]] == [high["id"], low["id"]]
    history = catalog_client.get(
        f"/v1/ops/order-items/{item_b['id']}/conversations", headers=ops
    ).json()
    assert history[0]["id"] == medium["id"]
    assert history[0]["status"] == "closed"
    assert "seller" not in history[0]
    assert "product" not in history[0]

    filtered_seller = catalog_client.get(
        f"/v1/ops/conversations?seller_id={SELLER_A_ID}", headers=ops
    ).json()
    assert [row["id"] for row in filtered_seller["items"]] == [low["id"]]
    filtered_priority = catalog_client.get(
        "/v1/ops/conversations?effective_priority=high", headers=ops
    ).json()
    assert [row["id"] for row in filtered_priority["items"]] == [high["id"]]
    filtered_item = catalog_client.get(
        f"/v1/ops/conversations?order_item_id={item_a['id']}", headers=ops
    ).json()
    assert [row["id"] for row in filtered_item["items"]] == [low["id"]]
    filtered_number = catalog_client.get(
        f"/v1/ops/conversations?number={item_a['number']}", headers=ops
    ).json()
    assert [row["id"] for row in filtered_number["items"]] == [low["id"]]
    too_big = catalog_client.get("/v1/ops/conversations?page_size=101", headers=ops)
    assert too_big.status_code == 422
    invalid = catalog_client.get("/v1/ops/conversations?effective_priority=urgent", headers=ops)
    assert invalid.status_code == 422


def test_critical_refresh_and_remove(catalog_client: TestClient, test_engine) -> None:
    product = _product(catalog_client)
    offer = _offer(catalog_client, product["id"], seller_a_headers(catalog_client), "80.00")
    item = _checkout(catalog_client, offer["id"], "80.00")
    opened = _open(catalog_client, item["id"], "elogio", buyer_headers(catalog_client))
    ops = ops_headers(catalog_client)
    conversation_id = opened["id"]

    before_critical = catalog_client.get(
        f"/v1/ops/conversations/{conversation_id}", headers=ops
    ).json()["calculated_priority"]
    missing = catalog_client.post(
        f"/v1/ops/conversations/{conversation_id}/critical",
        json={},
        headers=ops,
    )
    assert missing.status_code == 422
    blank = catalog_client.post(
        f"/v1/ops/conversations/{conversation_id}/critical",
        json={"justification": "   "},
        headers=ops,
    )
    assert blank.status_code == 422

    applied = catalog_client.post(
        f"/v1/ops/conversations/{conversation_id}/critical",
        json={"justification": "Prazo do cliente"},
        headers=ops,
    )
    assert applied.status_code == 200
    assert applied.json()["ops_override"] == "critical"
    assert applied.json()["effective_priority"] == "critical"
    assert applied.json()["calculated_priority"] == before_critical
    comments = catalog_client.get(
        f"/v1/ops/order-items/{item['id']}/internal-comments", headers=ops
    ).json()
    assert comments[-1]["content"] == "Prazo do cliente"
    assert comments[-1]["author_type"] == "ops"

    again = catalog_client.post(
        f"/v1/ops/conversations/{conversation_id}/critical",
        json={"justification": "outra"},
        headers=ops,
    )
    assert again.status_code == 409

    with Session(test_engine) as session:
        conversation = session.get(Conversation, UUID(conversation_id))
        assert conversation is not None
        conversation.created_at = datetime.now(UTC) - timedelta(hours=50)
        session.commit()

    stale_queue = catalog_client.get("/v1/ops/conversations", headers=ops).json()
    stale_row = next(row for row in stale_queue["items"] if row["id"] == conversation_id)
    stale_calculated = stale_row["calculated_priority"]

    refreshed = catalog_client.post(
        f"/v1/ops/conversations/{conversation_id}/priority/refresh",
        headers=ops,
    )
    assert refreshed.status_code == 200
    assert refreshed.json()["ops_override"] == "critical"
    assert refreshed.json()["effective_priority"] == "critical"
    calculated = refreshed.json()["calculated_priority"]
    assert stale_calculated == "low"
    assert calculated == "medium"

    queue = catalog_client.get("/v1/ops/conversations", headers=ops).json()
    assert queue["items"][0]["id"] == conversation_id
    assert queue["items"][0]["calculated_priority"] == calculated

    removed = catalog_client.post(
        f"/v1/ops/conversations/{conversation_id}/critical/remove",
        headers=ops,
    )
    assert removed.status_code == 200
    assert removed.json()["ops_override"] is None
    assert removed.json()["effective_priority"] == calculated
    still = catalog_client.get(
        f"/v1/ops/order-items/{item['id']}/internal-comments", headers=ops
    ).json()
    assert any(row["content"] == "Prazo do cliente" for row in still)
    assert (
        catalog_client.post(
            f"/v1/ops/conversations/{conversation_id}/critical/remove",
            headers=ops,
        ).status_code
        == 409
    )


def test_priority_routes_are_ops_only(catalog_client: TestClient) -> None:
    product = _product(catalog_client)
    offer = _offer(catalog_client, product["id"], seller_a_headers(catalog_client), "299.00")
    item = _checkout(catalog_client, offer["id"], "299.00")
    opened = _open(catalog_client, item["id"], "atraso", buyer_headers(catalog_client))
    conversation_id = opened["id"]
    for headers in (buyer_headers(catalog_client), seller_a_headers(catalog_client)):
        assert catalog_client.get("/v1/ops/conversations", headers=headers).status_code == 403
        assert (
            catalog_client.get(
                f"/v1/ops/conversations/{conversation_id}", headers=headers
            ).status_code
            == 403
        )
        assert (
            catalog_client.post(
                f"/v1/ops/conversations/{conversation_id}/critical",
                json={"justification": "nope"},
                headers=headers,
            ).status_code
            == 403
        )
    assert catalog_client.get("/v1/ops/conversations").status_code == 401
    missing = catalog_client.get(
        f"/v1/ops/conversations/{uuid4()}", headers=ops_headers(catalog_client)
    )
    assert missing.status_code == 404


def test_same_band_orders_by_last_interaction(catalog_client: TestClient, test_engine) -> None:
    product = _product(catalog_client)
    offer_a = _offer(catalog_client, product["id"], seller_a_headers(catalog_client), "80.00")
    offer_b = _offer(catalog_client, product["id"], seller_b_headers(catalog_client), "80.00")
    item_a = _checkout(catalog_client, offer_a["id"], "80.00")
    item_b = _checkout(catalog_client, offer_b["id"], "80.00")
    older = _open(catalog_client, item_a["id"], "elogio", buyer_headers(catalog_client))
    newer = _open(catalog_client, item_b["id"], "elogio", buyer_headers(catalog_client))

    older_at = datetime.now(UTC) - timedelta(hours=2)
    newer_at = datetime.now(UTC) - timedelta(hours=1)
    with Session(test_engine) as session:
        first = session.get(Conversation, UUID(older["id"]))
        second = session.get(Conversation, UUID(newer["id"]))
        assert first is not None and second is not None
        first.last_interaction_at = older_at
        second.last_interaction_at = newer_at
        session.commit()

    queue = catalog_client.get("/v1/ops/conversations", headers=ops_headers(catalog_client)).json()
    assert [row["id"] for row in queue["items"]] == [newer["id"], older["id"]]


def test_ops_queue_empty_and_pagination(catalog_client: TestClient) -> None:
    ops = ops_headers(catalog_client)
    empty = catalog_client.get("/v1/ops/conversations", headers=ops)
    assert empty.status_code == 200
    assert empty.json() == {"items": [], "page": 1, "page_size": 20, "total": 0}

    product = _product(catalog_client)
    offer_a = _offer(catalog_client, product["id"], seller_a_headers(catalog_client), "80.00")
    offer_b = _offer(catalog_client, product["id"], seller_b_headers(catalog_client), "80.00")
    item_a = _checkout(catalog_client, offer_a["id"], "80.00")
    item_b = _checkout(catalog_client, offer_b["id"], "80.00")
    first = _open(catalog_client, item_a["id"], "elogio", buyer_headers(catalog_client))
    second = _open(catalog_client, item_b["id"], "elogio", buyer_headers(catalog_client))
    page_two = catalog_client.get("/v1/ops/conversations?page=2&page_size=1", headers=ops).json()
    assert page_two["page"] == 2
    assert page_two["page_size"] == 1
    assert page_two["total"] == 2
    assert len(page_two["items"]) == 1
    assert page_two["items"][0]["id"] in {first["id"], second["id"]}


def test_ops_item_lists_open_and_closed(catalog_client: TestClient) -> None:
    product = _product(catalog_client)
    offer = _offer(catalog_client, product["id"], seller_a_headers(catalog_client), "80.00")
    item = _checkout(catalog_client, offer["id"], "80.00")
    first = _open(catalog_client, item["id"], "elogio", buyer_headers(catalog_client))
    closed = catalog_client.post(
        f"/v1/conversations/{first['id']}/close",
        headers=seller_a_headers(catalog_client),
    )
    assert closed.status_code == 200
    second = _open(catalog_client, item["id"], "atraso", buyer_headers(catalog_client))
    history = catalog_client.get(
        f"/v1/ops/order-items/{item['id']}/conversations",
        headers=ops_headers(catalog_client),
    ).json()
    assert [row["id"] for row in history] == [second["id"], first["id"]]
    assert [row["status"] for row in history] == ["open", "closed"]
    assert "seller" not in history[0]
    assert "product" not in history[0]


def test_refresh_uses_purchase_price_not_offer_price(catalog_client: TestClient) -> None:
    product = _product(catalog_client)
    seller = seller_a_headers(catalog_client)
    offer = _offer(catalog_client, product["id"], seller, "80.00")
    item = _checkout(catalog_client, offer["id"], "80.00")
    opened = _open(catalog_client, item["id"], "elogio", buyer_headers(catalog_client))
    patched = catalog_client.patch(
        f"/v1/offers/{offer['id']}", json={"price": "5000.00"}, headers=seller
    )
    assert patched.status_code == 200
    ops = ops_headers(catalog_client)
    refreshed = catalog_client.post(
        f"/v1/ops/conversations/{opened['id']}/priority/refresh", headers=ops
    )
    assert refreshed.status_code == 200
    assert refreshed.json()["calculated_priority"] == "low"


def test_p5_integrated_journey(catalog_client: TestClient) -> None:
    product = _product(catalog_client)
    seller_a = seller_a_headers(catalog_client)
    seller_b = seller_b_headers(catalog_client)
    buyer = buyer_headers(catalog_client)
    offer_subject = _offer(catalog_client, product["id"], seller_a, "500.00")
    offer_companion = _offer(catalog_client, product["id"], seller_b, "500.00")
    subject_item = _checkout(catalog_client, offer_subject["id"], "500.00")
    companion_item = _checkout(catalog_client, offer_companion["id"], "500.00")
    subject = _open(catalog_client, subject_item["id"], "atraso", buyer)
    companion = _open(catalog_client, companion_item["id"], "atraso", buyer)
    _advance_item_to_in_transit(catalog_client, companion_item["id"], seller_b)

    ops = ops_headers(catalog_client)
    created = catalog_client.get(f"/v1/ops/conversations/{subject['id']}", headers=ops)
    assert created.status_code == 200
    assert created.json()["calculated_priority"] == "medium"
    assert created.json()["effective_priority"] == "medium"

    catalog_client.post(f"/v1/ops/conversations/{companion['id']}/priority/refresh", headers=ops)
    queued = catalog_client.get("/v1/ops/conversations", headers=ops).json()
    ids = [row["id"] for row in queued["items"]]
    assert subject["id"] in ids
    assert queued["items"][0]["id"] == companion["id"]

    _advance_item_to_in_transit(catalog_client, subject_item["id"], seller_a)
    stale = catalog_client.get("/v1/ops/conversations", headers=ops).json()
    stale_row = next(row for row in stale["items"] if row["id"] == subject["id"])
    assert stale_row["calculated_priority"] == "medium"

    refreshed = catalog_client.post(
        f"/v1/ops/conversations/{subject['id']}/priority/refresh", headers=ops
    )
    assert refreshed.status_code == 200
    assert refreshed.json()["calculated_priority"] == "high"
    assert refreshed.json()["ops_override"] is None

    ranked = catalog_client.get("/v1/ops/conversations", headers=ops).json()
    assert ranked["items"][0]["id"] == companion["id"]

    critical = catalog_client.post(
        f"/v1/ops/conversations/{subject['id']}/critical",
        json={"justification": "Cliente em risco"},
        headers=ops,
    )
    assert critical.status_code == 200
    assert critical.json()["ops_override"] == "critical"
    assert critical.json()["effective_priority"] == "critical"
    assert critical.json()["calculated_priority"] == "high"
    comments = catalog_client.get(
        f"/v1/ops/order-items/{subject_item['id']}/internal-comments", headers=ops
    ).json()
    assert comments[-1]["content"] == "Cliente em risco"
    assert comments[-1]["author_type"] == "ops"

    top = catalog_client.get("/v1/ops/conversations", headers=ops).json()
    assert top["items"][0]["id"] == subject["id"]
    assert top["items"][0]["effective_priority"] == "critical"

    removed = catalog_client.post(
        f"/v1/ops/conversations/{subject['id']}/critical/remove", headers=ops
    )
    assert removed.status_code == 200
    assert removed.json()["ops_override"] is None
    assert removed.json()["calculated_priority"] == "high"
    assert removed.json()["effective_priority"] == "high"
