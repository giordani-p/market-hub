from uuid import uuid4

from fastapi.testclient import TestClient

from app.catalog.seed import SELLER_A_ID


def _create_product(
    client: TestClient, name: str = "Tenis XYZ", description: str | None = "Modelo 2026"
) -> dict:
    payload: dict = {"name": name}
    if description is not None:
        payload["description"] = description
    response = client.post("/v1/products", json=payload)
    assert response.status_code == 201
    return response.json()


def _create_offer(client: TestClient, product_id: str) -> dict:
    response = client.post(
        "/v1/offers",
        json={
            "product_id": product_id,
            "seller_id": str(SELLER_A_ID),
            "price": "299.00",
            "stock": 10,
        },
    )
    assert response.status_code == 201
    return response.json()


def test_create_product(catalog_client: TestClient) -> None:
    response = catalog_client.post(
        "/v1/products", json={"name": "Tenis XYZ", "description": "Modelo 2026"}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Tenis XYZ"
    assert body["description"] == "Modelo 2026"
    assert body["id"]


def test_get_product(catalog_client: TestClient) -> None:
    created = _create_product(catalog_client)

    response = catalog_client.get(f"/v1/products/{created['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_list_products(catalog_client: TestClient) -> None:
    first = _create_product(catalog_client, name="Tenis XYZ")
    second = _create_product(catalog_client, name="Tenis ABC")

    response = catalog_client.get("/v1/products")

    assert response.status_code == 200
    names = {item["name"] for item in response.json()}
    assert {first["name"], second["name"]} <= names


def test_update_product(catalog_client: TestClient) -> None:
    created = _create_product(catalog_client)

    response = catalog_client.patch(f"/v1/products/{created['id']}", json={"name": "Tenis XYZ Pro"})

    assert response.status_code == 200
    assert response.json()["name"] == "Tenis XYZ Pro"
    assert response.json()["description"] == created["description"]


def test_delete_product_without_offers(catalog_client: TestClient) -> None:
    created = _create_product(catalog_client)

    response = catalog_client.delete(f"/v1/products/{created['id']}")

    assert response.status_code == 204
    assert catalog_client.get(f"/v1/products/{created['id']}").status_code == 404


def test_delete_product_with_offers_is_rejected(catalog_client: TestClient) -> None:
    created = _create_product(catalog_client)
    offer = _create_offer(catalog_client, created["id"])

    response = catalog_client.delete(f"/v1/products/{created['id']}")

    assert response.status_code == 409
    assert response.json()["code"] == "resource_in_use"
    assert catalog_client.get(f"/v1/products/{created['id']}").status_code == 200
    assert catalog_client.get(f"/v1/offers/{offer['id']}").status_code == 200


def test_get_missing_product_returns_not_found(catalog_client: TestClient) -> None:
    response = catalog_client.get(f"/v1/products/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["code"] == "resource_not_found"


def test_update_missing_product_returns_not_found(catalog_client: TestClient) -> None:
    response = catalog_client.patch(f"/v1/products/{uuid4()}", json={"name": "Novo"})

    assert response.status_code == 404
    assert response.json()["code"] == "resource_not_found"


def test_delete_missing_product_returns_not_found(catalog_client: TestClient) -> None:
    response = catalog_client.delete(f"/v1/products/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["code"] == "resource_not_found"
