"""Add initiator credentials and explicit per-integration Daraja capabilities.

Revision ID: 0003_mpesa_core_capabilities
Revises: 0002_full_domain_schema
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0003_mpesa_core_capabilities"
down_revision: Union[str, None] = "0002_full_domain_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add optional API-user credential material and a safe capability allowlist."""
    op.add_column("providerintegration", sa.Column("initiator_name", sa.String(length=80), nullable=True))
    op.add_column(
        "providerintegration",
        sa.Column("initiator_password_ciphertext", sa.LargeBinary(), nullable=True),
    )
    op.add_column(
        "providerintegration",
        sa.Column(
            "enabled_capabilities",
            postgresql.JSON(astext_type=sa.Text()),
            server_default=sa.text("""'["stk_push"]'"""),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Remove only the additive Core fields introduced by this revision."""
    op.drop_column("providerintegration", "enabled_capabilities")
    op.drop_column("providerintegration", "initiator_password_ciphertext")
    op.drop_column("providerintegration", "initiator_name")
