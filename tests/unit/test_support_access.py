from uuid import uuid4

from app.support.access import ops_conversation_statement


def test_ops_conversation_loader_locks_on_mutation() -> None:
    stmt = ops_conversation_statement(uuid4(), for_update=True)
    assert stmt._for_update_arg is not None


def test_ops_conversation_loader_does_not_lock_on_read() -> None:
    stmt = ops_conversation_statement(uuid4(), for_update=False)
    assert stmt._for_update_arg is None
