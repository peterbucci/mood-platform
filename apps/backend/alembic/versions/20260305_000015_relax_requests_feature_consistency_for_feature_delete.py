"""relax requests feature consistency for feature deletion cleanup

Revision ID: 20260305_000015
Revises: 20260305_000014
Create Date: 2026-03-05 00:00:15.000000
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260305_000015"
down_revision: str | None = "20260305_000014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("ck_requests_feature_id_consistency", "requests", type_="check")
    op.create_check_constraint(
        "ck_requests_feature_id_consistency",
        "requests",
        "(status != 'pending' OR \"featureId\" IS NULL) "
        "AND (status != 'canceled' OR \"featureId\" IS NULL)",
    )


def downgrade() -> None:
    op.drop_constraint("ck_requests_feature_id_consistency", "requests", type_="check")
    op.create_check_constraint(
        "ck_requests_feature_id_consistency",
        "requests",
        "(status != 'pending' OR \"featureId\" IS NULL) "
        "AND (status != 'fulfilled' OR \"featureId\" IS NOT NULL)",
    )
