"""add integration settings table for fitbit oauth configuration

Revision ID: 20260309_000017
Revises: 20260307_000016
Create Date: 2026-03-09 00:00:17.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260309_000017"
down_revision: str | None = "20260307_000016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "integration_settings",
        sa.Column("id", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("fitbit_client_id", sa.Text(), nullable=True),
        sa.Column("fitbit_client_secret", sa.Text(), nullable=True),
        sa.Column("fitbit_redirect_uri", sa.Text(), nullable=True),
        sa.Column("fitbit_oauth_scope", sa.Text(), nullable=True),
        sa.Column("fitbit_subscriber_id", sa.Text(), nullable=True),
        sa.Column("fitbit_webhook_secret", sa.Text(), nullable=True),
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
        sa.CheckConstraint("id = 1", name="ck_integration_settings_singleton"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("integration_settings")
