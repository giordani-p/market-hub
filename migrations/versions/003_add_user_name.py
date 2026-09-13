"""add users.name

Revision ID: 003_add_user_name
Revises: 002_create_auth_and_orders
Create Date: 2026-09-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "003_add_user_name"
down_revision: str | None = "002_create_auth_and_orders"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("name", sa.String(length=200), nullable=True))
    op.execute(sa.text("UPDATE users SET name = email WHERE name IS NULL"))
    op.alter_column("users", "name", existing_type=sa.String(length=200), nullable=False)


def downgrade() -> None:
    op.drop_column("users", "name")
