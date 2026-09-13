from uuid import uuid4

from app.orders.access import buyer_item_statement, seller_item_statement


def test_seller_mutation_loader_locks_row() -> None:
    stmt = seller_item_statement(uuid4(), uuid4(), for_update=True)
    assert stmt._for_update_arg is not None


def test_seller_read_loader_does_not_lock_row() -> None:
    stmt = seller_item_statement(uuid4(), uuid4(), for_update=False)
    assert stmt._for_update_arg is None


def test_buyer_cancel_loader_locks_row() -> None:
    stmt = buyer_item_statement(uuid4(), uuid4(), for_update=True)
    assert stmt._for_update_arg is not None
