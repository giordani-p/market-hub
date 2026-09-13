"""add priority stale detection stamps

Revision ID: 007_add_priority_stale_stamps
Revises: 006_add_conversation_priority
Create Date: 2026-09-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "007_add_priority_stale_stamps"
down_revision: str | None = "006_add_conversation_priority"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "conversations",
        sa.Column("priority_calculated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "order_items",
        sa.Column("status_updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute("UPDATE order_items SET status_updated_at = updated_at")
    op.alter_column("order_items", "status_updated_at", nullable=False)


def downgrade() -> None:
    op.drop_column("order_items", "status_updated_at")
    op.drop_column("conversations", "priority_calculated_at")
