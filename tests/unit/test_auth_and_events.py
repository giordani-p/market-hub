from uuid import uuid4

from app.auth.models import User, UserRole
from app.auth.passwords import hash_password, verify_password
from app.auth.tokens import create_access_token, decode_access_token
from app.core.config import Settings
from app.core.events import PENDING_KEY, OrderCreated, publish_pending, publisher, record_event


class _FakeSession:
    def __init__(self) -> None:
        self.info: dict = {}


def test_password_hash_roundtrip() -> None:
    hashed = hash_password("secret-value")
    assert hashed != "secret-value"
    assert verify_password("secret-value", hashed)
    assert not verify_password("other", hashed)


def test_jwt_roundtrip() -> None:
    settings = Settings(jwt_secret="unit-secret-which-is-long-enough-32b", _env_file=None)
    user = User(
        id=uuid4(),
        email="buyer@example.com",
        name="Buyer Demo",
        password_hash="hash",
        role=UserRole.BUYER,
        seller_id=None,
    )
    token = create_access_token(user, settings)
    assert decode_access_token(token, settings) == user.id


def test_events_are_not_published_until_commit_hook() -> None:
    publisher.clear()
    session = _FakeSession()
    record_event(session, OrderCreated(order_id=uuid4(), buyer_id=uuid4()))  # type: ignore[arg-type]
    assert publisher.events == []
    assert len(session.info[PENDING_KEY]) == 1
    publish_pending(session)  # type: ignore[arg-type]
    assert len(publisher.events) == 1
    assert PENDING_KEY not in session.info
