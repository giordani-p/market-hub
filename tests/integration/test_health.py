from fastapi.testclient import TestClient

from app import __version__


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["version"] == __version__
    assert response.json()["version"] == "0.7.0"
