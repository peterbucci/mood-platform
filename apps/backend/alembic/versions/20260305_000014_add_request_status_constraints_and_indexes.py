"""add request status constraints and indexes

Revision ID: 20260305_000014
Revises: 20260305_000013
Create Date: 2026-03-05 00:00:14.000000
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260305_000014"
down_revision: str | None = "20260305_000013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_requests_status",
        "requests",
        "status IN ('pending','fulfilled','canceled')",
    )
    op.create_check_constraint(
        "ck_requests_feature_id_consistency",
        "requests",
        "(status != 'pending' OR \"featureId\" IS NULL) "
        "AND (status != 'fulfilled' OR \"featureId\" IS NOT NULL)",
    )
    op.create_index("ix_requests_status", "requests", ["status"], unique=False)
    op.create_index("ix_requests_user_status", "requests", ["userId", "status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_requests_user_status", table_name="requests")
    op.drop_index("ix_requests_status", table_name="requests")
    op.drop_constraint("ck_requests_feature_id_consistency", "requests", type_="check")
    op.drop_constraint("ck_requests_status", "requests", type_="check")
