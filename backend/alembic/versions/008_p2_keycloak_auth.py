"""P2 #25: keycloak_id on users; hashed_password nullable (SSO hard cut).

Revision ID: 008
Revises: 007
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("keycloak_id", sa.Uuid(), nullable=True))
        batch.alter_column(
            "hashed_password",
            existing_type=sa.String(),
            nullable=True,
        )
        batch.create_index("ix_users_keycloak_id", ["keycloak_id"], unique=True)


def downgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.drop_index("ix_users_keycloak_id")
        batch.drop_column("keycloak_id")
        batch.alter_column(
            "hashed_password",
            existing_type=sa.String(),
            nullable=False,
        )
