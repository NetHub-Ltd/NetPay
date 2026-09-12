"""P1-B: reconciliation_exceptions

Revision ID: 005
Revises: 004
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reconciliation_exceptions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=True),
        sa.Column("payment_intent_id", sa.Uuid(), nullable=True),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("provider_ref", sa.String(128), nullable=True),
        sa.Column("message", sa.String(512), nullable=False),
        sa.Column("details_json", sa.Text(), nullable=True),
        sa.Column("resolved_note", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["payment_intent_id"], ["payment_intents.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_recon_exceptions_status", "reconciliation_exceptions", ["status"])
    op.create_index("ix_recon_exceptions_kind", "reconciliation_exceptions", ["kind"])
    op.create_index("ix_recon_exceptions_tenant", "reconciliation_exceptions", ["tenant_id"])
    op.create_index("ix_recon_exceptions_intent", "reconciliation_exceptions", ["payment_intent_id"])
    op.create_index("ix_recon_exceptions_provider_ref", "reconciliation_exceptions", ["provider_ref"])


def downgrade() -> None:
    op.drop_table("reconciliation_exceptions")
