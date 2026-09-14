from uuid import uuid4

from fastapi.testclient import TestClient

from app.catalog.seed import SELLER_B_ID
from app.core.events import OrderItemCancelled, OrderItemStatusChanged, publisher
from tests.integration.auth_helpers import buyer_headers, seller_a_headers, seller_b_headers


def _product(client: TestClient, name: str = "Tenis XYZ") -> dict:
    response = client.post("/v1/products", json={"name": name, "description": "Par de tenis"})
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


def _checkout(client: TestClient, offer_id: str, price: str = "299.00") -> dict:
    response = client.post(
        "/v1/orders",
        json={"items": [{"offer_id": offer_id, "quantity": 1, "expected_price": price}]},
        headers=buyer_headers(client),
    )
    assert response.status_code == 201, response.text
    return response.json()["items"][0]


def test_empty_list_returns_envelope(catalog_client: TestClient) -> None:
    response = catalog_client.get("/v1/order-items", headers=seller_a_headers(catalog_client))
    assert response.status_code == 200
    body = response.json()
    assert body == {"items": [], "page": 1, "page_size": 20, "total": 0}


def test_list_is_isolated_and_newest_first(catalog_client: TestClient) -> None:
    product = _product(catalog_client)
    offer_a = _offer(catalog_client, product["id"], seller_a_headers(catalog_client))
    offer_b = _offer(
        catalog_client, product["id"], seller_b_headers(catalog_client), price="150.00"
    )
    first = _checkout(catalog_client, offer_a["id"])
    other = _checkout(catalog_client, offer_b["id"], price="150.00")
    second = _checkout(catalog_client, offer_a["id"])

    body = catalog_client.get("/v1/order-items", headers=seller_a_headers(catalog_client)).json()
    assert body["total"] == 2
    assert body["page_size"] == 20
    assert [item["order_item_id"] for item in body["items"]] == [second["id"], first["id"]]
    assert other["id"] not in [item["order_item_id"] for item in body["items"]]
    assert body["items"][0]["buyer"] == {
        "id": body["items"][0]["buyer"]["id"],
        "name": "Buyer Demo",
    }
    assert body["items"][0]["product"]["name"] == "Tenis XYZ"


def test_pagination_defaults_and_limits(catalog_client: TestClient) -> None:
    product = _product(catalog_client)
    offer = _offer(catalog_client, product["id"], seller_a_headers(catalog_client), stock=30)
    for _ in range(21):
        _checkout(catalog_client, offer["id"])

    headers = seller_a_headers(catalog_client)
    first_page = catalog_client.get("/v1/order-items", headers=headers).json()
    assert first_page["total"] == 21
    assert first_page["page"] == 1
    assert first_page["page_size"] == 20
    assert len(first_page["items"]) == 20

    second_page = catalog_client.get("/v1/order-items?page=2", headers=headers).json()
    assert len(second_page["items"]) == 1
    assert second_page["total"] == 21

    beyond = catalog_client.get("/v1/order-items?page=3", headers=headers).json()
    assert beyond["items"] == []
    assert beyond["total"] == 21

    large = catalog_client.get("/v1/order-items?page_size=100", headers=headers)
    assert large.status_code == 200
    assert len(large.json()["items"]) == 21

    too_big = catalog_client.get("/v1/order-items?page_size=101", headers=headers)
    assert too_big.status_code == 422


def test_filters_status_period_and_order_item_id(catalog_client: TestClient) -> None:
    product = _product(catalog_client)
    offer_a = _offer(catalog_client, product["id"], seller_a_headers(catalog_client))
    offer_b = _offer(
        catalog_client, product["id"], seller_b_headers(catalog_client), price="150.00"
    )
    placed = _checkout(catalog_client, offer_a["id"])
    foreign = _checkout(catalog_client, offer_b["id"], price="150.00")
    preparing = _checkout(catalog_client, offer_a["id"])
    seller = seller_a_headers(catalog_client)
    catalog_client.patch(
        f"/v1/order-items/{preparing['id']}", json={"status": "preparing"}, headers=seller
    )

    listed = catalog_client.get("/v1/order-items", headers=seller).json()["items"]
    newer = listed[0]
    older = listed[1]

    by_status = catalog_client.get("/v1/order-items?status=preparing", headers=seller).json()
    assert [item["order_item_id"] for item in by_status["items"]] == [preparing["id"]]

    by_id = catalog_client.get(
        f"/v1/order-items?order_item_id={placed['id']}", headers=seller
    ).json()
    assert [item["order_item_id"] for item in by_id["items"]] == [placed["id"]]

    foreign_filter = catalog_client.get(
        f"/v1/order-items?order_item_id={foreign['id']}", headers=seller
    ).json()
    assert foreign_filter["items"] == []
    assert foreign_filter["total"] == 0

    mismatch = catalog_client.get(
        f"/v1/order-items?order_item_id={placed['id']}&status=preparing", headers=seller
    ).json()
    assert mismatch["items"] == []

    period = catalog_client.get(
        "/v1/order-items",
        params={"from": older["created_at"], "to": newer["created_at"], "status": "placed"},
        headers=seller,
    ).json()
    assert [item["order_item_id"] for item in period["items"]] == [placed["id"]]

    inverted = catalog_client.get(
        "/v1/order-items",
        params={"from": newer["created_at"], "to": older["created_at"]},
        headers=seller,
    ).json()
    assert inverted["items"] == []


def test_seller_id_query_does_not_authorize(catalog_client: TestClient) -> None:
    product = _product(catalog_client)
    offer_a = _offer(catalog_client, product["id"], seller_a_headers(catalog_client))
    offer_b = _offer(
        catalog_client, product["id"], seller_b_headers(catalog_client), price="150.00"
    )
    own = _checkout(catalog_client, offer_a["id"])
    _checkout(catalog_client, offer_b["id"], price="150.00")

    body = catalog_client.get(
        f"/v1/order-items?seller_id={SELLER_B_ID}",
        headers=seller_a_headers(catalog_client),
    ).json()
    assert [item["order_item_id"] for item in body["items"]] == [own["id"]]


def test_detail_payload_and_isolation(catalog_client: TestClient) -> None:
    product = _product(catalog_client)
    offer = _offer(catalog_client, product["id"], seller_a_headers(catalog_client))
    item = _checkout(catalog_client, offer["id"])
    order_id = catalog_client.get("/v1/orders", headers=buyer_headers(catalog_client)).json()[0][
        "id"
    ]

    response = catalog_client.get(
        f"/v1/order-items/{item['id']}", headers=seller_a_headers(catalog_client)
    )
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == item["id"]
    assert body["offer_id"] == offer["id"]
    assert body["product"] == {
        "id": product["id"],
        "name": "Tenis XYZ",
        "description": "Par de tenis",
    }
    assert body["buyer"]["name"] == "Buyer Demo"
    assert body["order"]["id"] == order_id
    assert "price" not in body
    assert "stock" not in body

    other = catalog_client.get(
        f"/v1/order-items/{item['id']}", headers=seller_b_headers(catalog_client)
    )
    assert other.status_code == 404
    missing = catalog_client.get(
        f"/v1/order-items/{uuid4()}", headers=seller_a_headers(catalog_client)
    )
    assert missing.status_code == 404


def test_buyer_cannot_list_but_can_get_own_item_detail(catalog_client: TestClient) -> None:
    """Listagem continua exclusiva do Seller; o detalhe do proprio item e
    liberado pro Buyer desde o F5 do frontend, pro deep link de Notification
    (entity_type=ORDER_ITEM) resolver o order_id que a rota do Buyer exige.
    """
    product = _product(catalog_client)
    offer = _offer(catalog_client, product["id"], seller_a_headers(catalog_client))
    item = _checkout(catalog_client, offer["id"])
    buyer = buyer_headers(catalog_client)

    listed = catalog_client.get("/v1/order-items", headers=buyer)
    assert listed.status_code == 403

    detail = catalog_client.get(f"/v1/order-items/{item['id']}", headers=buyer)
    assert detail.status_code == 200
    body = detail.json()
    assert body["id"] == item["id"]
    assert "order" in body and "id" in body["order"]
    assert "price" not in body
    assert "stock" not in body

    anonymous = catalog_client.get("/v1/order-items")
    assert anonymous.status_code == 401


def test_patch_idempotent_and_revalidates(catalog_client: TestClient) -> None:
    product = _product(catalog_client)
    offer = _offer(catalog_client, product["id"], seller_a_headers(catalog_client))
    item = _checkout(catalog_client, offer["id"])
    headers = seller_a_headers(catalog_client)

    first = catalog_client.patch(
        f"/v1/order-items/{item['id']}", json={"status": "preparing"}, headers=headers
    )
    assert first.status_code == 200
    changed = [event for event in publisher.events if isinstance(event, OrderItemStatusChanged)]
    assert len(changed) == 1

    repeat = catalog_client.patch(
        f"/v1/order-items/{item['id']}", json={"status": "preparing"}, headers=headers
    )
    assert repeat.status_code == 200
    assert repeat.json()["status"] == "preparing"
    changed_after = [
        event for event in publisher.events if isinstance(event, OrderItemStatusChanged)
    ]
    assert len(changed_after) == 1

    skip = catalog_client.patch(
        f"/v1/order-items/{item['id']}", json={"status": "delivered"}, headers=headers
    )
    assert skip.status_code == 409

    cancelled = catalog_client.patch(
        f"/v1/order-items/{item['id']}", json={"status": "cancelled"}, headers=headers
    )
    assert cancelled.status_code == 422


def test_cancel_rules_and_idempotency(catalog_client: TestClient) -> None:
    product = _product(catalog_client)
    offer = _offer(catalog_client, product["id"], seller_a_headers(catalog_client), stock=5)
    placed = _checkout(catalog_client, offer["id"])
    seller = seller_a_headers(catalog_client)

    first = catalog_client.post(f"/v1/order-items/{placed['id']}/cancel", headers=seller)
    assert first.status_code == 200
    assert catalog_client.get(f"/v1/offers/{offer['id']}").json()["stock"] == 5
    cancelled_events = [
        event for event in publisher.events if isinstance(event, OrderItemCancelled)
    ]
    assert len(cancelled_events) == 1

    repeat = catalog_client.post(f"/v1/order-items/{placed['id']}/cancel", headers=seller)
    assert repeat.status_code == 200
    assert catalog_client.get(f"/v1/offers/{offer['id']}").json()["stock"] == 5
    cancelled_after = [event for event in publisher.events if isinstance(event, OrderItemCancelled)]
    assert len(cancelled_after) == 1

    buyer_item = _checkout(catalog_client, offer["id"])
    buyer = buyer_headers(catalog_client)
    catalog_client.post(f"/v1/order-items/{buyer_item['id']}/cancel", headers=buyer)
    stock_after_buyer = catalog_client.get(f"/v1/offers/{offer['id']}").json()["stock"]
    catalog_client.post(f"/v1/order-items/{buyer_item['id']}/cancel", headers=buyer)
    assert catalog_client.get(f"/v1/offers/{offer['id']}").json()["stock"] == stock_after_buyer

    delivered = _checkout(catalog_client, offer["id"])
    catalog_client.patch(
        f"/v1/order-items/{delivered['id']}", json={"status": "preparing"}, headers=seller
    )
    catalog_client.patch(
        f"/v1/order-items/{delivered['id']}", json={"status": "in_transit"}, headers=seller
    )
    catalog_client.patch(
        f"/v1/order-items/{delivered['id']}", json={"status": "delivered"}, headers=seller
    )
    rejected = catalog_client.post(f"/v1/order-items/{delivered['id']}/cancel", headers=seller)
    assert rejected.status_code == 409


def test_seller_cannot_operate_foreign_item(catalog_client: TestClient) -> None:
    product = _product(catalog_client)
    offer = _offer(catalog_client, product["id"], seller_a_headers(catalog_client))
    item = _checkout(catalog_client, offer["id"])
    other = seller_b_headers(catalog_client)

    patch = catalog_client.patch(
        f"/v1/order-items/{item['id']}", json={"status": "preparing"}, headers=other
    )
    cancel = catalog_client.post(f"/v1/order-items/{item['id']}/cancel", headers=other)
    assert patch.status_code == 404
    assert cancel.status_code == 404
