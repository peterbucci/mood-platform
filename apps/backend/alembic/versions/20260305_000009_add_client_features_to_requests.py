"""add optional clientFeatures payload to requests

Revision ID: 20260305_000009
Revises: 20260305_000008
Create Date: 2026-03-05 00:00:09.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260305_000009"
down_revision: str | None = "20260305_000008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("requests", sa.Column("clientFeatures", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("requests", "clientFeatures")
