from fastapi.testclient import TestClient

from app.auth.seed import BUYER_EMAIL, BUYER_ID, SELLER_A_EMAIL, SELLER_A_ID
from tests.conftest import TEST_SEED_PASSWORD
from tests.integration.auth_helpers import buyer_headers, seller_a_headers


def test_login_returns_token(catalog_client: TestClient) -> None:
    response = catalog_client.post(
        "/v1/auth/login", json={"email": BUYER_EMAIL, "password": TEST_SEED_PASSWORD}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_with_wrong_password_returns_unauthorized(catalog_client: TestClient) -> None:
    response = catalog_client.post(
        "/v1/auth/login", json={"email": BUYER_EMAIL, "password": "wrong-password"}
    )
    assert response.status_code == 401
    assert response.json()["code"] == "unauthorized"


def test_me_returns_buyer(catalog_client: TestClient) -> None:
    response = catalog_client.get("/v1/auth/me", headers=buyer_headers(catalog_client))
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(BUYER_ID)
    assert body["email"] == BUYER_EMAIL
    assert body["name"] == "Buyer Demo"
    assert body["role"] == "buyer"
    assert body["seller_id"] is None


def test_me_returns_seller(catalog_client: TestClient) -> None:
    response = catalog_client.get("/v1/auth/me", headers=seller_a_headers(catalog_client))
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == SELLER_A_EMAIL
    assert body["name"] == "Loja A"
    assert body["role"] == "seller"
    assert body["seller_id"] == str(SELLER_A_ID)


def test_me_without_token_returns_unauthorized(catalog_client: TestClient) -> None:
    response = catalog_client.get("/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["code"] == "unauthorized"


def test_register_is_not_exposed(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]
    assert "/v1/auth/register" not in paths
    response = client.post("/v1/auth/register", json={})
    assert response.status_code == 404
