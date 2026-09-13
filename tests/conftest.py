"""Fixtures compartilhadas pelos testes."""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import sessionmaker

from app.catalog.seed import seed_sellers
from app.core.config import Settings, get_settings
from app.database import get_engine, get_session, get_session_factory
from app.main import create_app

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def settings() -> Settings:
    return Settings(environment="local", api_prefix="/v1")


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    with TestClient(create_app(settings)) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def test_database_url() -> str:
    url = Settings(_env_file=ROOT / ".env").test_database_url
    if not url:
        pytest.fail(
            "TEST_DATABASE_URL is not set. Run `make db-up` and fill TEST_DATABASE_URL in .env."
        )
    return url


@pytest.fixture(scope="session")
def test_engine(test_database_url: str) -> Iterator[Engine]:
    original = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = test_database_url
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()
    try:
        command.upgrade(Config(str(ROOT / "alembic.ini")), "head")
        engine = create_engine(test_database_url, pool_pre_ping=True)
        yield engine
        engine.dispose()
    finally:
        if original is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = original
        get_settings.cache_clear()
        get_engine.cache_clear()
        get_session_factory.cache_clear()


@pytest.fixture
def catalog_client(settings: Settings, test_engine: Engine) -> Iterator[TestClient]:
    session_factory = sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)

    with session_factory() as session:
        session.execute(text("TRUNCATE offers, products, sellers RESTART IDENTITY CASCADE"))
        seed_sellers(session)
        session.commit()

    def override_get_session() -> Iterator[object]:
        session = session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    app = create_app(settings)
    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
