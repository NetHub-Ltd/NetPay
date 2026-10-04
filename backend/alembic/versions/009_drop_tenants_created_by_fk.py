"""Ensure tenants.created_by has no FK to local users (NetHub principal ids).

Revision ID: 009
Revises: 008
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    if dialect == "postgresql":
        # Idempotent — production may still have this constraint if 008 never applied.
        op.execute("ALTER TABLE tenants DROP CONSTRAINT IF EXISTS tenants_created_by_fkey")
        op.execute(
            "ALTER TABLE users ALTER COLUMN hashed_password DROP NOT NULL"
        )


def downgrade() -> None:
    # Do not re-add FK: identity is NetHub; local users row may not exist.
    pass
