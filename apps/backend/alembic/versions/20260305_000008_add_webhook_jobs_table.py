"""add webhook jobs table for async ingestion processing

Revision ID: 20260305_000008
Revises: 20260305_000007
Create Date: 2026-03-05 00:00:08.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260305_000008"
down_revision: str | None = "20260305_000007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "webhook_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fitbit_user_id", sa.Text(), nullable=False),
        sa.Column("job_type", sa.Text(), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default=sa.text("'pending'")),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_webhook_jobs_status_created_at",
        "webhook_jobs",
        ["status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_webhook_jobs_user_status_created_at_desc",
        "webhook_jobs",
        ["user_id", "status", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_webhook_jobs_user_status_created_at_desc", table_name="webhook_jobs")
    op.drop_index("ix_webhook_jobs_status_created_at", table_name="webhook_jobs")
    op.drop_table("webhook_jobs")
