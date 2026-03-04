"""add Fitbit OAuth state and token tables

Revision ID: 20260304_000006
Revises: 20260304_000005
Create Date: 2026-03-04 00:00:06.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260304_000006"
down_revision: str | None = "20260304_000005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "fitbit_oauth_states",
        sa.Column("state", sa.Text(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("state"),
    )
    op.create_index(
        "ix_fitbit_oauth_states_expires_at",
        "fitbit_oauth_states",
        ["expires_at"],
        unique=False,
    )

    op.create_table(
        "fitbit_oauth_connections",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fitbit_user_id", sa.Text(), nullable=False),
        sa.Column("access_token", sa.Text(), nullable=False),
        sa.Column("refresh_token", sa.Text(), nullable=False),
        sa.Column("scope", sa.Text(), nullable=False),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_index(
        "ix_fitbit_oauth_connections_expires_at",
        "fitbit_oauth_connections",
        ["expires_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_fitbit_oauth_connections_expires_at", table_name="fitbit_oauth_connections")
    op.drop_table("fitbit_oauth_connections")

    op.drop_index("ix_fitbit_oauth_states_expires_at", table_name="fitbit_oauth_states")
    op.drop_table("fitbit_oauth_states")
