"""per-tenant routing quality target

Revision ID: 20260930_0002
Revises: 20260916_0001
Create Date: 2026-09-30 00:00:00.000000

The learned router picks the cheapest operating point whose out-of-fold quality
meets the tenant's ``routing_quality_target``. The baseline revision builds the
schema from the live ORM models, so a database created from it already has the
column; only databases created before phase 3 need it added.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260930_0002"
down_revision = "20260916_0001"
branch_labels = None
depends_on = None

_TABLE = "tenant_policies"
_COLUMN = "routing_quality_target"


def _has_column() -> bool:
    columns = sa.inspect(op.get_bind()).get_columns(_TABLE)
    return any(column["name"] == _COLUMN for column in columns)


def upgrade() -> None:
    if _has_column():
        return
    with op.batch_alter_table(_TABLE) as batch:
        batch.add_column(sa.Column(_COLUMN, sa.Float(), nullable=False, server_default="0.95"))


def downgrade() -> None:
    if not _has_column():
        return
    with op.batch_alter_table(_TABLE) as batch:
        batch.drop_column(_COLUMN)
