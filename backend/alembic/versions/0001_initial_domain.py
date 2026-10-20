"""Initial durable NetPay domain schema.

Revision ID: 0001_initial_domain
Revises:
Create Date: 2026-10-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial_domain"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "merchant",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_merchant_name", "merchant", ["name"], unique=False)
    op.create_index("ix_merchant_status", "merchant", ["status"], unique=False)

    op.create_table(
        "m2mclient",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("client_id", sa.String(length=80), nullable=False),
        sa.Column("secret_hash", sa.String(length=255), nullable=False),
        sa.Column("scopes", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchant.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_m2mclient_merchant_id", "m2mclient", ["merchant_id"], unique=False)
    op.create_index("ix_m2mclient_client_id", "m2mclient", ["client_id"], unique=True)
    op.create_index("ix_m2mclient_status", "m2mclient", ["status"], unique=False)

    op.create_table(
        "darajaintegration",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("integration_id", sa.String(length=64), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("environment", sa.String(length=16), nullable=False),
        sa.Column("shortcode", sa.String(length=32), nullable=False),
        sa.Column("party_b_shortcode", sa.String(length=32), nullable=False),
        sa.Column("product_type", sa.String(length=24), nullable=False),
        sa.Column("consumer_key_ciphertext", sa.LargeBinary(), nullable=False),
        sa.Column("consumer_secret_ciphertext", sa.LargeBinary(), nullable=False),
        sa.Column("passkey_ciphertext", sa.LargeBinary(), nullable=False),
        sa.Column("credential_status", sa.String(length=24), nullable=False),
        sa.Column("c2b_enabled", sa.Boolean(), nullable=False),
        sa.Column("c2b_registration_status", sa.String(length=24), nullable=False),
        sa.Column("stk_callback_url", sa.String(length=512), nullable=False),
        sa.Column("c2b_validation_url", sa.String(length=512), nullable=False),
        sa.Column("c2b_confirmation_url", sa.String(length=512), nullable=False),
        sa.Column("registration_error", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchant.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("merchant_id", "shortcode", "environment", name="uq_integration_merchant_shortcode_env"),
    )
    op.create_index("ix_darajaintegration_integration_id", "darajaintegration", ["integration_id"], unique=True)
    op.create_index("ix_darajaintegration_merchant_id", "darajaintegration", ["merchant_id"], unique=False)
    op.create_index("ix_darajaintegration_shortcode", "darajaintegration", ["shortcode"], unique=False)
    op.create_index("ix_darajaintegration_credential_status", "darajaintegration", ["credential_status"], unique=False)

    op.create_table(
        "payment",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("integration_id", sa.Uuid(), nullable=False),
        sa.Column("client_reference", sa.String(length=100), nullable=False),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("phone_number", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("provider_checkout_request_id", sa.String(length=120), nullable=True),
        sa.Column("provider_merchant_request_id", sa.String(length=120), nullable=True),
        sa.Column("provider_receipt", sa.String(length=64), nullable=True),
        sa.Column("provider_result_code", sa.String(length=32), nullable=True),
        sa.Column("provider_result_description", sa.String(length=250), nullable=True),
        sa.Column("initiated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("amount_minor > 0", name="ck_payment_amount_positive"),
        sa.ForeignKeyConstraint(["integration_id"], ["darajaintegration.id"]),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchant.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("merchant_id", "client_reference", name="uq_payment_merchant_client_reference"),
    )
    for column in ("merchant_id", "integration_id", "status", "provider_checkout_request_id", "provider_merchant_request_id", "provider_receipt"):
        op.create_index(f"ix_payment_{column}", "payment", [column], unique=False)

    op.create_table(
        "idempotencyrecord",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.String(length=200), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("resource_id", sa.Uuid(), nullable=True),
        sa.Column("response_status", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchant.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("merchant_id", "key", name="uq_idempotency_merchant_key"),
    )
    op.create_index("ix_idempotencyrecord_merchant_id", "idempotencyrecord", ["merchant_id"], unique=False)
    op.create_index("ix_idempotencyrecord_resource_id", "idempotencyrecord", ["resource_id"], unique=False)
    op.create_index("ix_idempotencyrecord_expires_at", "idempotencyrecord", ["expires_at"], unique=False)

    op.create_table(
        "providercallback",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("integration_id", sa.Uuid(), nullable=False),
        sa.Column("payment_id", sa.Uuid(), nullable=True),
        sa.Column("callback_type", sa.String(length=32), nullable=False),
        sa.Column("dedupe_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("safe_payload", sa.JSON(), nullable=False),
        sa.Column("processing_status", sa.String(length=24), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["integration_id"], ["darajaintegration.id"]),
        sa.ForeignKeyConstraint(["payment_id"], ["payment.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("integration_id", "dedupe_fingerprint", name="uq_callback_integration_fingerprint"),
    )
    for column in ("integration_id", "payment_id", "callback_type", "processing_status"):
        op.create_index(f"ix_providercallback_{column}", "providercallback", [column], unique=False)

    op.create_table(
        "eventoutbox",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("aggregate_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("delivery_status", sa.String(length=24), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_error_code", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchant.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id"),
    )
    for column in ("event_id", "merchant_id", "aggregate_id", "event_type", "delivery_status", "next_attempt_at"):
        op.create_index(f"ix_eventoutbox_{column}", "eventoutbox", [column], unique=False)

    op.create_table(
        "paymentattempt",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("payment_id", sa.Uuid(), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("correlation_id", sa.Uuid(), nullable=False),
        sa.Column("outcome", sa.String(length=24), nullable=False),
        sa.Column("provider_result_code", sa.String(length=32), nullable=True),
        sa.Column("safe_error_code", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["payment_id"], ["payment.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("payment_id", "attempt_number", name="uq_payment_attempt_number"),
    )
    op.create_index("ix_paymentattempt_payment_id", "paymentattempt", ["payment_id"], unique=False)
    op.create_index("ix_paymentattempt_correlation_id", "paymentattempt", ["correlation_id"], unique=True)
    op.create_index("ix_paymentattempt_outcome", "paymentattempt", ["outcome"], unique=False)


def downgrade() -> None:
    for table, columns in (
        ("paymentattempt", ("payment_id", "correlation_id", "outcome")),
        ("eventoutbox", ("event_id", "merchant_id", "aggregate_id", "event_type", "delivery_status", "next_attempt_at")),
        ("providercallback", ("integration_id", "payment_id", "callback_type", "processing_status")),
        ("idempotencyrecord", ("merchant_id", "resource_id", "expires_at")),
        ("payment", ("merchant_id", "integration_id", "status", "provider_checkout_request_id", "provider_merchant_request_id", "provider_receipt")),
        ("darajaintegration", ("integration_id", "merchant_id", "shortcode", "credential_status")),
        ("m2mclient", ("merchant_id", "client_id", "status")),
        ("merchant", ("name", "status")),
    ):
        for column in columns:
            op.drop_index(f"ix_{table}_{column}", table_name=table)
    op.drop_table("paymentattempt")
    op.drop_table("eventoutbox")
    op.drop_table("providercallback")
    op.drop_table("idempotencyrecord")
    op.drop_table("payment")
    op.drop_table("darajaintegration")
    op.drop_table("m2mclient")
    op.drop_table("merchant")
