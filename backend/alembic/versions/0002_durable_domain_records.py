"""Add shared soft deletion and durable verification/reconciliation models.

Revision ID: 0002_durable_domain_records
Revises: 0001_initial_domain

This migration is additive: the initial schema remains intact so existing
installations can upgrade without rewriting migration history.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002_durable_domain_records"
down_revision: Union[str, None] = "0001_initial_domain"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = sa.Uuid()
AWARE_DATETIME = sa.DateTime(timezone=True)
JSON = sa.JSON()


def _add_common_columns(table: str, *, add_updated_at: bool = False) -> None:
    """Add shared UTC timestamp and soft-deletion columns to an existing table."""
    if add_updated_at:
        op.add_column(table, sa.Column("updated_at", AWARE_DATETIME, nullable=True))
        op.execute(sa.text(f"UPDATE {table} SET updated_at = created_at WHERE updated_at IS NULL"))
        op.alter_column(table, "updated_at", existing_type=AWARE_DATETIME, nullable=False)
    op.add_column(table, sa.Column("deleted_at", AWARE_DATETIME, nullable=True))


def upgrade() -> None:
    # Existing models receive the common soft-delete column. Tables that
    # previously lacked updated_at receive it with a backfill from created_at.
    for table in (
        "merchant", "m2mclient", "darajaintegration", "payment",
        "idempotencyrecord", "providercallback", "paymentattempt",
        "eventdestination", "eventoutbox", "eventdeliveryattempt",
    ):
        _add_common_columns(
            table,
            add_updated_at=table in {
                "m2mclient", "idempotencyrecord", "providercallback",
                "eventoutbox", "eventdeliveryattempt",
            },
        )

    # Backfill merchant identity before enforcing uniqueness/non-nullability.
    op.add_column("merchant", sa.Column("slug", sa.String(length=100), nullable=True))
    op.add_column("merchant", sa.Column("default_currency", sa.String(length=3), server_default="KES", nullable=False))
    op.add_column("merchant", sa.Column("contact_email", sa.String(length=254), nullable=True))
    op.add_column("merchant", sa.Column("contact_phone", sa.String(length=20), nullable=True))
    op.add_column("merchant", sa.Column("attributes", JSON, server_default=sa.text("'{}'"), nullable=False))
    op.execute(sa.text("UPDATE merchant SET slug = 'merchant-' || REPLACE(CAST(id AS VARCHAR), '-', '') WHERE slug IS NULL"))
    op.alter_column("merchant", "slug", existing_type=sa.String(length=100), nullable=False)
    op.create_index("ix_merchant_slug", "merchant", ["slug"], unique=True)

    op.add_column("m2mclient", sa.Column("expires_at", AWARE_DATETIME, nullable=True))
    op.add_column("m2mclient", sa.Column("revoked_at", AWARE_DATETIME, nullable=True))

    op.add_column("darajaintegration", sa.Column("credentials_validated_at", AWARE_DATETIME, nullable=True))
    op.add_column("darajaintegration", sa.Column("credential_version", sa.Integer(), server_default="1", nullable=False))
    op.add_column("darajaintegration", sa.Column("c2b_registered_at", AWARE_DATETIME, nullable=True))

    op.add_column("payment", sa.Column("direction", sa.String(length=16), server_default="inbound", nullable=False))
    op.add_column("payment", sa.Column("description", sa.String(length=250), nullable=True))
    op.add_column("payment", sa.Column("succeeded_at", AWARE_DATETIME, nullable=True))
    op.add_column("payment", sa.Column("failed_at", AWARE_DATETIME, nullable=True))
    op.add_column("payment", sa.Column("cancelled_at", AWARE_DATETIME, nullable=True))

    op.add_column("idempotencyrecord", sa.Column("client_id", UUID, nullable=True))
    op.create_foreign_key("fk_idempotencyrecord_client_id_m2mclient", "idempotencyrecord", "m2mclient", ["client_id"], ["id"])
    op.create_index("ix_idempotencyrecord_client_id", "idempotencyrecord", ["client_id"], unique=False)
    op.add_column("idempotencyrecord", sa.Column("response_snapshot", JSON, nullable=True))

    op.add_column("providercallback", sa.Column("merchant_id", UUID, nullable=True))
    op.create_foreign_key("fk_providercallback_merchant_id_merchant", "providercallback", "merchant", ["merchant_id"], ["id"])
    op.create_index("ix_providercallback_merchant_id", "providercallback", ["merchant_id"], unique=False)
    op.add_column("providercallback", sa.Column("provider_event_id", sa.String(length=120), nullable=True))
    op.add_column("providercallback", sa.Column("provider_transaction_id", sa.String(length=120), nullable=True))
    op.create_index("ix_providercallback_provider_transaction_id", "providercallback", ["provider_transaction_id"], unique=False)
    op.add_column("providercallback", sa.Column("processing_error", sa.String(length=500), nullable=True))

    op.add_column("eventoutbox", sa.Column("aggregate_type", sa.String(length=50), server_default="payment", nullable=False))
    op.add_column("eventoutbox", sa.Column("published_at", AWARE_DATETIME, nullable=True))

    op.create_table(
        "providerrequest",
        sa.Column("id", UUID, nullable=False),
        sa.Column("created_at", AWARE_DATETIME, nullable=False),
        sa.Column("updated_at", AWARE_DATETIME, nullable=False),
        sa.Column("deleted_at", AWARE_DATETIME, nullable=True),
        sa.Column("merchant_id", UUID, nullable=True),
        sa.Column("integration_id", UUID, nullable=False),
        sa.Column("payment_id", UUID, nullable=True),
        sa.Column("payment_attempt_id", UUID, nullable=True),
        sa.Column("operation", sa.String(length=48), nullable=False),
        sa.Column("correlation_id", UUID, nullable=False),
        sa.Column("provider_request_id", sa.String(length=120), nullable=True),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.Column("request_metadata", JSON, nullable=False),
        sa.Column("response_metadata", JSON, nullable=False),
        sa.Column("started_at", AWARE_DATETIME, nullable=False),
        sa.Column("completed_at", AWARE_DATETIME, nullable=True),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchant.id"]),
        sa.ForeignKeyConstraint(["integration_id"], ["darajaintegration.id"]),
        sa.ForeignKeyConstraint(["payment_id"], ["payment.id"]),
        sa.ForeignKeyConstraint(["payment_attempt_id"], ["paymentattempt.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_providerrequest_correlation_id", "providerrequest", ["correlation_id"], unique=True)
    for column in ("merchant_id", "integration_id", "payment_id", "payment_attempt_id", "operation", "provider_request_id", "outcome"):
        op.create_index(f"ix_providerrequest_{column}", "providerrequest", [column], unique=False)

    op.create_table(
        "paymentverification",
        sa.Column("id", UUID, nullable=False),
        sa.Column("created_at", AWARE_DATETIME, nullable=False),
        sa.Column("updated_at", AWARE_DATETIME, nullable=False),
        sa.Column("deleted_at", AWARE_DATETIME, nullable=True),
        sa.Column("merchant_id", UUID, nullable=False),
        sa.Column("payment_id", UUID, nullable=False),
        sa.Column("payment_attempt_id", UUID, nullable=True),
        sa.Column("provider_request_id", UUID, nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("provider_transaction_id", sa.String(length=120), nullable=True),
        sa.Column("checked_at", AWARE_DATETIME, nullable=False),
        sa.Column("evidence", JSON, nullable=False),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchant.id"]),
        sa.ForeignKeyConstraint(["payment_id"], ["payment.id"]),
        sa.ForeignKeyConstraint(["payment_attempt_id"], ["paymentattempt.id"]),
        sa.ForeignKeyConstraint(["provider_request_id"], ["providerrequest.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("merchant_id", "payment_id", "payment_attempt_id", "provider_request_id", "status", "provider_transaction_id"):
        op.create_index(f"ix_paymentverification_{column}", "paymentverification", [column], unique=False)

    op.create_table(
        "reconciliationrun",
        sa.Column("id", UUID, nullable=False),
        sa.Column("created_at", AWARE_DATETIME, nullable=False),
        sa.Column("updated_at", AWARE_DATETIME, nullable=False),
        sa.Column("deleted_at", AWARE_DATETIME, nullable=True),
        sa.Column("merchant_id", UUID, nullable=False),
        sa.Column("integration_id", UUID, nullable=False),
        sa.Column("source", sa.String(length=48), nullable=False),
        sa.Column("window_start", AWARE_DATETIME, nullable=False),
        sa.Column("window_end", AWARE_DATETIME, nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", AWARE_DATETIME, nullable=True),
        sa.Column("completed_at", AWARE_DATETIME, nullable=True),
        sa.Column("summary", JSON, nullable=False),
        sa.Column("error_summary", sa.String(length=500), nullable=True),
        sa.CheckConstraint("window_start < window_end", name="ck_reconciliation_window_order"),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchant.id"]),
        sa.ForeignKeyConstraint(["integration_id"], ["darajaintegration.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("merchant_id", "integration_id", "status"):
        op.create_index(f"ix_reconciliationrun_{column}", "reconciliationrun", [column], unique=False)

    op.create_table(
        "reconciliationitem",
        sa.Column("id", UUID, nullable=False),
        sa.Column("created_at", AWARE_DATETIME, nullable=False),
        sa.Column("updated_at", AWARE_DATETIME, nullable=False),
        sa.Column("deleted_at", AWARE_DATETIME, nullable=True),
        sa.Column("merchant_id", UUID, nullable=False),
        sa.Column("reconciliation_run_id", UUID, nullable=False),
        sa.Column("payment_id", UUID, nullable=True),
        sa.Column("provider_transaction_id", sa.String(length=120), nullable=True),
        sa.Column("match_status", sa.String(length=40), nullable=False),
        sa.Column("provider_amount_minor", sa.Integer(), nullable=True),
        sa.Column("netpay_amount_minor", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("provider_status", sa.String(length=48), nullable=True),
        sa.Column("netpay_status", sa.String(length=48), nullable=True),
        sa.Column("details", JSON, nullable=False),
        sa.Column("resolved_at", AWARE_DATETIME, nullable=True),
        sa.Column("resolution_note", sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchant.id"]),
        sa.ForeignKeyConstraint(["reconciliation_run_id"], ["reconciliationrun.id"]),
        sa.ForeignKeyConstraint(["payment_id"], ["payment.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("reconciliation_run_id", "provider_transaction_id", name="uq_reconciliation_item_provider_transaction"),
        sa.CheckConstraint("provider_amount_minor IS NULL OR provider_amount_minor >= 0", name="ck_reconciliation_provider_amount_nonnegative"),
        sa.CheckConstraint("netpay_amount_minor IS NULL OR netpay_amount_minor >= 0", name="ck_reconciliation_netpay_amount_nonnegative"),
    )
    for column in ("merchant_id", "reconciliation_run_id", "payment_id", "provider_transaction_id", "match_status"):
        op.create_index(f"ix_reconciliationitem_{column}", "reconciliationitem", [column], unique=False)

    op.create_table(
        "webhookendpoint",
        sa.Column("id", UUID, nullable=False),
        sa.Column("created_at", AWARE_DATETIME, nullable=False),
        sa.Column("updated_at", AWARE_DATETIME, nullable=False),
        sa.Column("deleted_at", AWARE_DATETIME, nullable=True),
        sa.Column("merchant_id", UUID, nullable=False),
        sa.Column("url", sa.String(length=512), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("subscribed_events", JSON, nullable=False),
        sa.Column("signing_secret_ciphertext", sa.LargeBinary(), nullable=True),
        sa.Column("signing_secret_reference", sa.String(length=255), nullable=True),
        sa.Column("last_success_at", AWARE_DATETIME, nullable=True),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchant.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_webhookendpoint_merchant_id", "webhookendpoint", ["merchant_id"], unique=False)
    op.create_index("ix_webhookendpoint_status", "webhookendpoint", ["status"], unique=False)

    op.create_table(
        "eventdelivery",
        sa.Column("id", UUID, nullable=False),
        sa.Column("created_at", AWARE_DATETIME, nullable=False),
        sa.Column("updated_at", AWARE_DATETIME, nullable=False),
        sa.Column("deleted_at", AWARE_DATETIME, nullable=True),
        sa.Column("merchant_id", UUID, nullable=False),
        sa.Column("outbox_event_id", UUID, nullable=False),
        sa.Column("webhook_endpoint_id", UUID, nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("next_attempt_at", AWARE_DATETIME, nullable=False),
        sa.Column("last_http_status", sa.Integer(), nullable=True),
        sa.Column("last_error", sa.String(length=500), nullable=True),
        sa.Column("delivered_at", AWARE_DATETIME, nullable=True),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchant.id"]),
        sa.ForeignKeyConstraint(["outbox_event_id"], ["eventoutbox.id"]),
        sa.ForeignKeyConstraint(["webhook_endpoint_id"], ["webhookendpoint.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("outbox_event_id", "webhook_endpoint_id", name="uq_event_delivery_event_endpoint"),
        sa.CheckConstraint("attempt_count >= 0", name="ck_eventdelivery_attempt_count_nonnegative"),
    )
    for column in ("merchant_id", "outbox_event_id", "webhook_endpoint_id", "status", "next_attempt_at"):
        op.create_index(f"ix_eventdelivery_{column}", "eventdelivery", [column], unique=False)

    op.add_column("eventdeliveryattempt", sa.Column("event_delivery_id", UUID, nullable=True))
    op.create_foreign_key("fk_eventdeliveryattempt_event_delivery_id_eventdelivery", "eventdeliveryattempt", "eventdelivery", ["event_delivery_id"], ["id"])
    op.create_index("ix_eventdeliveryattempt_event_delivery_id", "eventdeliveryattempt", ["event_delivery_id"], unique=False)

    op.create_table(
        "auditlog",
        sa.Column("id", UUID, nullable=False),
        sa.Column("created_at", AWARE_DATETIME, nullable=False),
        sa.Column("updated_at", AWARE_DATETIME, nullable=False),
        sa.Column("deleted_at", AWARE_DATETIME, nullable=True),
        sa.Column("merchant_id", UUID, nullable=True),
        sa.Column("actor_type", sa.String(length=32), nullable=False),
        sa.Column("actor_id", sa.String(length=120), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("target_type", sa.String(length=100), nullable=False),
        sa.Column("target_id", sa.String(length=120), nullable=True),
        sa.Column("occurred_at", AWARE_DATETIME, nullable=False),
        sa.Column("metadata_json", JSON, nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchant.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("merchant_id", "action", "target_id", "occurred_at"):
        op.create_index(f"ix_auditlog_{column}", "auditlog", [column], unique=False)


def downgrade() -> None:
    """Remove the additive domain tables and columns introduced by this revision."""
    op.drop_table("auditlog")
    op.drop_index("ix_eventdeliveryattempt_event_delivery_id", table_name="eventdeliveryattempt")
    op.drop_constraint("fk_eventdeliveryattempt_event_delivery_id_eventdelivery", "eventdeliveryattempt", type_="foreignkey")
    op.drop_column("eventdeliveryattempt", "event_delivery_id")
    op.drop_table("eventdelivery")
    op.drop_table("webhookendpoint")
    op.drop_table("reconciliationitem")
    op.drop_table("reconciliationrun")
    op.drop_table("paymentverification")
    op.drop_table("providerrequest")

    for column in ("aggregate_type", "published_at"):
        op.drop_column("eventoutbox", column)
    op.drop_index("ix_providercallback_provider_transaction_id", table_name="providercallback")
    op.drop_index("ix_providercallback_merchant_id", table_name="providercallback")
    op.drop_constraint("fk_providercallback_merchant_id_merchant", "providercallback", type_="foreignkey")
    for column in ("processing_error", "provider_transaction_id", "provider_event_id", "merchant_id"):
        op.drop_column("providercallback", column)
    op.drop_column("idempotencyrecord", "response_snapshot")
    op.drop_index("ix_idempotencyrecord_client_id", table_name="idempotencyrecord")
    op.drop_constraint("fk_idempotencyrecord_client_id_m2mclient", "idempotencyrecord", type_="foreignkey")
    op.drop_column("idempotencyrecord", "client_id")
    for column in ("direction", "description", "succeeded_at", "failed_at", "cancelled_at"):
        op.drop_column("payment", column)
    op.drop_column("m2mclient", "revoked_at")
    op.drop_column("m2mclient", "expires_at")
    for column in ("credentials_validated_at", "credential_version", "c2b_registered_at"):
        op.drop_column("darajaintegration", column)
    op.drop_index("ix_merchant_slug", table_name="merchant")
    for column in ("slug", "default_currency", "contact_email", "contact_phone", "attributes"):
        op.drop_column("merchant", column)
    for table in (
        "merchant", "m2mclient", "darajaintegration", "payment",
        "idempotencyrecord", "providercallback", "paymentattempt",
        "eventdestination", "eventoutbox", "eventdeliveryattempt",
    ):
        op.drop_column(table, "deleted_at")
    for table in ("m2mclient", "idempotencyrecord", "providercallback", "eventoutbox", "eventdeliveryattempt"):
        op.drop_column(table, "updated_at")
