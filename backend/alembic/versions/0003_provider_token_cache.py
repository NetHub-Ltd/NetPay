"""Add encrypted shared Daraja access-token cache fields.

Revision ID: 0003_provider_token_cache
Revises: 0002_full_domain_schema
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003_provider_token_cache"
down_revision: Union[str, None] = "0002_full_domain_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add nullable encrypted token and expiry columns without rewriting prior revisions."""
    op.add_column(
        "providerintegration",
        sa.Column("provider_access_token_ciphertext", sa.LargeBinary(), nullable=True),
    )
    op.add_column(
        "providerintegration",
        sa.Column("provider_token_expires_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Remove the token cache fields; provider credentials remain unchanged."""
    op.drop_column("providerintegration", "provider_token_expires_at")
    op.drop_column("providerintegration", "provider_access_token_ciphertext")
