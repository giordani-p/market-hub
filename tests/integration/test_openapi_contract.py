"""Guarda do API First: a implementacao deve cobrir o contrato commitado.

O contrato em api/openapi.yaml e escrito a mao e revisado antes do codigo.
Se este teste falhar, a rota especificada ainda nao foi implementada ou o
codigo passou a expor algo que nao esta no contrato.
"""

from pathlib import Path

import yaml
from fastapi.testclient import TestClient

CONTRACT_PATH = Path(__file__).parents[2] / "api" / "openapi.yaml"
HTTP_METHODS = {"get", "put", "post", "delete", "options", "head", "patch", "trace"}


def _operations(path_item: dict) -> list[str]:
    return sorted(name for name in path_item if name in HTTP_METHODS)


def test_implemented_routes_match_contract(client: TestClient) -> None:
    contract = yaml.safe_load(CONTRACT_PATH.read_text())
    generated = client.get("/openapi.json").json()

    for path, operations in contract["paths"].items():
        assert path in generated["paths"], f"{path} especificado no contrato e nao implementado"
        assert _operations(operations) == _operations(generated["paths"][path])

    assert sorted(generated["paths"]) == sorted(contract["paths"])
