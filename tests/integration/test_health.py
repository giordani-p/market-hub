from typing import NoReturn

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from app import __version__


def test_health_returns_ok(client: TestClient, test_engine: Engine) -> None:
    response = client.get("/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": __version__}


def test_health_returns_error_when_database_is_down(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail_engine() -> NoReturn:
        raise RuntimeError("database down")

    monkeypatch.setattr("app.health.get_engine", fail_engine)

    response = client.get("/v1/health")

    assert response.status_code == 503
    assert response.json() == {"status": "error", "version": __version__}
    assert "database down" not in response.text
