"""Identity via NetHub: drop users FK on tenants.created_by; nullable hashed_password.

Revision ID: 008
Revises: 007
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    if dialect == "postgresql":
        op.execute("ALTER TABLE tenants DROP CONSTRAINT IF EXISTS tenants_created_by_fkey")
        op.execute("ALTER TABLE users ALTER COLUMN hashed_password DROP NOT NULL")


def downgrade() -> None:
    pass
