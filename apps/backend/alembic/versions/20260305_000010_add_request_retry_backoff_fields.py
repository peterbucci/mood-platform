"""add retry backoff fields to requests

Revision ID: 20260305_000010
Revises: 20260305_000009
Create Date: 2026-03-05 00:00:10.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260305_000010"
down_revision: str | None = "20260305_000009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "requests",
        sa.Column("attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column("requests", sa.Column("nextAttemptAt", sa.Integer(), nullable=True))
    op.add_column("requests", sa.Column("lastErrorCode", sa.Integer(), nullable=True))
    op.add_column("requests", sa.Column("lastErrorSignal", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("requests", "lastErrorSignal")
    op.drop_column("requests", "lastErrorCode")
    op.drop_column("requests", "nextAttemptAt")
    op.drop_column("requests", "attempts")
