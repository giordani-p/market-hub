"""create catalog tables

Revision ID: 001_create_catalog
Revises:
Create Date: 2026-09-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "001_create_catalog"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sellers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "products",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(length=2000), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "offers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("seller_id", sa.Uuid(), nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("stock", sa.Integer(), nullable=False),
        sa.Column("available", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["seller_id"], ["sellers.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("offers")
    op.drop_table("products")
    op.drop_table("sellers")
