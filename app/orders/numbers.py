"""Numero publico de Order e Order Item."""

import re

from sqlalchemy.sql import Select

from app.orders.models import Order, OrderItem

PUBLIC_NUMBER_PATTERN = re.compile(r"^(\d+)(?:-(\d+))?$")
PUBLIC_NUMBER_QUERY_PATTERN = r"^[0-9]+(-[0-9]+)?$"


def item_number(order_number: int, line: int) -> str:
    """Identificador publico do item, composto do pedido e da linha."""
    return f"{order_number}-{line}"


def parse_public_number(value: str) -> tuple[int, int | None]:
    """Interpreta '1042' ou '1042-1'. Levanta ValueError se o formato for invalido."""
    match = PUBLIC_NUMBER_PATTERN.fullmatch(value.strip())
    if match is None:
        raise ValueError("Invalid public order number")
    order_number = int(match.group(1))
    line_raw = match.group(2)
    line = int(line_raw) if line_raw is not None else None
    return order_number, line


def apply_public_number_filter(stmt: Select, public_number: str | None) -> Select:
    """Filtra por numero do pedido ou do item. Exige join com Order."""
    if not public_number:
        return stmt
    order_number, line = parse_public_number(public_number)
    stmt = stmt.where(Order.number == order_number)
    if line is not None:
        stmt = stmt.where(OrderItem.line == line)
    return stmt
