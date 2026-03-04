"""add features table for public feature API

Revision ID: 20260304_000004
Revises: 20260304_000003
Create Date: 2026-03-04 00:00:04.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260304_000004"
down_revision: str | None = "20260304_000003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "features",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("userId", sa.Text(), nullable=False),
        sa.Column("createdAt", sa.Integer(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("data", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_features_user_created_at_desc",
        "features",
        ["userId", "createdAt"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_features_user_created_at_desc", table_name="features")
    op.drop_table("features")
