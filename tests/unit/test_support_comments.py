from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.auth.models import User, UserRole
from app.communication.lifecycle import author_type_for as conversation_author_type_for
from app.core.errors import ForbiddenError
from app.support.comments import author_type_for
from app.support.schemas import CreateInternalCommentRequest


def test_content_is_stripped_and_blank_rejected() -> None:
    assert CreateInternalCommentRequest(content="  hello  ").content == "hello"
    with pytest.raises(ValidationError):
        CreateInternalCommentRequest(content="   ")
    with pytest.raises(ValidationError):
        CreateInternalCommentRequest(content="")
    with pytest.raises(ValidationError):
        CreateInternalCommentRequest(content="x" * 2001)


def test_comment_author_type_for_seller_and_ops() -> None:
    seller = User(
        id=uuid4(), email="s@example.com", name="S", password_hash="h", role=UserRole.SELLER
    )
    ops = User(id=uuid4(), email="o@example.com", name="O", password_hash="h", role=UserRole.OPS)
    buyer = User(
        id=uuid4(), email="b@example.com", name="B", password_hash="h", role=UserRole.BUYER
    )
    assert author_type_for(seller) == "seller"
    assert author_type_for(ops) == "ops"
    with pytest.raises(ForbiddenError):
        author_type_for(buyer)


def test_conversation_author_type_rejects_ops() -> None:
    ops = User(id=uuid4(), email="o@example.com", name="O", password_hash="h", role=UserRole.OPS)
    buyer = User(
        id=uuid4(), email="b@example.com", name="B", password_hash="h", role=UserRole.BUYER
    )
    seller = User(
        id=uuid4(), email="s@example.com", name="S", password_hash="h", role=UserRole.SELLER
    )
    assert conversation_author_type_for(buyer) == "buyer"
    assert conversation_author_type_for(seller) == "seller"
    with pytest.raises(ForbiddenError):
        conversation_author_type_for(ops)
