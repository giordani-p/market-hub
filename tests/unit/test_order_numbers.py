"""Numero publico de Order e Order Item."""

from uuid import UUID

import pytest

from app.orders.numbers import item_number, parse_public_number
from app.orders.seed import assert_unique_demo_order_ids, item_id, public_item_number


def test_item_number_composes_order_and_line() -> None:
    assert item_number(1042, 1) == "1042-1"
    assert item_number(1001, 3) == "1001-3"


def test_parse_public_number_accepts_order_and_item() -> None:
    assert parse_public_number("1042") == (1042, None)
    assert parse_public_number("1042-1") == (1042, 1)
    assert parse_public_number(" 1001-2 ") == (1001, 2)


def test_parse_public_number_rejects_invalid_format() -> None:
    with pytest.raises(ValueError, match="Invalid public order number"):
        parse_public_number("abc")
    with pytest.raises(ValueError, match="Invalid public order number"):
        parse_public_number("1042-")
    with pytest.raises(ValueError, match="Invalid public order number"):
        parse_public_number("")


def test_public_item_number_follows_demo_orders_table() -> None:
    assert public_item_number(6) == "1003-1"
    assert public_item_number(2) == "1001-2"
    with pytest.raises(RuntimeError, match="Order item 99999"):
        public_item_number(99999)


def test_demo_item_uuid_is_determined_by_order_and_line() -> None:
    assert_unique_demo_order_ids()
    assert item_id(1) == UUID("01000004-0000-4000-8000-000001000001")
    assert item_id(2) == UUID("01000004-0000-4000-8000-000001000002")
    assert item_id(6) == UUID("01000004-0000-4000-8000-000003000001")
    assert item_id(1) != item_id(6)
