"""add public order numbers

Revision ID: 009_add_order_public_numbers
Revises: 008_create_notifications
Create Date: 2026-09-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "009_add_order_public_numbers"
down_revision: str | None = "008_create_notifications"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(sa.text("CREATE SEQUENCE order_number_seq START 1001"))
    op.add_column("orders", sa.Column("number", sa.Integer(), nullable=True))
    op.add_column("order_items", sa.Column("line", sa.Integer(), nullable=True))
    op.execute(
        sa.text(
            """
            WITH numbered AS (
                SELECT id, 1000 + row_number() OVER (ORDER BY created_at, id) AS n
                FROM orders
            )
            UPDATE orders SET number = numbered.n FROM numbered WHERE orders.id = numbered.id
            """
        )
    )
    op.execute(
        sa.text(
            """
            WITH numbered AS (
                SELECT id, row_number() OVER (PARTITION BY order_id ORDER BY created_at, id) AS n
                FROM order_items
            )
            UPDATE order_items SET line = numbered.n FROM numbered WHERE order_items.id = numbered.id
            """
        )
    )
    op.alter_column("orders", "number", existing_type=sa.Integer(), nullable=False)
    op.alter_column("order_items", "line", existing_type=sa.Integer(), nullable=False)
    op.create_unique_constraint("uq_orders_number", "orders", ["number"])
    op.create_unique_constraint("uq_order_items_order_id_line", "order_items", ["order_id", "line"])
    op.execute(sa.text("ALTER SEQUENCE order_number_seq OWNED BY orders.number"))
    op.execute(sa.text("ALTER TABLE orders ALTER COLUMN number SET DEFAULT nextval('order_number_seq')"))
    op.execute(
        sa.text("SELECT setval('order_number_seq', (SELECT COALESCE(MAX(number), 1000) FROM orders))")
    )


def downgrade() -> None:
    op.execute(sa.text("ALTER TABLE orders ALTER COLUMN number DROP DEFAULT"))
    op.drop_constraint("uq_order_items_order_id_line", "order_items", type_="unique")
    op.drop_constraint("uq_orders_number", "orders", type_="unique")
    op.drop_column("order_items", "line")
    op.drop_column("orders", "number")
    op.execute(sa.text("DROP SEQUENCE IF EXISTS order_number_seq"))
