"""per-tenant requests-per-minute limit

Revision ID: 20260930_0003
Revises: 20260930_0002
Create Date: 2026-09-30 12:00:00.000000

Nullable: no value means no limit, which is every tenant's behaviour before
phase 5. As with 0002, a database built from the baseline revision already
has the column.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260930_0003"
down_revision = "20260930_0002"
branch_labels = None
depends_on = None

_TABLE = "tenant_policies"
_COLUMN = "rate_limit_requests_per_minute"


def _has_column() -> bool:
    columns = sa.inspect(op.get_bind()).get_columns(_TABLE)
    return any(column["name"] == _COLUMN for column in columns)


def upgrade() -> None:
    if _has_column():
        return
    with op.batch_alter_table(_TABLE) as batch:
        batch.add_column(sa.Column(_COLUMN, sa.Integer(), nullable=True))


def downgrade() -> None:
    if not _has_column():
        return
    with op.batch_alter_table(_TABLE) as batch:
        batch.drop_column(_COLUMN)
