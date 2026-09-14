from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.models import User, UserRole
from app.auth.passwords import hash_password
from tests.conftest import TEST_SEED_PASSWORD
from tests.integration.auth_helpers import (
    buyer_headers,
    ops_headers,
    seller_a_headers,
    seller_b_headers,
)

EMPTY_STATUS = {
    "placed": 0,
    "preparing": 0,
    "in_transit": 0,
    "delivered": 0,
    "cancelled": 0,
}
EMPTY_PRIORITY = {"critical": 0, "high": 0, "medium": 0, "low": 0}


def _product(client: TestClient, name: str = "Tenis XYZ") -> dict:
    response = client.post("/v1/products", json={"name": name})
    assert response.status_code == 201
    return response.json()


def _offer(
    client: TestClient,
    product_id: str,
    headers: dict[str, str],
    price: str = "299.00",
    stock: int = 50,
) -> dict:
    response = client.post(
        "/v1/offers",
        json={"product_id": product_id, "price": price, "stock": stock},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def _checkout(
    client: TestClient,
    items: list[dict],
    headers: dict[str, str] | None = None,
) -> dict:
    response = client.post(
        "/v1/orders",
        json={"items": items},
        headers=headers or buyer_headers(client),
    )
    assert response.status_code == 201, response.text
    return response.json()


def _checkout_item(client: TestClient, offer_id: str, price: str = "299.00") -> dict:
    return _checkout(client, [{"offer_id": offer_id, "quantity": 1, "expected_price": price}])[
        "items"
    ][0]


def _open(client: TestClient, item_id: str, reason: str = "atraso") -> dict:
    response = client.post(
        f"/v1/order-items/{item_id}/conversation",
        json={"reason": reason},
        headers=buyer_headers(client),
    )
    assert response.status_code == 201, response.text
    return response.json()


def _advance(client: TestClient, item_id: str, headers: dict[str, str], *statuses: str) -> None:
    for status in statuses:
        response = client.patch(
            f"/v1/order-items/{item_id}", json={"status": status}, headers=headers
        )
        assert response.status_code == 200, response.text


def _dashboard(client: TestClient, headers: dict[str, str] | None = None):
    return client.get("/v1/dashboard", headers=headers)


def test_empty_dashboards_return_zeros(catalog_client: TestClient) -> None:
    seller = _dashboard(catalog_client, seller_a_headers(catalog_client))
    assert seller.status_code == 200
    assert seller.json() == {
        "role": "seller",
        "summary": {
            "total_order_items": 0,
            "active_order_items": 0,
            "order_items_by_status": EMPTY_STATUS,
        },
        "attention": {"open_conversations": 0},
        "recent": {"order_items": []},
    }

    buyer = _dashboard(catalog_client, buyer_headers(catalog_client))
    assert buyer.status_code == 200
    assert buyer.json() == {
        "role": "buyer",
        "summary": {"active_orders": 0, "completed_orders": 0},
        "attention": {"open_conversations": 0},
        "recent": {"orders": []},
    }

    ops = _dashboard(catalog_client, ops_headers(catalog_client))
    assert ops.status_code == 200
    assert ops.json() == {
        "role": "ops",
        "summary": {
            "open_conversations": 0,
            "conversations_by_priority": EMPTY_PRIORITY,
        },
        "attention": {"priority_queue_preview": []},
        "recent": {},
    }


def test_seller_summary_and_zero_conversations(catalog_client: TestClient) -> None:
    product = _product(catalog_client)
    seller = seller_a_headers(catalog_client)
    offer = _offer(catalog_client, product["id"], seller, price="10.00")
    item = _checkout_item(catalog_client, offer["id"], "10.00")

    body = _dashboard(catalog_client, seller).json()
    assert body["role"] == "seller"
    assert body["summary"]["total_order_items"] == 1
    assert body["summary"]["active_order_items"] == 1
    assert body["summary"]["order_items_by_status"] == {**EMPTY_STATUS, "placed": 1}
    assert body["attention"]["open_conversations"] == 0
    assert len(body["recent"]["order_items"]) == 1
    recent = body["recent"]["order_items"][0]
    assert recent["order_item_id"] == item["id"]
    assert recent["product"]["name"] == "Tenis XYZ"
    assert recent["buyer"]["name"] == "Buyer Demo"
    assert recent["purchase_price"] == "10.00"
    assert recent["status"] == "placed"
    assert recent["quantity"] == 1


def test_seller_recent_limited_and_newest_first(catalog_client: TestClient) -> None:
    product = _product(catalog_client)
    seller = seller_a_headers(catalog_client)
    offer = _offer(catalog_client, product["id"], seller, stock=20)
    items = [_checkout_item(catalog_client, offer["id"]) for _ in range(6)]

    recent = _dashboard(catalog_client, seller).json()["recent"]["order_items"]
    assert len(recent) == 5
    assert [row["order_item_id"] for row in recent] == [item["id"] for item in reversed(items[1:])]


def test_seller_isolation_and_multi_seller_order(catalog_client: TestClient) -> None:
    product = _product(catalog_client)
    seller_a = seller_a_headers(catalog_client)
    seller_b = seller_b_headers(catalog_client)
    offer_a = _offer(catalog_client, product["id"], seller_a, price="100.00")
    offer_b = _offer(catalog_client, product["id"], seller_b, price="50.00")
    order = _checkout(
        catalog_client,
        [
            {"offer_id": offer_a["id"], "quantity": 1, "expected_price": "100.00"},
            {"offer_id": offer_b["id"], "quantity": 1, "expected_price": "50.00"},
        ],
    )
    item_a = next(item for item in order["items"] if item["offer_id"] == offer_a["id"])
    _open(catalog_client, item_a["id"], "atraso")

    dash_a = _dashboard(catalog_client, seller_a).json()
    dash_b = _dashboard(catalog_client, seller_b).json()
    assert dash_a["summary"]["total_order_items"] == 1
    assert dash_b["summary"]["total_order_items"] == 1
    assert dash_a["recent"]["order_items"][0]["order_item_id"] == item_a["id"]
    assert dash_b["recent"]["order_items"][0]["order_item_id"] != item_a["id"]
    assert dash_a["attention"]["open_conversations"] == 1
    assert dash_b["attention"]["open_conversations"] == 0

    buyer = _dashboard(catalog_client, buyer_headers(catalog_client)).json()
    assert buyer["summary"]["active_orders"] == 1
    assert buyer["attention"]["open_conversations"] == 1


def test_buyer_counts_order_once_and_completed(catalog_client: TestClient) -> None:
    product = _product(catalog_client)
    seller = seller_a_headers(catalog_client)
    offer_a = _offer(catalog_client, product["id"], seller, price="10.00")
    offer_b = _offer(catalog_client, product["id"], seller, price="5.00")
    order = _checkout(
        catalog_client,
        [
            {"offer_id": offer_a["id"], "quantity": 2, "expected_price": "10.00"},
            {"offer_id": offer_b["id"], "quantity": 1, "expected_price": "5.00"},
        ],
    )
    buyer = buyer_headers(catalog_client)
    body = _dashboard(catalog_client, buyer).json()
    assert body["role"] == "buyer"
    assert body["summary"]["active_orders"] == 1
    assert body["summary"]["completed_orders"] == 0
    assert "calculated_priority" not in body
    assert "seller" not in body
    assert "priority_queue_preview" not in body["attention"]
    recent = body["recent"]["orders"][0]
    assert recent["order_id"] == order["id"]
    assert recent["status"] == "in_progress"
    assert recent["total_amount"] == "25.00"
    assert len(recent["items"]) == 2
    assert "purchase_price" not in recent["items"][0]

    for item in order["items"]:
        _advance(catalog_client, item["id"], seller, "preparing", "in_transit", "delivered")

    completed = _dashboard(catalog_client, buyer).json()
    assert completed["summary"]["active_orders"] == 0
    assert completed["summary"]["completed_orders"] == 1
    assert completed["recent"]["orders"][0]["status"] == "completed"


def test_buyer_mixed_and_cancelled_orders_out_of_summary(catalog_client: TestClient) -> None:
    product = _product(catalog_client)
    seller = seller_a_headers(catalog_client)
    offer_a = _offer(catalog_client, product["id"], seller, price="20.00")
    offer_b = _offer(catalog_client, product["id"], seller, price="7.00")
    mixed = _checkout(
        catalog_client,
        [
            {"offer_id": offer_a["id"], "quantity": 1, "expected_price": "20.00"},
            {"offer_id": offer_b["id"], "quantity": 1, "expected_price": "7.00"},
        ],
    )
    delivered_item = next(item for item in mixed["items"] if item["offer_id"] == offer_a["id"])
    cancelled_item = next(item for item in mixed["items"] if item["offer_id"] == offer_b["id"])
    _advance(catalog_client, delivered_item["id"], seller, "preparing", "in_transit", "delivered")
    cancel = catalog_client.post(f"/v1/order-items/{cancelled_item['id']}/cancel", headers=seller)
    assert cancel.status_code == 200, cancel.text

    only_cancelled_offer = _offer(catalog_client, product["id"], seller, price="3.00")
    only_cancelled = _checkout_item(catalog_client, only_cancelled_offer["id"], "3.00")
    catalog_client.post(f"/v1/order-items/{only_cancelled['id']}/cancel", headers=seller)

    body = _dashboard(catalog_client, buyer_headers(catalog_client)).json()
    assert body["summary"]["active_orders"] == 0
    assert body["summary"]["completed_orders"] == 0
    statuses = {row["order_id"]: row["status"] for row in body["recent"]["orders"]}
    assert statuses[mixed["id"]] == "cancelled"
    mixed_row = next(row for row in body["recent"]["orders"] if row["order_id"] == mixed["id"])
    assert mixed_row["total_amount"] == "27.00"


def test_buyer_recent_limited_and_newest_first(catalog_client: TestClient) -> None:
    product = _product(catalog_client)
    offer = _offer(catalog_client, product["id"], seller_a_headers(catalog_client), stock=20)
    orders = [_checkout_item(catalog_client, offer["id"]) for _ in range(6)]

    recent = _dashboard(catalog_client, buyer_headers(catalog_client)).json()["recent"]["orders"]
    assert len(recent) == 5
    expected = [item["order_id"] for item in reversed(orders[1:])]
    assert [row["order_id"] for row in recent] == expected


def test_buyer_two_cannot_see_seed_buyer_data(catalog_client: TestClient, test_engine) -> None:
    product = _product(catalog_client)
    offer = _offer(catalog_client, product["id"], seller_a_headers(catalog_client))
    item = _checkout_item(catalog_client, offer["id"])
    _open(catalog_client, item["id"])

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
    body = _dashboard(catalog_client, other).json()
    assert body["summary"]["active_orders"] == 0
    assert body["attention"]["open_conversations"] == 0
    assert body["recent"]["orders"] == []


def test_closed_conversation_is_not_counted(catalog_client: TestClient) -> None:
    product = _product(catalog_client)
    seller = seller_a_headers(catalog_client)
    offer = _offer(catalog_client, product["id"], seller)
    item = _checkout_item(catalog_client, offer["id"])
    opened = _open(catalog_client, item["id"])
    closed = catalog_client.post(f"/v1/conversations/{opened['id']}/close", headers=seller)
    assert closed.status_code == 200

    assert _dashboard(catalog_client, seller).json()["attention"]["open_conversations"] == 0
    assert (
        _dashboard(catalog_client, buyer_headers(catalog_client)).json()["attention"][
            "open_conversations"
        ]
        == 0
    )
    ops = _dashboard(catalog_client, ops_headers(catalog_client)).json()
    assert ops["summary"]["open_conversations"] == 0
    assert ops["attention"]["priority_queue_preview"] == []


def test_ops_priority_override_and_preview_matches_queue(catalog_client: TestClient) -> None:
    product = _product(catalog_client)
    seller = seller_a_headers(catalog_client)
    ops = ops_headers(catalog_client)
    conversations = []
    for _ in range(6):
        offer = _offer(catalog_client, product["id"], seller, price="80.00")
        item = _checkout_item(catalog_client, offer["id"], "80.00")
        conversations.append(_open(catalog_client, item["id"], "elogio"))

    marked = catalog_client.post(
        f"/v1/ops/conversations/{conversations[0]['id']}/critical",
        json={"justification": "Cliente precisa receber amanha"},
        headers=ops,
    )
    assert marked.status_code == 200, marked.text

    queue = catalog_client.get("/v1/ops/conversations", headers=ops).json()
    dash = _dashboard(catalog_client, ops).json()
    preview = dash["attention"]["priority_queue_preview"]
    assert dash["summary"]["open_conversations"] == 6
    assert dash["summary"]["conversations_by_priority"]["critical"] == 1
    assert dash["summary"]["conversations_by_priority"]["low"] == 5
    assert dash["recent"] == {}
    assert len(preview) == 5
    assert [row["conversation_id"] for row in preview] == [row["id"] for row in queue["items"][:5]]
    assert preview[0]["effective_priority"] == "critical"
    assert preview[0]["ops_override"] == "critical"
    assert preview[0]["seller"]["name"] == "Loja A"
    assert preview[0]["buyer"]["name"] == "Buyer Demo"
    assert preview[0]["product"]["name"] == "Tenis XYZ"
    assert preview[0]["purchase_price"] == "80.00"
    assert "status" not in preview[0]
    assert "messages" not in preview[0]


def test_unauthenticated_is_401(catalog_client: TestClient) -> None:
    assert _dashboard(catalog_client).status_code == 401


def test_unknown_role_is_403(catalog_client: TestClient, test_engine) -> None:
    with Session(test_engine) as session:
        session.add(
            User(
                email="admin@example.com",
                name="Admin",
                password_hash=hash_password(TEST_SEED_PASSWORD),
                role="admin",
            )
        )
        session.commit()

    token = catalog_client.post(
        "/v1/auth/login",
        json={"email": "admin@example.com", "password": TEST_SEED_PASSWORD},
    ).json()["access_token"]
    response = _dashboard(catalog_client, {"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    assert response.json()["code"] == "forbidden"
