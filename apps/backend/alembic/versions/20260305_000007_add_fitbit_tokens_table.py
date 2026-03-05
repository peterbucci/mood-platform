"""add durable fitbit token storage

Revision ID: 20260305_000007
Revises: 20260304_000006
Create Date: 2026-03-05 00:00:07.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260305_000007"
down_revision: str | None = "20260304_000006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "fitbit_tokens",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fitbit_user_id", sa.Text(), nullable=True),
        sa.Column("access_token", sa.Text(), nullable=False),
        sa.Column("refresh_token", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scope", sa.Text(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_index("ix_fitbit_tokens_expires_at", "fitbit_tokens", ["expires_at"], unique=False)
    op.execute(
        """
        INSERT INTO fitbit_tokens (
            user_id,
            fitbit_user_id,
            access_token,
            refresh_token,
            expires_at,
            scope,
            updated_at
        )
        SELECT
            user_id,
            fitbit_user_id,
            access_token,
            refresh_token,
            expires_at,
            scope,
            updated_at
        FROM fitbit_oauth_connections
        """
    )


def downgrade() -> None:
    op.drop_index("ix_fitbit_tokens_expires_at", table_name="fitbit_tokens")
    op.drop_table("fitbit_tokens")
