"""add worker locks table for fulfillment coordination

Revision ID: 20260304_000005
Revises: 20260304_000004
Create Date: 2026-03-04 00:00:05.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260304_000005"
down_revision: str | None = "20260304_000004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "worker_locks",
        sa.Column("lock_key", sa.Text(), nullable=False),
        sa.Column("owner_id", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("lock_key"),
    )
    op.create_index("ix_worker_locks_expires_at", "worker_locks", ["expires_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_worker_locks_expires_at", table_name="worker_locks")
    op.drop_table("worker_locks")
