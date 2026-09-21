from uuid import uuid4

from fastapi.testclient import TestClient

from app.catalog.seed import SELLER_A_ID
from tests.integration.auth_helpers import buyer_headers, seller_a_headers, seller_b_headers


def _create_product(client: TestClient, name: str = "Tenis XYZ") -> dict:
    response = client.post("/v1/products", json={"name": name})
    assert response.status_code == 201
    return response.json()


def _create_offer(
    client: TestClient,
    product_id: str,
    headers: dict[str, str] | None = None,
    price: str = "299.00",
    stock: int = 10,
    available: bool | None = None,
) -> dict:
    payload: dict = {
        "product_id": product_id,
        "price": price,
        "stock": stock,
    }
    if available is not None:
        payload["available"] = available
    headers = headers or seller_a_headers(client)
    response = client.post("/v1/offers", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_offer_uses_authenticated_seller(catalog_client: TestClient) -> None:
    product = _create_product(catalog_client)

    response = catalog_client.post(
        "/v1/offers",
        json={"product_id": product["id"], "price": "299.00", "stock": 10},
        headers=seller_a_headers(catalog_client),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["product_id"] == product["id"]
    assert body["seller_id"] == str(SELLER_A_ID)
    assert body["seller"] == {"id": str(SELLER_A_ID), "name": "Loja A"}
    assert body["price"] == "299.00"
    assert body["stock"] == 10
    assert body["available"] is True


def test_create_offer_without_token_returns_unauthorized(catalog_client: TestClient) -> None:
    product = _create_product(catalog_client)
    response = catalog_client.post(
        "/v1/offers",
        json={"product_id": product["id"], "price": "299.00", "stock": 10},
    )
    assert response.status_code == 401
    assert response.json()["code"] == "unauthorized"


def test_create_offer_as_buyer_returns_forbidden(catalog_client: TestClient) -> None:
    product = _create_product(catalog_client)
    response = catalog_client.post(
        "/v1/offers",
        json={"product_id": product["id"], "price": "299.00", "stock": 10},
        headers=buyer_headers(catalog_client),
    )
    assert response.status_code == 403
    assert response.json()["code"] == "forbidden"


def test_create_offer_with_missing_product_returns_not_found(catalog_client: TestClient) -> None:
    response = catalog_client.post(
        "/v1/offers",
        json={"product_id": str(uuid4()), "price": "299.00", "stock": 10},
        headers=seller_a_headers(catalog_client),
    )
    assert response.status_code == 404
    assert response.json()["code"] == "resource_not_found"


def test_update_offer_price(catalog_client: TestClient) -> None:
    product = _create_product(catalog_client)
    offer = _create_offer(catalog_client, product["id"])
    headers = seller_a_headers(catalog_client)

    response = catalog_client.patch(
        f"/v1/offers/{offer['id']}", json={"price": "279.00"}, headers=headers
    )

    assert response.status_code == 200
    assert response.json()["price"] == "279.00"
    assert response.json()["stock"] == offer["stock"]


def test_seller_cannot_update_another_sellers_offer(catalog_client: TestClient) -> None:
    product = _create_product(catalog_client)
    offer = _create_offer(catalog_client, product["id"], headers=seller_a_headers(catalog_client))

    response = catalog_client.patch(
        f"/v1/offers/{offer['id']}",
        json={"stock": 1},
        headers=seller_b_headers(catalog_client),
    )
    assert response.status_code == 403
    assert response.json()["code"] == "forbidden"


def test_update_offer_stock(catalog_client: TestClient) -> None:
    product = _create_product(catalog_client)
    offer = _create_offer(catalog_client, product["id"])
    headers = seller_a_headers(catalog_client)

    response = catalog_client.patch(f"/v1/offers/{offer['id']}", json={"stock": 5}, headers=headers)
    assert response.status_code == 200
    assert response.json()["stock"] == 5


def test_update_offer_availability(catalog_client: TestClient) -> None:
    product = _create_product(catalog_client)
    offer = _create_offer(catalog_client, product["id"])
    headers = seller_a_headers(catalog_client)

    response = catalog_client.patch(
        f"/v1/offers/{offer['id']}", json={"available": False}, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["available"] is False


def test_negative_stock_is_rejected(catalog_client: TestClient) -> None:
    product = _create_product(catalog_client)
    headers = seller_a_headers(catalog_client)

    create_response = catalog_client.post(
        "/v1/offers",
        json={"product_id": product["id"], "price": "299.00", "stock": -1},
        headers=headers,
    )
    assert create_response.status_code == 422

    offer = _create_offer(catalog_client, product["id"], headers=headers)
    update_response = catalog_client.patch(
        f"/v1/offers/{offer['id']}", json={"stock": -1}, headers=headers
    )
    assert update_response.status_code == 422


def test_get_offer(catalog_client: TestClient) -> None:
    product = _create_product(catalog_client)
    offer = _create_offer(catalog_client, product["id"])

    response = catalog_client.get(f"/v1/offers/{offer['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == offer["id"]
    assert response.json()["seller"] == {"id": str(SELLER_A_ID), "name": "Loja A"}


def test_list_offers(catalog_client: TestClient) -> None:
    product = _create_product(catalog_client)
    first = _create_offer(catalog_client, product["id"], headers=seller_a_headers(catalog_client))
    second = _create_offer(
        catalog_client,
        product["id"],
        headers=seller_b_headers(catalog_client),
        price="279.00",
    )

    response = catalog_client.get("/v1/offers")
    assert response.status_code == 200
    ids = {item["id"] for item in response.json()}
    assert {first["id"], second["id"]} <= ids


def test_list_offers_filtered_by_seller(catalog_client: TestClient) -> None:
    product = _create_product(catalog_client)
    of_a = _create_offer(catalog_client, product["id"], headers=seller_a_headers(catalog_client))
    _create_offer(
        catalog_client, product["id"], headers=seller_b_headers(catalog_client), price="279.00"
    )

    response = catalog_client.get(f"/v1/offers?seller_id={SELLER_A_ID}")
    assert response.status_code == 200
    body = response.json()
    assert [item["id"] for item in body] == [of_a["id"]]
    assert body[0]["seller_id"] == str(SELLER_A_ID)
    assert body[0]["seller"] == {"id": str(SELLER_A_ID), "name": "Loja A"}


def test_delete_offer(catalog_client: TestClient) -> None:
    product = _create_product(catalog_client)
    offer = _create_offer(catalog_client, product["id"])
    headers = seller_a_headers(catalog_client)

    response = catalog_client.delete(f"/v1/offers/{offer['id']}", headers=headers)
    assert response.status_code == 204
    assert catalog_client.get(f"/v1/offers/{offer['id']}").status_code == 404


def test_get_missing_offer_returns_not_found(catalog_client: TestClient) -> None:
    response = catalog_client.get(f"/v1/offers/{uuid4()}")
    assert response.status_code == 404
    assert response.json()["code"] == "resource_not_found"


def test_update_missing_offer_returns_not_found(catalog_client: TestClient) -> None:
    response = catalog_client.patch(
        f"/v1/offers/{uuid4()}", json={"stock": 1}, headers=seller_a_headers(catalog_client)
    )
    assert response.status_code == 404
    assert response.json()["code"] == "resource_not_found"


def test_delete_missing_offer_returns_not_found(catalog_client: TestClient) -> None:
    response = catalog_client.delete(
        f"/v1/offers/{uuid4()}", headers=seller_a_headers(catalog_client)
    )
    assert response.status_code == 404
    assert response.json()["code"] == "resource_not_found"
