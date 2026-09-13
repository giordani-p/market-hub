from fastapi.testclient import TestClient

from app.auth.seed import BUYER_EMAIL, OPS_EMAIL, SELLER_A_EMAIL, SELLER_B_EMAIL
from tests.conftest import TEST_SEED_PASSWORD


def auth_header(client: TestClient, email: str) -> dict[str, str]:
    response = client.post("/v1/auth/login", json={"email": email, "password": TEST_SEED_PASSWORD})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def seller_a_headers(client: TestClient) -> dict[str, str]:
    return auth_header(client, SELLER_A_EMAIL)


def seller_b_headers(client: TestClient) -> dict[str, str]:
    return auth_header(client, SELLER_B_EMAIL)


def buyer_headers(client: TestClient) -> dict[str, str]:
    return auth_header(client, BUYER_EMAIL)


def ops_headers(client: TestClient) -> dict[str, str]:
    return auth_header(client, OPS_EMAIL)
