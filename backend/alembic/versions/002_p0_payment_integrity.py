"""P0: amount_minor, idempotency_key, unique provider_checkout_id

Revision ID: 002
Revises: 001
Create Date: 2026-09-12
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "payment_intents",
        sa.Column("amount_minor", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "payment_intents",
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
    )
    # Backfill minor units: KES amount * 100
    op.execute(
        sa.text(
            "UPDATE payment_intents SET amount_minor = CAST(ROUND(CAST(amount AS REAL) * 100) AS INTEGER) "
            "WHERE amount_minor = 0"
        )
    )
    op.create_index(
        "ix_payment_intents_idempotency_key",
        "payment_intents",
        ["idempotency_key"],
        unique=False,
    )
    # Unique (tenant_id, idempotency_key) — multiple NULLs allowed on SQLite/Postgres
    op.create_index(
        "uq_payment_intents_tenant_idempotency",
        "payment_intents",
        ["tenant_id", "idempotency_key"],
        unique=True,
    )
    # Unique checkout id (NULLs distinct on SQLite/Postgres unique)
    op.drop_index("ix_payment_intents_provider_checkout_id", table_name="payment_intents")
    op.create_index(
        "uq_payment_intents_provider_checkout_id",
        "payment_intents",
        ["provider_checkout_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_payment_intents_provider_checkout_id", table_name="payment_intents")
    op.create_index(
        "ix_payment_intents_provider_checkout_id",
        "payment_intents",
        ["provider_checkout_id"],
        unique=False,
    )
    op.drop_index("uq_payment_intents_tenant_idempotency", table_name="payment_intents")
    op.drop_index("ix_payment_intents_idempotency_key", table_name="payment_intents")
    op.drop_column("payment_intents", "idempotency_key")
    op.drop_column("payment_intents", "amount_minor")
