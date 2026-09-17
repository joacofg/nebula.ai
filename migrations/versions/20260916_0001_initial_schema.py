"""initial schema

Revision ID: 20260916_0001
Revises:
Create Date: 2026-09-16 00:00:00.000000

Single baseline derived from ``nebula.db.models.Base``. The ORM models are the
schema's source of truth; ``alembic revision --autogenerate`` builds on top of
this revision for future changes.
"""

from __future__ import annotations

from alembic import op

from nebula.db.models import Base

revision = "20260916_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
