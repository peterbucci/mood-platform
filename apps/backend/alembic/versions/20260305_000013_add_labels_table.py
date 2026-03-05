"""add labels table linked to fulfilled request features

Revision ID: 20260305_000013
Revises: 20260305_000012
Create Date: 2026-03-05 00:00:13.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260305_000013"
down_revision: str | None = "20260305_000012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "labels",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("userId", sa.Text(), nullable=False),
        sa.Column("featureId", sa.Text(), nullable=False),
        sa.Column("requestId", sa.Text(), nullable=False),
        sa.Column("label", sa.Text(), nullable=True),
        sa.Column("emotionWord", sa.Text(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column(
            "createdAt",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "category IN ('energized','calm','stressed','tired')",
            name="ck_labels_category",
        ),
        sa.ForeignKeyConstraint(["featureId"], ["features.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requestId"], ["requests.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_labels_feature_id", "labels", ["featureId"], unique=False)
    op.create_index("ix_labels_request_id", "labels", ["requestId"], unique=False)
    op.create_index(
        "ix_labels_user_created_at_desc",
        "labels",
        ["userId", sa.text('"createdAt" DESC')],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_labels_user_created_at_desc", table_name="labels")
    op.drop_index("ix_labels_request_id", table_name="labels")
    op.drop_index("ix_labels_feature_id", table_name="labels")
    op.drop_table("labels")
