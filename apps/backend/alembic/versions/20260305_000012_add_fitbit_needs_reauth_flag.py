"""add needs_reauth flag to fitbit tokens

Revision ID: 20260305_000012
Revises: 20260305_000011
Create Date: 2026-03-05 00:00:12.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260305_000012"
down_revision: str | None = "20260305_000011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "fitbit_tokens",
        sa.Column("needs_reauth", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )


def downgrade() -> None:
    op.drop_column("fitbit_tokens", "needs_reauth")
