"""Add encrypted server-side BFF sessions.

Revision ID: 0005_bff_sessions
Revises: 0004_merchant_member
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_bff_sessions"
down_revision: Union[str, None] = "0004_merchant_member"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "bffsession",
        sa.Column("session_id_hash", sa.String(length=64), primary_key=True, nullable=False),
        sa.Column("access_token_ciphertext", sa.Text(), nullable=False),
        sa.Column("refresh_token_ciphertext", sa.Text(), nullable=True),
        sa.Column("access_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_bffsession_expires_at", "bffsession", ["expires_at"])
    op.create_index("ix_bffsession_access_expires_at", "bffsession", ["access_expires_at"])


def downgrade() -> None:
    op.drop_index("ix_bffsession_access_expires_at", table_name="bffsession")
    op.drop_index("ix_bffsession_expires_at", table_name="bffsession")
    op.drop_table("bffsession")
