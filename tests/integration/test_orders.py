from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.events import OrderCreated, OrderItemCancelled, publisher
from tests.integration.auth_helpers import buyer_headers, seller_a_headers, seller_b_headers


def _product(client: TestClient) -> dict:
    response = client.post("/v1/products", json={"name": "Tenis XYZ"})
    assert response.status_code == 201
    return response.json()


def _offer(
    client: TestClient,
    product_id: str,
    headers: dict[str, str],
    price: str = "299.00",
    stock: int = 10,
    available: bool = True,
) -> dict:
    response = client.post(
        "/v1/offers",
        json={"product_id": product_id, "price": price, "stock": stock, "available": available},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_checkout_with_items_from_two_sellers(catalog_client: TestClient) -> None:
    product = _product(catalog_client)
    offer_a = _offer(catalog_client, product["id"], seller_a_headers(catalog_client))
    offer_b = _offer(
        catalog_client, product["id"], seller_b_headers(catalog_client), price="150.00"
    )
    headers = buyer_headers(catalog_client)

    response = catalog_client.post(
        "/v1/orders",
        json={
            "items": [
                {"offer_id": offer_a["id"], "quantity": 2, "expected_price": "299.00"},
                {"offer_id": offer_b["id"], "quantity": 1, "expected_price": "150.00"},
            ]
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert isinstance(body["number"], int)
    assert body["number"] >= 1001
    assert len(body["items"]) == 2
    assert {item["number"] for item in body["items"]} == {
        f"{body['number']}-1",
        f"{body['number']}-2",
    }
    prices = {item["offer_id"]: item["purchase_price"] for item in body["items"]}
    assert prices[offer_a["id"]] == "299.00"
    assert prices[offer_b["id"]] == "150.00"
    assert all(item["status"] == "placed" for item in body["items"])
    assert all(item["product"]["name"] == product["name"] for item in body["items"])

    assert catalog_client.get(f"/v1/offers/{offer_a['id']}").json()["stock"] == 8
    assert catalog_client.get(f"/v1/offers/{offer_b['id']}").json()["stock"] == 9
    assert any(isinstance(event, OrderCreated) for event in publisher.events)

    get_response = catalog_client.get("/v1/orders", headers=buyer_headers(catalog_client))
    assert get_response.status_code == 200
    listed = get_response.json()[0]
    assert {item["offer_id"]: item["product"]["name"] for item in listed["items"]} == {
        offer_a["id"]: product["name"],
        offer_b["id"]: product["name"],
    }


def test_checkout_rejects_price_change_without_creating_order(catalog_client: TestClient) -> None:
    product = _product(catalog_client)
    offer = _offer(catalog_client, product["id"], seller_a_headers(catalog_client))
    catalog_client.patch(
        f"/v1/offers/{offer['id']}",
        json={"price": "310.00"},
        headers=seller_a_headers(catalog_client),
    )

    response = catalog_client.post(
        "/v1/orders",
        json={
            "items": [
                {"offer_id": offer["id"], "quantity": 1, "expected_price": "299.00"},
            ]
        },
        headers=buyer_headers(catalog_client),
    )
    assert response.status_code == 409
    body = response.json()
    assert body["code"] == "checkout_rejected"
    assert body["items"][0]["reason"] == "price_changed"
    assert body["items"][0]["current_price"] == "310.00"
    assert catalog_client.get("/v1/orders", headers=buyer_headers(catalog_client)).json() == []
    assert catalog_client.get(f"/v1/offers/{offer['id']}").json()["stock"] == 10
    assert publisher.events == []


def test_checkout_rejects_insufficient_stock(catalog_client: TestClient) -> None:
    product = _product(catalog_client)
    offer = _offer(catalog_client, product["id"], seller_a_headers(catalog_client), stock=1)
    response = catalog_client.post(
        "/v1/orders",
        json={"items": [{"offer_id": offer["id"], "quantity": 2, "expected_price": "299.00"}]},
        headers=buyer_headers(catalog_client),
    )
    assert response.status_code == 409
    assert response.json()["items"][0]["reason"] == "insufficient_stock"
    assert catalog_client.get("/v1/orders", headers=buyer_headers(catalog_client)).json() == []


def test_checkout_rejects_unavailable_offer(catalog_client: TestClient) -> None:
    product = _product(catalog_client)
    offer = _offer(catalog_client, product["id"], seller_a_headers(catalog_client), available=False)
    response = catalog_client.post(
        "/v1/orders",
        json={"items": [{"offer_id": offer["id"], "quantity": 1, "expected_price": "299.00"}]},
        headers=buyer_headers(catalog_client),
    )
    assert response.status_code == 409
    assert response.json()["items"][0]["reason"] == "unavailable"


def test_second_checkout_fails_when_stock_is_exhausted(catalog_client: TestClient) -> None:
    product = _product(catalog_client)
    offer = _offer(catalog_client, product["id"], seller_a_headers(catalog_client), stock=1)
    payload = {"items": [{"offer_id": offer["id"], "quantity": 1, "expected_price": "299.00"}]}
    headers = buyer_headers(catalog_client)

    first = catalog_client.post("/v1/orders", json=payload, headers=headers)
    second = catalog_client.post("/v1/orders", json=payload, headers=headers)

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["items"][0]["reason"] == "insufficient_stock"
    assert catalog_client.get(f"/v1/offers/{offer['id']}").json()["stock"] == 0
    assert len(catalog_client.get("/v1/orders", headers=headers).json()) == 1


def test_duplicate_offer_id_is_rejected(catalog_client: TestClient) -> None:
    product = _product(catalog_client)
    offer = _offer(catalog_client, product["id"], seller_a_headers(catalog_client))
    response = catalog_client.post(
        "/v1/orders",
        json={
            "items": [
                {"offer_id": offer["id"], "quantity": 1, "expected_price": "299.00"},
                {"offer_id": offer["id"], "quantity": 1, "expected_price": "299.00"},
            ]
        },
        headers=buyer_headers(catalog_client),
    )
    assert response.status_code == 422


def test_seller_lists_only_own_order_items(catalog_client: TestClient) -> None:
    product = _product(catalog_client)
    offer_a = _offer(catalog_client, product["id"], seller_a_headers(catalog_client))
    offer_b = _offer(
        catalog_client, product["id"], seller_b_headers(catalog_client), price="150.00"
    )
    order = catalog_client.post(
        "/v1/orders",
        json={
            "items": [
                {"offer_id": offer_a["id"], "quantity": 1, "expected_price": "299.00"},
                {"offer_id": offer_b["id"], "quantity": 1, "expected_price": "150.00"},
            ]
        },
        headers=buyer_headers(catalog_client),
    ).json()
    id_a = next(item["id"] for item in order["items"] if item["offer_id"] == offer_a["id"])
    id_b = next(item["id"] for item in order["items"] if item["offer_id"] == offer_b["id"])

    items_a = catalog_client.get("/v1/order-items", headers=seller_a_headers(catalog_client)).json()
    items_b = catalog_client.get("/v1/order-items", headers=seller_b_headers(catalog_client)).json()
    assert items_a["total"] == 1
    assert items_b["total"] == 1
    assert [item["order_item_id"] for item in items_a["items"]] == [id_a]
    assert [item["order_item_id"] for item in items_b["items"]] == [id_b]
    assert items_a["items"][0]["number"] == f"{order['number']}-1"
    assert items_b["items"][0]["number"] == f"{order['number']}-2"

    by_order = catalog_client.get(
        f"/v1/order-items?number={order['number']}",
        headers=seller_a_headers(catalog_client),
    ).json()
    assert [item["order_item_id"] for item in by_order["items"]] == [id_a]
    by_other_line = catalog_client.get(
        f"/v1/order-items?number={order['number']}-2",
        headers=seller_a_headers(catalog_client),
    ).json()
    assert by_other_line["items"] == []
    assert by_other_line["total"] == 0


def test_seller_cannot_advance_another_sellers_item(catalog_client: TestClient) -> None:
    product = _product(catalog_client)
    offer = _offer(catalog_client, product["id"], seller_a_headers(catalog_client))
    order = catalog_client.post(
        "/v1/orders",
        json={"items": [{"offer_id": offer["id"], "quantity": 1, "expected_price": "299.00"}]},
        headers=buyer_headers(catalog_client),
    ).json()
    item_id = order["items"][0]["id"]

    response = catalog_client.patch(
        f"/v1/order-items/{item_id}",
        json={"status": "preparing"},
        headers=seller_b_headers(catalog_client),
    )
    assert response.status_code == 404
    assert response.json()["code"] == "resource_not_found"


def test_seller_advances_status_in_order(catalog_client: TestClient) -> None:
    product = _product(catalog_client)
    offer = _offer(catalog_client, product["id"], seller_a_headers(catalog_client))
    order = catalog_client.post(
        "/v1/orders",
        json={"items": [{"offer_id": offer["id"], "quantity": 1, "expected_price": "299.00"}]},
        headers=buyer_headers(catalog_client),
    ).json()
    item_id = order["items"][0]["id"]
    headers = seller_a_headers(catalog_client)

    preparing = catalog_client.patch(
        f"/v1/order-items/{item_id}", json={"status": "preparing"}, headers=headers
    )
    assert preparing.status_code == 200
    assert preparing.json()["status"] == "preparing"

    skip = catalog_client.patch(
        f"/v1/order-items/{item_id}", json={"status": "delivered"}, headers=headers
    )
    assert skip.status_code == 409
    assert skip.json()["code"] == "invalid_transition"


def test_buyer_cancel_restores_stock(catalog_client: TestClient) -> None:
    product = _product(catalog_client)
    offer = _offer(catalog_client, product["id"], seller_a_headers(catalog_client), stock=5)
    order = catalog_client.post(
        "/v1/orders",
        json={"items": [{"offer_id": offer["id"], "quantity": 2, "expected_price": "299.00"}]},
        headers=buyer_headers(catalog_client),
    ).json()
    item_id = order["items"][0]["id"]

    response = catalog_client.post(
        f"/v1/order-items/{item_id}/cancel", headers=buyer_headers(catalog_client)
    )
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    assert catalog_client.get(f"/v1/offers/{offer['id']}").json()["stock"] == 5
    assert any(isinstance(event, OrderItemCancelled) for event in publisher.events)


def test_buyer_cannot_cancel_in_transit(catalog_client: TestClient) -> None:
    product = _product(catalog_client)
    offer = _offer(catalog_client, product["id"], seller_a_headers(catalog_client))
    order = catalog_client.post(
        "/v1/orders",
        json={"items": [{"offer_id": offer["id"], "quantity": 1, "expected_price": "299.00"}]},
        headers=buyer_headers(catalog_client),
    ).json()
    item_id = order["items"][0]["id"]
    seller = seller_a_headers(catalog_client)
    catalog_client.patch(f"/v1/order-items/{item_id}", json={"status": "preparing"}, headers=seller)
    catalog_client.patch(
        f"/v1/order-items/{item_id}", json={"status": "in_transit"}, headers=seller
    )

    response = catalog_client.post(
        f"/v1/order-items/{item_id}/cancel", headers=buyer_headers(catalog_client)
    )
    assert response.status_code == 409
    assert catalog_client.get(f"/v1/offers/{offer['id']}").json()["stock"] == 9


def test_seller_cancel_in_transit_does_not_restore_stock(catalog_client: TestClient) -> None:
    product = _product(catalog_client)
    offer = _offer(catalog_client, product["id"], seller_a_headers(catalog_client), stock=4)
    order = catalog_client.post(
        "/v1/orders",
        json={"items": [{"offer_id": offer["id"], "quantity": 1, "expected_price": "299.00"}]},
        headers=buyer_headers(catalog_client),
    ).json()
    item_id = order["items"][0]["id"]
    seller = seller_a_headers(catalog_client)
    catalog_client.patch(f"/v1/order-items/{item_id}", json={"status": "preparing"}, headers=seller)
    catalog_client.patch(
        f"/v1/order-items/{item_id}", json={"status": "in_transit"}, headers=seller
    )

    response = catalog_client.post(f"/v1/order-items/{item_id}/cancel", headers=seller)
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    assert catalog_client.get(f"/v1/offers/{offer['id']}").json()["stock"] == 3


def test_delete_offer_with_order_items_is_rejected(catalog_client: TestClient) -> None:
    product = _product(catalog_client)
    offer = _offer(catalog_client, product["id"], seller_a_headers(catalog_client))
    catalog_client.post(
        "/v1/orders",
        json={"items": [{"offer_id": offer["id"], "quantity": 1, "expected_price": "299.00"}]},
        headers=buyer_headers(catalog_client),
    )
    response = catalog_client.delete(
        f"/v1/offers/{offer['id']}", headers=seller_a_headers(catalog_client)
    )
    assert response.status_code == 409
    assert response.json()["code"] == "resource_in_use"


def test_buyer_cannot_get_missing_order(catalog_client: TestClient) -> None:
    response = catalog_client.get(f"/v1/orders/{uuid4()}", headers=buyer_headers(catalog_client))
    assert response.status_code == 404


def test_seller_cannot_checkout(catalog_client: TestClient) -> None:
    response = catalog_client.post(
        "/v1/orders",
        json={"items": [{"offer_id": str(uuid4()), "quantity": 1, "expected_price": "1.00"}]},
        headers=seller_a_headers(catalog_client),
    )
    assert response.status_code == 403
