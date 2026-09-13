"""create communication tables

Revision ID: 004_create_communication
Revises: 003_add_user_name
Create Date: 2026-09-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "004_create_communication"
down_revision: str | None = "003_add_user_name"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("order_item_id", sa.Uuid(), nullable=False),
        sa.Column("reason", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_interaction_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["order_item_id"], ["order_items.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_conversations_order_item_id", "conversations", ["order_item_id"])
    op.create_index("ix_conversations_last_interaction_at", "conversations", ["last_interaction_at"])
    op.create_index(
        "uq_conversations_open_order_item",
        "conversations",
        ["order_item_id"],
        unique=True,
        postgresql_where=sa.text("status = 'open'"),
    )
    op.create_table(
        "messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("author_type", sa.String(length=20), nullable=False),
        sa.Column("author_user_id", sa.Uuid(), nullable=True),
        sa.Column("content", sa.String(length=2000), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["author_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_messages_conversation_created_at", "messages", ["conversation_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_messages_conversation_created_at", table_name="messages")
    op.drop_table("messages")
    op.drop_index("uq_conversations_open_order_item", table_name="conversations")
    op.drop_index("ix_conversations_last_interaction_at", table_name="conversations")
    op.drop_index("ix_conversations_order_item_id", table_name="conversations")
    op.drop_table("conversations")
