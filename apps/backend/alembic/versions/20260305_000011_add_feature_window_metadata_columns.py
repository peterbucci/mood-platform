"""add source timezone and window metadata columns to features

Revision ID: 20260305_000011
Revises: 20260305_000010
Create Date: 2026-03-05 00:00:11.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260305_000011"
down_revision: str | None = "20260305_000010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("features", sa.Column("sourceTimezone", sa.Text(), nullable=True))
    op.add_column(
        "features",
        sa.Column("windowStart", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "features",
        sa.Column("windowEnd", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("features", "windowEnd")
    op.drop_column("features", "windowStart")
    op.drop_column("features", "sourceTimezone")
