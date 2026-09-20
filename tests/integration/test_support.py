from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.auth.seed import OPS_EMAIL, OPS_ID
from app.catalog.seed import SELLER_A_ID, SELLER_B_ID
from app.core.events import InternalCommentCreated, publisher
from tests.conftest import TEST_SEED_PASSWORD
from tests.integration.auth_helpers import (
    buyer_headers,
    ops_headers,
    seller_a_headers,
    seller_b_headers,
)


def _product(client: TestClient) -> dict:
    response = client.post("/v1/products", json={"name": "Tenis XYZ", "description": "Par"})
    assert response.status_code == 201
    return response.json()


def _offer(
    client: TestClient, product_id: str, headers: dict[str, str], price: str = "299.00"
) -> dict:
    response = client.post(
        "/v1/offers",
        json={"product_id": product_id, "price": price, "stock": 50},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def _checkout_item(client: TestClient, offer_id: str, price: str = "299.00") -> dict:
    response = client.post(
        "/v1/orders",
        json={"items": [{"offer_id": offer_id, "quantity": 1, "expected_price": price}]},
        headers=buyer_headers(client),
    )
    assert response.status_code == 201, response.text
    return response.json()["items"][0]


def _item_for_seller_a(client: TestClient) -> str:
    product = _product(client)
    offer = _offer(client, product["id"], seller_a_headers(client))
    return _checkout_item(client, offer["id"])["id"]


OPS_ROUTE_CASES = [
    ("GET", "/v1/ops/order-items", None),
    ("GET", "/v1/ops/order-items/{item_id}", None),
    ("GET", "/v1/ops/order-items/{item_id}/internal-comments", None),
    ("POST", "/v1/ops/order-items/{item_id}/internal-comments", {"content": "note"}),
    ("GET", "/v1/ops/order-items/{item_id}/conversations", None),
    ("GET", "/v1/ops/conversations", None),
    ("GET", "/v1/ops/conversations/{conversation_id}", None),
    ("POST", "/v1/ops/conversations/{conversation_id}/priority/refresh", None),
    ("POST", "/v1/ops/conversations/{conversation_id}/critical", {"justification": "urgent"}),
    ("POST", "/v1/ops/conversations/{conversation_id}/critical/remove", None),
]


def _ops_path(template: str) -> str:
    fake = str(uuid4())
    return template.format(item_id=fake, conversation_id=fake)


def test_ops_login_and_me(catalog_client: TestClient) -> None:
    login = catalog_client.post(
        "/v1/auth/login", json={"email": OPS_EMAIL, "password": TEST_SEED_PASSWORD}
    )
    assert login.status_code == 200
    me = catalog_client.get("/v1/auth/me", headers=ops_headers(catalog_client))
    assert me.status_code == 200
    body = me.json()
    assert body["id"] == str(OPS_ID)
    assert body["email"] == OPS_EMAIL
    assert body["name"] == "Ops Demo"
    assert body["role"] == "ops"
    assert body["seller_id"] is None


def test_anonymous_ops_and_seller_comments_are_401(catalog_client: TestClient) -> None:
    item_id = uuid4()
    assert catalog_client.get("/v1/ops/order-items").status_code == 401
    assert catalog_client.get(f"/v1/ops/order-items/{item_id}").status_code == 401
    assert catalog_client.get(f"/v1/order-items/{item_id}/internal-comments").status_code == 401
    assert (
        catalog_client.post(
            f"/v1/order-items/{item_id}/internal-comments",
            json={"content": "nope"},
        ).status_code
        == 401
    )


@pytest.mark.parametrize(("method", "template", "body"), OPS_ROUTE_CASES)
def test_anonymous_ops_routes_are_401(
    catalog_client: TestClient, method: str, template: str, body: dict | None
) -> None:
    kwargs: dict = {"headers": {}}
    if body is not None:
        kwargs["json"] = body
    response = catalog_client.request(method, _ops_path(template), **kwargs)
    assert response.status_code == 401


@pytest.mark.parametrize(("method", "template", "body"), OPS_ROUTE_CASES)
def test_buyer_and_seller_ops_routes_are_403(
    catalog_client: TestClient, method: str, template: str, body: dict | None
) -> None:
    path = _ops_path(template)
    for headers in (buyer_headers(catalog_client), seller_a_headers(catalog_client)):
        kwargs: dict = {"headers": headers}
        if body is not None:
            kwargs["json"] = body
        assert catalog_client.request(method, path, **kwargs).status_code == 403


def test_ops_empty_list_and_cross_seller_listing(catalog_client: TestClient) -> None:
    headers = ops_headers(catalog_client)
    empty = catalog_client.get("/v1/ops/order-items", headers=headers)
    assert empty.status_code == 200
    assert empty.json() == {"items": [], "page": 1, "page_size": 20, "total": 0}

    product = _product(catalog_client)
    offer_a = _offer(catalog_client, product["id"], seller_a_headers(catalog_client))
    offer_b = _offer(
        catalog_client, product["id"], seller_b_headers(catalog_client), price="150.00"
    )
    item_a = _checkout_item(catalog_client, offer_a["id"])
    item_b = _checkout_item(catalog_client, offer_b["id"], price="150.00")

    listed = catalog_client.get("/v1/ops/order-items", headers=headers).json()
    assert listed["total"] == 2
    ids = [item["order_item_id"] for item in listed["items"]]
    assert ids == [item_b["id"], item_a["id"]]
    sellers = {item["order_item_id"]: item["seller"] for item in listed["items"]}
    assert sellers[item_a["id"]] == {"id": str(SELLER_A_ID), "name": "Loja A"}
    assert sellers[item_b["id"]] == {"id": str(SELLER_B_ID), "name": "Loja B"}

    only_a = catalog_client.get(
        f"/v1/ops/order-items?seller_id={SELLER_A_ID}", headers=headers
    ).json()
    assert [item["order_item_id"] for item in only_a["items"]] == [item_a["id"]]


def test_ops_pagination_limits(catalog_client: TestClient) -> None:
    product = _product(catalog_client)
    offer = catalog_client.post(
        "/v1/offers",
        json={"product_id": product["id"], "price": "10.00", "stock": 30},
        headers=seller_a_headers(catalog_client),
    )
    assert offer.status_code == 201
    for _ in range(21):
        _checkout_item(catalog_client, offer.json()["id"], price="10.00")

    headers = ops_headers(catalog_client)
    first_page = catalog_client.get("/v1/ops/order-items", headers=headers).json()
    assert first_page["total"] == 21
    assert first_page["page_size"] == 20
    assert len(first_page["items"]) == 20
    second_page = catalog_client.get("/v1/ops/order-items?page=2", headers=headers).json()
    assert second_page["page"] == 2
    assert len(second_page["items"]) == 1
    too_big = catalog_client.get("/v1/ops/order-items?page_size=101", headers=headers)
    assert too_big.status_code == 422


def test_ops_detail_and_missing_item(catalog_client: TestClient) -> None:
    item_id = _item_for_seller_a(catalog_client)
    headers = ops_headers(catalog_client)
    detail = catalog_client.get(f"/v1/ops/order-items/{item_id}", headers=headers)
    assert detail.status_code == 200
    body = detail.json()
    assert body["id"] == item_id
    assert body["seller"] == {"id": str(SELLER_A_ID), "name": "Loja A"}
    assert body["buyer"]["name"] == "Buyer Demo"
    assert body["status"] == "placed"
    assert body["purchase_price"] == "299.00"
    assert body["product"]["name"] == "Tenis XYZ"
    missing = catalog_client.get(f"/v1/ops/order-items/{uuid4()}", headers=headers)
    assert missing.status_code == 404
    assert missing.json()["code"] == "resource_not_found"


def test_internal_comments_shared_history_without_conversation(catalog_client: TestClient) -> None:
    item_id = _item_for_seller_a(catalog_client)
    seller = seller_a_headers(catalog_client)
    ops = ops_headers(catalog_client)

    empty = catalog_client.get(f"/v1/order-items/{item_id}/internal-comments", headers=seller)
    assert empty.status_code == 200
    assert empty.json() == []

    created_seller = catalog_client.post(
        f"/v1/order-items/{item_id}/internal-comments",
        json={"content": "  Preciso de ajuda  ", "author_type": "ops"},
        headers=seller,
    )
    assert created_seller.status_code == 201
    assert created_seller.json()["author_type"] == "seller"
    assert created_seller.json()["content"] == "Preciso de ajuda"
    assert any(isinstance(event, InternalCommentCreated) for event in publisher.events)

    created_ops = catalog_client.post(
        f"/v1/ops/order-items/{item_id}/internal-comments",
        json={"content": "Vamos verificar o estoque"},
        headers=ops,
    )
    assert created_ops.status_code == 201
    assert created_ops.json()["author_type"] == "ops"

    seller_list = catalog_client.get(
        f"/v1/order-items/{item_id}/internal-comments", headers=seller
    ).json()
    ops_list = catalog_client.get(
        f"/v1/ops/order-items/{item_id}/internal-comments", headers=ops
    ).json()
    assert [row["content"] for row in seller_list] == [
        "Preciso de ajuda",
        "Vamos verificar o estoque",
    ]
    assert [row["id"] for row in seller_list] == [row["id"] for row in ops_list]

    missing_item = uuid4()
    assert (
        catalog_client.get(
            f"/v1/ops/order-items/{missing_item}/internal-comments", headers=ops
        ).status_code
        == 404
    )
    assert (
        catalog_client.post(
            f"/v1/ops/order-items/{missing_item}/internal-comments",
            json={"content": "nope"},
            headers=ops,
        ).status_code
        == 404
    )
    assert (
        catalog_client.get(
            f"/v1/ops/order-items/{missing_item}/conversations", headers=ops
        ).status_code
        == 404
    )

    blank = catalog_client.post(
        f"/v1/order-items/{item_id}/internal-comments",
        json={"content": "   "},
        headers=seller,
    )
    assert blank.status_code == 422
    assert (
        catalog_client.patch(
            f"/v1/order-items/{item_id}/internal-comments",
            json={"content": "nope"},
            headers=seller,
        ).status_code
        == 405
    )
    assert (
        catalog_client.delete(
            f"/v1/ops/order-items/{item_id}/internal-comments",
            headers=ops,
        ).status_code
        == 405
    )


def test_isolation_and_forbidden_roles(catalog_client: TestClient) -> None:
    item_id = _item_for_seller_a(catalog_client)
    ops = ops_headers(catalog_client)
    seller_b = seller_b_headers(catalog_client)
    buyer = buyer_headers(catalog_client)

    assert catalog_client.get("/v1/ops/order-items", headers=buyer).status_code == 403
    seller_a = seller_a_headers(catalog_client)
    assert catalog_client.get("/v1/ops/order-items", headers=seller_a).status_code == 403
    assert (
        catalog_client.get(
            f"/v1/order-items/{item_id}/internal-comments", headers=buyer
        ).status_code
        == 403
    )
    assert (
        catalog_client.post(
            f"/v1/order-items/{item_id}/internal-comments",
            json={"content": "nope"},
            headers=buyer,
        ).status_code
        == 403
    )
    assert (
        catalog_client.get(
            f"/v1/order-items/{item_id}/internal-comments", headers=seller_b
        ).status_code
        == 404
    )
    assert (
        catalog_client.post(
            f"/v1/order-items/{item_id}/internal-comments",
            json={"content": "nope"},
            headers=seller_b,
        ).status_code
        == 404
    )
    assert catalog_client.get(f"/v1/order-items/{item_id}", headers=ops).status_code == 403
    assert (
        catalog_client.patch(
            f"/v1/order-items/{item_id}", json={"status": "preparing"}, headers=ops
        ).status_code
        == 403
    )
    assert catalog_client.post(f"/v1/order-items/{item_id}/cancel", headers=ops).status_code == 403
    assert (
        catalog_client.post(
            "/v1/offers",
            json={"product_id": str(uuid4()), "price": "10.00", "stock": 1},
            headers=ops,
        ).status_code
        == 403
    )
    conversation = catalog_client.post(
        f"/v1/order-items/{item_id}/conversation",
        json={"reason": "atraso"},
        headers=ops,
    )
    assert conversation.status_code == 404


def test_ops_cannot_message_or_close_conversation(catalog_client: TestClient) -> None:
    item_id = _item_for_seller_a(catalog_client)
    opened = catalog_client.post(
        f"/v1/order-items/{item_id}/conversation",
        json={"reason": "atraso"},
        headers=buyer_headers(catalog_client),
    )
    assert opened.status_code == 201
    conversation_id = opened.json()["id"]
    ops = ops_headers(catalog_client)
    assert (
        catalog_client.get(f"/v1/conversations/{conversation_id}", headers=ops).status_code == 404
    )
    assert (
        catalog_client.get(f"/v1/conversations/{conversation_id}/messages", headers=ops).status_code
        == 404
    )
    assert (
        catalog_client.post(
            f"/v1/conversations/{conversation_id}/messages",
            json={"content": "hello"},
            headers=ops,
        ).status_code
        == 404
    )
    assert (
        catalog_client.post(f"/v1/conversations/{conversation_id}/close", headers=ops).status_code
        == 403
    )


def test_ops_list_filters_status_period_and_order_item_id(catalog_client: TestClient) -> None:
    product = _product(catalog_client)
    offer_a = _offer(catalog_client, product["id"], seller_a_headers(catalog_client))
    offer_b = _offer(
        catalog_client, product["id"], seller_b_headers(catalog_client), price="150.00"
    )
    placed = _checkout_item(catalog_client, offer_a["id"])
    other_seller = _checkout_item(catalog_client, offer_b["id"], price="150.00")
    preparing = _checkout_item(catalog_client, offer_a["id"])
    catalog_client.patch(
        f"/v1/order-items/{preparing['id']}",
        json={"status": "preparing"},
        headers=seller_a_headers(catalog_client),
    )
    ops = ops_headers(catalog_client)

    by_status = catalog_client.get("/v1/ops/order-items?status=preparing", headers=ops).json()
    assert [item["order_item_id"] for item in by_status["items"]] == [preparing["id"]]

    by_id = catalog_client.get(
        f"/v1/ops/order-items?order_item_id={placed['id']}", headers=ops
    ).json()
    assert [item["order_item_id"] for item in by_id["items"]] == [placed["id"]]

    other_filter = catalog_client.get(
        f"/v1/ops/order-items?order_item_id={other_seller['id']}", headers=ops
    ).json()
    assert [item["order_item_id"] for item in other_filter["items"]] == [other_seller["id"]]

    mismatch = catalog_client.get(
        f"/v1/ops/order-items?order_item_id={placed['id']}&status=preparing", headers=ops
    ).json()
    assert mismatch["items"] == []

    listed = catalog_client.get("/v1/ops/order-items", headers=ops).json()["items"]
    newer = listed[0]
    older = listed[-1]
    period = catalog_client.get(
        "/v1/ops/order-items",
        params={"from": older["created_at"], "to": newer["created_at"], "status": "placed"},
        headers=ops,
    ).json()
    period_ids = [item["order_item_id"] for item in period["items"]]
    assert placed["id"] in period_ids
    assert other_seller["id"] in period_ids
    assert preparing["id"] not in period_ids

    inverted = catalog_client.get(
        "/v1/ops/order-items",
        params={"from": newer["created_at"], "to": older["created_at"]},
        headers=ops,
    ).json()
    assert inverted["items"] == []


def test_ops_filters_by_public_number(catalog_client: TestClient) -> None:
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
    other = _checkout_item(catalog_client, offer_a["id"])
    ops = ops_headers(catalog_client)
    order_number = order["number"]
    line_a = next(item for item in order["items"] if item["offer_id"] == offer_a["id"])

    by_order = catalog_client.get(f"/v1/ops/order-items?number={order_number}", headers=ops).json()
    assert {item["order_item_id"] for item in by_order["items"]} == {
        item["id"] for item in order["items"]
    }
    assert other["id"] not in {item["order_item_id"] for item in by_order["items"]}

    by_line = catalog_client.get(
        f"/v1/ops/order-items?number={line_a['number']}", headers=ops
    ).json()
    assert [item["order_item_id"] for item in by_line["items"]] == [line_a["id"]]

    missing = catalog_client.get("/v1/ops/order-items?number=999999", headers=ops).json()
    assert missing["items"] == []
    invalid = catalog_client.get("/v1/ops/order-items?number=abc", headers=ops)
    assert invalid.status_code == 422
