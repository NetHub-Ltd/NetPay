"""Expand the clean foundation to the complete 16-table NetPay domain schema.

Revision ID: 0002_full_domain_schema
Revises: 0001_initial_schema

The first revision is retained unchanged. This revision adds the remaining
domain records and expands existing tables without dropping existing data.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002_full_domain_schema"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = postgresql.UUID(as_uuid=True)
AWARE_DATETIME = sa.DateTime(timezone=True)
JSON = sa.JSON()


def _common_columns() -> list[sa.Column]:
    """Return fresh shared columns for a new table."""
    return [
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("created_at", AWARE_DATETIME, nullable=False),
        sa.Column("updated_at", AWARE_DATETIME, nullable=False),
        sa.Column("deleted_at", AWARE_DATETIME, nullable=True),
    ]


def upgrade() -> None:
    # Expand merchant profile fields without rewriting the first revision.
    op.add_column("merchant", sa.Column("contact_email", sa.String(254), nullable=True))
    op.add_column("merchant", sa.Column("contact_phone", sa.String(20), nullable=True))
    op.add_column("merchant", sa.Column("attributes", JSON, server_default=sa.text("'{}'"), nullable=False))

    # Keep the initial provider integration columns for a lossless upgrade.
    # New Daraja-specific fields are nullable until onboarding validates them.
    op.add_column("providerintegration", sa.Column("integration_id", sa.String(64), nullable=True))
    op.execute(sa.text("UPDATE providerintegration SET integration_id = 'int_' || REPLACE(CAST(id AS VARCHAR), '-', '') WHERE integration_id IS NULL"))
    op.alter_column("providerintegration", "integration_id", existing_type=sa.String(64), nullable=False)
    op.create_unique_constraint("uq_providerintegration_integration_id", "providerintegration", ["integration_id"])
    op.add_column("providerintegration", sa.Column("shortcode", sa.String(32), nullable=True))
    op.add_column("providerintegration", sa.Column("party_b_shortcode", sa.String(32), nullable=True))
    op.add_column("providerintegration", sa.Column("product_type", sa.String(24), nullable=True))
    op.add_column("providerintegration", sa.Column("consumer_key_ciphertext", sa.LargeBinary(), nullable=True))
    op.add_column("providerintegration", sa.Column("consumer_secret_ciphertext", sa.LargeBinary(), nullable=True))
    op.add_column("providerintegration", sa.Column("passkey_ciphertext", sa.LargeBinary(), nullable=True))
    op.add_column("providerintegration", sa.Column("credential_status", sa.String(24), server_default="pending", nullable=False))
    op.add_column("providerintegration", sa.Column("credentials_validated_at", AWARE_DATETIME, nullable=True))
    op.add_column("providerintegration", sa.Column("credential_version", sa.Integer(), server_default="1", nullable=False))
    op.add_column("providerintegration", sa.Column("c2b_enabled", sa.Boolean(), server_default=sa.false(), nullable=False))
    op.add_column("providerintegration", sa.Column("c2b_registration_status", sa.String(24), server_default="not_requested", nullable=False))
    op.add_column("providerintegration", sa.Column("stk_callback_url", sa.String(512), nullable=True))
    op.add_column("providerintegration", sa.Column("c2b_validation_url", sa.String(512), nullable=True))
    op.add_column("providerintegration", sa.Column("c2b_confirmation_url", sa.String(512), nullable=True))
    op.add_column("providerintegration", sa.Column("c2b_registered_at", AWARE_DATETIME, nullable=True))
    op.add_column("providerintegration", sa.Column("registration_error", sa.String(500), nullable=True))
    op.create_index("ix_providerintegration_merchant_id", "providerintegration", ["merchant_id"])
    op.create_index("ix_providerintegration_shortcode", "providerintegration", ["shortcode"])
    op.create_index("ix_providerintegration_credential_status", "providerintegration", ["credential_status"])

    # Add payment request identity and provider evidence fields.
    op.add_column("payment", sa.Column("phone_number", sa.String(20), nullable=True))
    op.add_column("payment", sa.Column("payment_source", sa.String(16), server_default="stk", nullable=False))
    op.add_column("payment", sa.Column("provider_checkout_request_id", sa.String(120), nullable=True))
    op.add_column("payment", sa.Column("provider_merchant_request_id", sa.String(120), nullable=True))
    op.add_column("payment", sa.Column("provider_receipt", sa.String(64), nullable=True))
    op.add_column("payment", sa.Column("provider_result_code", sa.String(32), nullable=True))
    op.add_column("payment", sa.Column("provider_result_description", sa.String(250), nullable=True))
    op.add_column("payment", sa.Column("initiated_at", AWARE_DATETIME, nullable=True))
    op.add_column("payment", sa.Column("completed_at", AWARE_DATETIME, nullable=True))
    op.add_column("payment", sa.Column("cancelled_at", AWARE_DATETIME, nullable=True))
    op.create_index("ix_payment_merchant_id", "payment", ["merchant_id"])
    op.create_index("ix_payment_integration_id", "payment", ["integration_id"])
    op.create_index("ix_payment_payment_source", "payment", ["payment_source"])
    op.create_index("ix_payment_status", "payment", ["status"])
    op.create_index("ix_payment_provider_transaction_id", "payment", ["provider_transaction_id"])
    op.create_index("ix_payment_provider_checkout_request_id", "payment", ["provider_checkout_request_id"])
    op.create_index("ix_payment_provider_merchant_request_id", "payment", ["provider_merchant_request_id"])
    op.create_index("ix_payment_provider_receipt", "payment", ["provider_receipt"])
    op.create_unique_constraint("uq_payment_integration_provider_receipt", "payment", ["integration_id", "provider_receipt"])
    op.create_unique_constraint("uq_payment_integration_checkout", "payment", ["integration_id", "provider_checkout_request_id"])
    op.create_unique_constraint("uq_payment_integration_merchant_request", "payment", ["integration_id", "provider_merchant_request_id"])

    # Add correlation and sanitized error fields to attempts.
    op.add_column("paymentattempt", sa.Column("correlation_id", UUID, nullable=True))
    op.execute(sa.text("UPDATE paymentattempt SET correlation_id = id WHERE correlation_id IS NULL"))
    op.alter_column("paymentattempt", "correlation_id", existing_type=UUID, nullable=False)
    op.create_unique_constraint("uq_paymentattempt_correlation_id", "paymentattempt", ["correlation_id"])
    op.add_column("paymentattempt", sa.Column("provider_result_code", sa.String(32), nullable=True))
    op.add_column("paymentattempt", sa.Column("safe_error_code", sa.String(100), nullable=True))
    op.add_column("paymentattempt", sa.Column("safe_error_message", sa.String(500), nullable=True))
    op.create_index("ix_paymentattempt_payment_id", "paymentattempt", ["payment_id"])
    op.create_index("ix_paymentattempt_status", "paymentattempt", ["status"])

    # New machine-to-machine client credentials are merchant-scoped.
    op.create_table(
        "m2mclient",
        *_common_columns(),
        sa.Column("merchant_id", UUID, sa.ForeignKey("merchant.id"), nullable=False),
        sa.Column("client_id", sa.String(80), nullable=False),
        sa.Column("secret_hash", sa.String(255), nullable=False),
        sa.Column("scopes", JSON, nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("last_used_at", AWARE_DATETIME, nullable=True),
        sa.Column("expires_at", AWARE_DATETIME, nullable=True),
        sa.Column("revoked_at", AWARE_DATETIME, nullable=True),
        sa.UniqueConstraint("client_id", name="uq_m2mclient_client_id"),
    )
    op.create_index("ix_m2mclient_merchant_id", "m2mclient", ["merchant_id"])
    op.create_index("ix_m2mclient_status", "m2mclient", ["status"])
    op.create_index("ix_m2mclient_expires_at", "m2mclient", ["expires_at"])


    # Tie idempotency records to the calling client and resulting resource.
    op.add_column("idempotencyrecord", sa.Column("client_id", UUID, nullable=True))
    op.create_foreign_key("fk_idempotencyrecord_client_id_m2mclient", "idempotencyrecord", "m2mclient", ["client_id"], ["id"])
    op.add_column("idempotencyrecord", sa.Column("resource_id", UUID, nullable=True))
    op.create_index("ix_idempotencyrecord_merchant_id", "idempotencyrecord", ["merchant_id"])
    op.create_index("ix_idempotencyrecord_client_id", "idempotencyrecord", ["client_id"])
    op.create_index("ix_idempotencyrecord_resource_id", "idempotencyrecord", ["resource_id"])
    op.create_index("ix_idempotencyrecord_expires_at", "idempotencyrecord", ["expires_at"])

    # Preserve callback records while adding a deterministic deduplication key.
    op.add_column("providercallback", sa.Column("merchant_id", UUID, nullable=True))
    op.create_foreign_key("fk_providercallback_merchant_id_merchant", "providercallback", "merchant", ["merchant_id"], ["id"])
    op.add_column("providercallback", sa.Column("payment_id", UUID, nullable=True))
    op.create_foreign_key("fk_providercallback_payment_id_payment", "providercallback", "payment", ["payment_id"], ["id"])
    op.add_column("providercallback", sa.Column("callback_type", sa.String(32), server_default="stk", nullable=False))
    op.add_column("providercallback", sa.Column("dedupe_fingerprint", sa.String(64), nullable=True))
    op.execute(sa.text("UPDATE providercallback SET dedupe_fingerprint = REPLACE(CAST(id AS VARCHAR), '-', '') WHERE dedupe_fingerprint IS NULL"))
    op.alter_column("providercallback", "dedupe_fingerprint", existing_type=sa.String(64), nullable=False)
    op.add_column("providercallback", sa.Column("provider_transaction_id", sa.String(120), nullable=True))
    op.add_column("providercallback", sa.Column("processing_error", sa.String(500), nullable=True))
    op.create_unique_constraint("uq_callback_integration_fingerprint", "providercallback", ["integration_id", "dedupe_fingerprint"])
    op.create_index("ix_providercallback_integration_id", "providercallback", ["integration_id"])
    op.create_index("ix_providercallback_merchant_id", "providercallback", ["merchant_id"])
    op.create_index("ix_providercallback_payment_id", "providercallback", ["payment_id"])
    op.create_index("ix_providercallback_callback_type", "providercallback", ["callback_type"])
    op.create_index("ix_providercallback_provider_transaction_id", "providercallback", ["provider_transaction_id"])
    op.create_index("ix_providercallback_processing_status", "providercallback", ["processing_status"])

    # Event identity and merchant scope make the outbox durable and consumer-safe.
    op.add_column("eventoutbox", sa.Column("event_id", UUID, nullable=True))
    op.execute(sa.text("UPDATE eventoutbox SET event_id = id WHERE event_id IS NULL"))
    op.alter_column("eventoutbox", "event_id", existing_type=UUID, nullable=False)
    op.add_column("eventoutbox", sa.Column("merchant_id", UUID, nullable=True))
    op.create_foreign_key("fk_eventoutbox_merchant_id_merchant", "eventoutbox", "merchant", ["merchant_id"], ["id"])
    op.add_column("eventoutbox", sa.Column("schema_version", sa.Integer(), server_default="1", nullable=False))
    op.create_unique_constraint("uq_eventoutbox_event_id", "eventoutbox", ["event_id"])
    op.create_index("ix_eventoutbox_event_type", "eventoutbox", ["event_type"])
    op.create_index("ix_eventoutbox_aggregate_id", "eventoutbox", ["aggregate_id"])
    op.create_index("ix_eventoutbox_published_at", "eventoutbox", ["published_at"])

    # Add a durable audit timestamp while preserving the original audit fields.
    op.add_column("auditevent", sa.Column("occurred_at", AWARE_DATETIME, nullable=True))
    op.execute(sa.text("UPDATE auditevent SET occurred_at = created_at WHERE occurred_at IS NULL"))
    op.alter_column("auditevent", "occurred_at", existing_type=AWARE_DATETIME, nullable=False)
    op.create_index("ix_auditevent_merchant_id", "auditevent", ["merchant_id"])
    op.create_index("ix_auditevent_action", "auditevent", ["action"])
    op.create_index("ix_auditevent_resource_id", "auditevent", ["resource_id"])
    op.create_index("ix_auditevent_occurred_at", "auditevent", ["occurred_at"])

    op.create_table(
        "providerrequest",
        *_common_columns(),
        sa.Column("merchant_id", UUID, sa.ForeignKey("merchant.id"), nullable=True),
        sa.Column("integration_id", UUID, sa.ForeignKey("providerintegration.id"), nullable=False),
        sa.Column("payment_id", UUID, sa.ForeignKey("payment.id"), nullable=True),
        sa.Column("payment_attempt_id", UUID, sa.ForeignKey("paymentattempt.id"), nullable=True),
        sa.Column("operation", sa.String(48), nullable=False),
        sa.Column("correlation_id", UUID, nullable=False),
        sa.Column("provider_request_id", sa.String(120), nullable=True),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("outcome", sa.String(32), nullable=False),
        sa.Column("request_metadata", JSON, nullable=False),
        sa.Column("response_metadata", JSON, nullable=False),
        sa.Column("started_at", AWARE_DATETIME, nullable=False),
        sa.Column("completed_at", AWARE_DATETIME, nullable=True),
        sa.UniqueConstraint("correlation_id", name="uq_providerrequest_correlation_id"),
    )
    for column in ("merchant_id", "integration_id", "payment_id", "payment_attempt_id", "operation", "provider_request_id", "outcome"):
        op.create_index(f"ix_providerrequest_{column}", "providerrequest", [column])
    op.create_index("ix_providerrequest_correlation_id", "providerrequest", ["correlation_id"], unique=True)

    op.create_table(
        "paymentverification",
        *_common_columns(),
        sa.Column("merchant_id", UUID, sa.ForeignKey("merchant.id"), nullable=False),
        sa.Column("payment_id", UUID, sa.ForeignKey("payment.id"), nullable=False),
        sa.Column("payment_attempt_id", UUID, sa.ForeignKey("paymentattempt.id"), nullable=True),
        sa.Column("provider_request_id", UUID, sa.ForeignKey("providerrequest.id"), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("provider_transaction_id", sa.String(120), nullable=True),
        sa.Column("checked_at", AWARE_DATETIME, nullable=False),
        sa.Column("evidence", JSON, nullable=False),
        sa.Column("error_code", sa.String(100), nullable=True),
        sa.Column("error_message", sa.String(500), nullable=True),
    )
    for column in ("merchant_id", "payment_id", "payment_attempt_id", "provider_request_id", "status", "provider_transaction_id"):
        op.create_index(f"ix_paymentverification_{column}", "paymentverification", [column])

    op.create_table(
        "reconciliationrun",
        *_common_columns(),
        sa.Column("merchant_id", UUID, sa.ForeignKey("merchant.id"), nullable=False),
        sa.Column("integration_id", UUID, sa.ForeignKey("providerintegration.id"), nullable=False),
        sa.Column("source", sa.String(48), nullable=False),
        sa.Column("window_start", AWARE_DATETIME, nullable=False),
        sa.Column("window_end", AWARE_DATETIME, nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("started_at", AWARE_DATETIME, nullable=True),
        sa.Column("completed_at", AWARE_DATETIME, nullable=True),
        sa.Column("summary", JSON, nullable=False),
        sa.Column("error_summary", sa.String(500), nullable=True),
        sa.CheckConstraint("window_start < window_end", name="ck_reconciliation_window_order"),
    )
    op.create_index("ix_reconciliationrun_merchant_id", "reconciliationrun", ["merchant_id"])
    op.create_index("ix_reconciliationrun_integration_id", "reconciliationrun", ["integration_id"])
    op.create_index("ix_reconciliationrun_status", "reconciliationrun", ["status"])

    op.create_table(
        "reconciliationitem",
        *_common_columns(),
        sa.Column("merchant_id", UUID, sa.ForeignKey("merchant.id"), nullable=False),
        sa.Column("reconciliation_run_id", UUID, sa.ForeignKey("reconciliationrun.id"), nullable=False),
        sa.Column("payment_id", UUID, sa.ForeignKey("payment.id"), nullable=True),
        sa.Column("provider_transaction_id", sa.String(120), nullable=True),
        sa.Column("match_status", sa.String(40), nullable=False),
        sa.Column("provider_amount_minor", sa.Integer(), nullable=True),
        sa.Column("netpay_amount_minor", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("provider_status", sa.String(48), nullable=True),
        sa.Column("netpay_status", sa.String(48), nullable=True),
        sa.Column("details", JSON, nullable=False),
        sa.Column("resolved_at", AWARE_DATETIME, nullable=True),
        sa.Column("resolution_note", sa.String(500), nullable=True),
        sa.UniqueConstraint("reconciliation_run_id", "provider_transaction_id", name="uq_reconciliation_item_provider_transaction"),
        sa.CheckConstraint("provider_amount_minor IS NULL OR provider_amount_minor >= 0", name="ck_reconciliation_provider_amount_nonnegative"),
        sa.CheckConstraint("netpay_amount_minor IS NULL OR netpay_amount_minor >= 0", name="ck_reconciliation_netpay_amount_nonnegative"),
    )
    for column in ("merchant_id", "reconciliation_run_id", "payment_id", "provider_transaction_id", "match_status"):
        op.create_index(f"ix_reconciliationitem_{column}", "reconciliationitem", [column])

    op.create_table(
        "webhookendpoint",
        *_common_columns(),
        sa.Column("merchant_id", UUID, sa.ForeignKey("merchant.id"), nullable=False),
        sa.Column("url", sa.String(512), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("subscribed_events", JSON, nullable=False),
        sa.Column("signing_secret_ciphertext", sa.LargeBinary(), nullable=True),
        sa.Column("signing_secret_reference", sa.String(255), nullable=True),
        sa.Column("last_success_at", AWARE_DATETIME, nullable=True),
    )
    op.create_index("ix_webhookendpoint_merchant_id", "webhookendpoint", ["merchant_id"])
    op.create_index("ix_webhookendpoint_status", "webhookendpoint", ["status"])

    op.create_table(
        "eventdelivery",
        *_common_columns(),
        sa.Column("merchant_id", UUID, sa.ForeignKey("merchant.id"), nullable=False),
        sa.Column("outbox_event_id", UUID, sa.ForeignKey("eventoutbox.id"), nullable=False),
        sa.Column("webhook_endpoint_id", UUID, sa.ForeignKey("webhookendpoint.id"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("next_attempt_at", AWARE_DATETIME, nullable=False),
        sa.Column("last_http_status", sa.Integer(), nullable=True),
        sa.Column("last_error", sa.String(500), nullable=True),
        sa.Column("delivered_at", AWARE_DATETIME, nullable=True),
        sa.UniqueConstraint("outbox_event_id", "webhook_endpoint_id", name="uq_event_delivery_event_endpoint"),
        sa.CheckConstraint("attempt_count >= 0", name="ck_eventdelivery_attempt_count_nonnegative"),
    )
    for column in ("merchant_id", "outbox_event_id", "webhook_endpoint_id", "status", "next_attempt_at"):
        op.create_index(f"ix_eventdelivery_{column}", "eventdelivery", [column])

    op.create_table(
        "eventdeliveryattempt",
        *_common_columns(),
        sa.Column("event_delivery_id", UUID, sa.ForeignKey("eventdelivery.id"), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("attempted_at", AWARE_DATETIME, nullable=False),
        sa.Column("completed_at", AWARE_DATETIME, nullable=True),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("response_excerpt", sa.String(500), nullable=True),
        sa.Column("error_code", sa.String(100), nullable=True),
        sa.UniqueConstraint("event_delivery_id", "attempt_number", name="uq_delivery_attempt_number"),
    )
    op.create_index("ix_eventdeliveryattempt_event_delivery_id", "eventdeliveryattempt", ["event_delivery_id"])
    op.create_index("ix_eventdeliveryattempt_status", "eventdeliveryattempt", ["status"])


def downgrade() -> None:
    """Remove new tables and added fields; do not delete the original foundation tables."""
    op.drop_table("eventdeliveryattempt")
    op.drop_table("eventdelivery")
    op.drop_table("webhookendpoint")
    op.drop_table("reconciliationitem")
    op.drop_table("reconciliationrun")
    op.drop_table("paymentverification")
    op.drop_table("providerrequest")
    op.drop_table("m2mclient")

    for index in ("ix_auditevent_occurred_at", "ix_auditevent_resource_id", "ix_auditevent_action", "ix_auditevent_merchant_id"):
        op.drop_index(index, table_name="auditevent")
    op.drop_column("auditevent", "occurred_at")

    for index in ("ix_eventoutbox_published_at", "ix_eventoutbox_aggregate_id", "ix_eventoutbox_event_type"):
        op.drop_index(index, table_name="eventoutbox")
    op.drop_constraint("uq_eventoutbox_event_id", "eventoutbox", type_="unique")
    op.drop_constraint("fk_eventoutbox_merchant_id_merchant", "eventoutbox", type_="foreignkey")
    for column in ("schema_version", "merchant_id", "event_id"):
        op.drop_column("eventoutbox", column)

    for index in ("ix_providercallback_processing_status", "ix_providercallback_provider_transaction_id", "ix_providercallback_callback_type", "ix_providercallback_payment_id", "ix_providercallback_merchant_id", "ix_providercallback_integration_id"):
        op.drop_index(index, table_name="providercallback")
    op.drop_constraint("uq_callback_integration_fingerprint", "providercallback", type_="unique")
    op.drop_constraint("fk_providercallback_payment_id_payment", "providercallback", type_="foreignkey")
    op.drop_constraint("fk_providercallback_merchant_id_merchant", "providercallback", type_="foreignkey")
    for column in ("processing_error", "provider_transaction_id", "dedupe_fingerprint", "callback_type", "payment_id", "merchant_id"):
        op.drop_column("providercallback", column)

    for index in ("ix_idempotencyrecord_expires_at", "ix_idempotencyrecord_resource_id", "ix_idempotencyrecord_client_id", "ix_idempotencyrecord_merchant_id"):
        op.drop_index(index, table_name="idempotencyrecord")
    op.drop_constraint("fk_idempotencyrecord_client_id_m2mclient", "idempotencyrecord", type_="foreignkey")
    for column in ("resource_id", "client_id"):
        op.drop_column("idempotencyrecord", column)

    for index in ("ix_paymentattempt_status", "ix_paymentattempt_payment_id"):
        op.drop_index(index, table_name="paymentattempt")
    op.drop_constraint("uq_paymentattempt_correlation_id", "paymentattempt", type_="unique")
    for column in ("safe_error_message", "safe_error_code", "provider_result_code", "correlation_id"):
        op.drop_column("paymentattempt", column)

    for index in ("ix_payment_provider_receipt", "ix_payment_provider_merchant_request_id", "ix_payment_provider_checkout_request_id", "ix_payment_provider_transaction_id", "ix_payment_status", "ix_payment_payment_source", "ix_payment_integration_id", "ix_payment_merchant_id"):
        op.drop_index(index, table_name="payment")
    for constraint in ("uq_payment_integration_merchant_request", "uq_payment_integration_checkout", "uq_payment_integration_provider_receipt"):
        op.drop_constraint(constraint, "payment", type_="unique")
    for column in ("cancelled_at", "completed_at", "initiated_at", "provider_result_description", "provider_result_code", "provider_receipt", "provider_merchant_request_id", "provider_checkout_request_id", "payment_source", "phone_number"):
        op.drop_column("payment", column)

    for index in ("ix_providerintegration_credential_status", "ix_providerintegration_shortcode", "ix_providerintegration_merchant_id"):
        op.drop_index(index, table_name="providerintegration")
    op.drop_constraint("uq_providerintegration_integration_id", "providerintegration", type_="unique")
    for column in ("registration_error", "c2b_registered_at", "c2b_confirmation_url", "c2b_validation_url", "stk_callback_url", "c2b_registration_status", "c2b_enabled", "credential_version", "credentials_validated_at", "credential_status", "passkey_ciphertext", "consumer_secret_ciphertext", "consumer_key_ciphertext", "product_type", "party_b_shortcode", "shortcode", "integration_id"):
        op.drop_column("providerintegration", column)

    for column in ("attributes", "contact_phone", "contact_email"):
        op.drop_column("merchant", column)
