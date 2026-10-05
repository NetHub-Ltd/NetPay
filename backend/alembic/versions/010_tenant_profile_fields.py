"""Add business profile fields on tenants.

Revision ID: 010
Revises: 009
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("category", sa.String(length=64), nullable=True))
    op.add_column("tenants", sa.Column("email", sa.String(length=255), nullable=True))
    op.add_column("tenants", sa.Column("phone_number", sa.String(length=32), nullable=True))


def downgrade() -> None:
    op.drop_column("tenants", "phone_number")
    op.drop_column("tenants", "email")
    op.drop_column("tenants", "category")
