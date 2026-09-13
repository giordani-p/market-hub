"""add conversation priority columns

Revision ID: 006_add_conversation_priority
Revises: 005_create_support
Create Date: 2026-09-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "006_add_conversation_priority"
down_revision: str | None = "005_create_support"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "conversations",
        sa.Column(
            "calculated_priority",
            sa.String(length=20),
            nullable=False,
            server_default="low",
        ),
    )
    op.add_column("conversations", sa.Column("ops_override", sa.String(length=20), nullable=True))
    op.alter_column("conversations", "calculated_priority", server_default=None)


def downgrade() -> None:
    op.drop_column("conversations", "ops_override")
    op.drop_column("conversations", "calculated_priority")
