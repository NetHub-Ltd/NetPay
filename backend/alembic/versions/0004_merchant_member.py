"""Add merchant_member for NetHubKe user → NetPay merchant ACL.

Revision ID: 0004_merchant_member
Revises: 0003_mpesa_core_capabilities
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0004_merchant_member"
down_revision: Union[str, None] = "0003_mpesa_core_capabilities"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "merchant_member",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("merchant_id", UUID(as_uuid=True), sa.ForeignKey("merchant.id"), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False, server_default="member"),
        sa.UniqueConstraint("user_id", "merchant_id", name="uq_merchant_member_user_merchant"),
    )
    op.create_index("ix_merchant_member_user_id", "merchant_member", ["user_id"])
    op.create_index("ix_merchant_member_merchant_id", "merchant_member", ["merchant_id"])
    op.create_index("ix_merchant_member_role", "merchant_member", ["role"])


def downgrade() -> None:
    op.drop_index("ix_merchant_member_role", table_name="merchant_member")
    op.drop_index("ix_merchant_member_merchant_id", table_name="merchant_member")
    op.drop_index("ix_merchant_member_user_id", table_name="merchant_member")
    op.drop_table("merchant_member")
