"""S1: STK request/response on intent, status callback, outbound payment_intent_id

Revision ID: 007
Revises: 006
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("payment_intents", sa.Column("stk_request_json", sa.Text(), nullable=True))
    op.add_column("payment_intents", sa.Column("stk_response_json", sa.Text(), nullable=True))
    op.add_column("payment_intents", sa.Column("status_callback_url", sa.String(length=1024), nullable=True))
    op.add_column("payment_intents", sa.Column("metadata_json", sa.Text(), nullable=True))
    op.add_column("outbound_requests", sa.Column("payment_intent_id", sa.Uuid(), nullable=True))
    op.create_index("ix_outbound_requests_payment_intent_id", "outbound_requests", ["payment_intent_id"])


def downgrade() -> None:
    op.drop_index("ix_outbound_requests_payment_intent_id", table_name="outbound_requests")
    op.drop_column("outbound_requests", "payment_intent_id")
    op.drop_column("payment_intents", "metadata_json")
    op.drop_column("payment_intents", "status_callback_url")
    op.drop_column("payment_intents", "stk_response_json")
    op.drop_column("payment_intents", "stk_request_json")
