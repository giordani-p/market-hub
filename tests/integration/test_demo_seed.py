from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker

from app.auth.models import User
from app.auth.seed import BUYER_EMAIL, BUYER_ID, OPS_EMAIL, SELLER_A_EMAIL, SELLER_B_EMAIL
from app.catalog.models import Offer, Product
from app.catalog.seed import SELLER_A_ID, seed_demo
from app.communication.models import Conversation
from app.orders.models import Order, OrderItem
from tests.conftest import TEST_SEED_PASSWORD
from tests.integration.auth_helpers import buyer_headers, ops_headers, seller_a_headers


def _apply_demo(test_engine, password: str) -> None:
    factory = sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)
    with factory() as session:
        seed_demo(session, password)
        session.commit()


def test_demo_seed_populates_marketplace(catalog_client: TestClient, test_engine, settings) -> None:
    _apply_demo(test_engine, settings.seed_password)
    factory = sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)
    with factory() as session:
        user_count = session.scalar(select(func.count()).select_from(User))
        product_count = session.scalar(select(func.count()).select_from(Product))
        offer_sellers = set(session.scalars(select(Offer.seller_id).distinct()))
        statuses = set(session.scalars(select(OrderItem.status).distinct()))
        loja_a_items = session.scalar(
            select(func.count())
            .select_from(OrderItem)
            .join(Offer, OrderItem.offer_id == Offer.id)
            .where(Offer.seller_id == SELLER_A_ID)
        )
        buyer_orders = session.scalar(
            select(func.count()).select_from(Order).where(Order.buyer_id == BUYER_ID)
        )
        open_conversations = list(
            session.scalars(select(Conversation).where(Conversation.status == "open"))
        )
        now = datetime.now(UTC)

    assert user_count is not None and user_count >= 20
    assert product_count is not None and product_count >= 30
    assert len(offer_sellers) >= 8
    assert statuses == {"placed", "preparing", "in_transit", "delivered", "cancelled"}
    assert loja_a_items is not None and loja_a_items > 20
    assert buyer_orders is not None and buyer_orders >= 6
    assert any(row.calculated_priority == "high" for row in open_conversations)
    assert any(row.ops_override == "critical" for row in open_conversations)
    assert all(now - row.last_interaction_at < timedelta(hours=120) for row in open_conversations)


def test_demo_seed_is_idempotent(catalog_client: TestClient, test_engine, settings) -> None:
    _apply_demo(test_engine, settings.seed_password)
    factory = sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)
    with factory() as session:
        users_first = session.scalar(select(func.count()).select_from(User))
        items_first = session.scalar(select(func.count()).select_from(OrderItem))
        convs_first = session.scalar(select(func.count()).select_from(Conversation))
    _apply_demo(test_engine, settings.seed_password)
    with factory() as session:
        assert session.scalar(select(func.count()).select_from(User)) == users_first
        assert session.scalar(select(func.count()).select_from(OrderItem)) == items_first
        assert session.scalar(select(func.count()).select_from(Conversation)) == convs_first


def test_canonical_logins_work_after_demo_seed(
    catalog_client: TestClient, test_engine, settings
) -> None:
    _apply_demo(test_engine, settings.seed_password)
    for email in (SELLER_A_EMAIL, SELLER_B_EMAIL, BUYER_EMAIL, OPS_EMAIL):
        response = catalog_client.post(
            "/v1/auth/login",
            json={"email": email, "password": TEST_SEED_PASSWORD},
        )
        assert response.status_code == 200, response.text


def test_demo_dashboards_are_not_empty(catalog_client: TestClient, test_engine, settings) -> None:
    _apply_demo(test_engine, settings.seed_password)
    seller = catalog_client.get("/v1/dashboard", headers=seller_a_headers(catalog_client)).json()
    buyer = catalog_client.get("/v1/dashboard", headers=buyer_headers(catalog_client)).json()
    ops = catalog_client.get("/v1/dashboard", headers=ops_headers(catalog_client)).json()
    listed = catalog_client.get(
        "/v1/order-items",
        params={"page_size": 20},
        headers=seller_a_headers(catalog_client),
    ).json()

    assert seller["summary"]["total_order_items"] > 20
    assert seller["attention"]["open_conversations"] > 0
    assert buyer["summary"]["active_orders"] > 0
    assert buyer["recent"]["orders"]
    assert ops["summary"]["open_conversations"] > 0
    assert ops["attention"]["priority_queue_preview"]
    assert listed["total"] > 20
    assert len(listed["items"]) == 20
