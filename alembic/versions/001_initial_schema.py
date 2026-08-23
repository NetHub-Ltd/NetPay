"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-08-23
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("display_name", sa.String(120), nullable=True),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_role", "users", ["role"])
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])

    op.create_table("tenants",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("slug", sa.String(40), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tenants_slug", "tenants", ["slug"], unique=True)
    # users.tenant_id FK omitted for SQLite ALTER limitation; app enforces integrity

    op.create_table("integrations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("public_id", sa.String(32), nullable=False),
        sa.Column("shortcode", sa.String(12), nullable=False),
        sa.Column("type", sa.String(16), nullable=False),
        sa.Column("environment", sa.String(16), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("confirmation_url", sa.String(512), nullable=True),
        sa.Column("validation_url", sa.String(512), nullable=True),
        sa.Column("stk_callback_url", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_integrations_tenant_id", "integrations", ["tenant_id"])
    op.create_index("ix_integrations_public_id", "integrations", ["public_id"], unique=True)

    op.create_table("credentials",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("integration_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("value", sa.String(512), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["integration_id"], ["integrations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_credentials_integration_id", "credentials", ["integration_id"])

    op.create_table("oauth_clients",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("client_id", sa.String(64), nullable=False),
        sa.Column("client_secret_hash", sa.String(), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_oauth_clients_client_id", "oauth_clients", ["client_id"], unique=True)
    op.create_index("ix_oauth_clients_tenant_id", "oauth_clients", ["tenant_id"])

    op.create_table("webhooks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("url", sa.String(512), nullable=False),
        sa.Column("secret", sa.String(128), nullable=False),
        sa.Column("last_live_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_webhooks_tenant_id", "webhooks", ["tenant_id"])

    op.create_table("webhook_deliveries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("webhook_id", sa.Uuid(), nullable=False),
        sa.Column("payment_intent_id", sa.Uuid(), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("ok", sa.Boolean(), nullable=False),
        sa.Column("error", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["webhook_id"], ["webhooks.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_webhook_deliveries_webhook_id", "webhook_deliveries", ["webhook_id"])

    op.create_table("payment_intents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("integration_id", sa.Uuid(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("intent_type", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False),
        sa.Column("phone", sa.String(16), nullable=False),
        sa.Column("account_reference", sa.String(12), nullable=True),
        sa.Column("description", sa.String(32), nullable=True),
        sa.Column("context_json", sa.String(), nullable=True),
        sa.Column("provider", sa.String(16), nullable=False),
        sa.Column("provider_checkout_id", sa.String(64), nullable=True),
        sa.Column("provider_merchant_id", sa.String(64), nullable=True),
        sa.Column("provider_transaction_id", sa.String(64), nullable=True),
        sa.Column("failure_reason", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["integration_id"], ["integrations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payment_intents_tenant_id", "payment_intents", ["tenant_id"])
    op.create_index("ix_payment_intents_integration_id", "payment_intents", ["integration_id"])
    op.create_index("ix_payment_intents_status", "payment_intents", ["status"])
    op.create_index("ix_payment_intents_provider_checkout_id", "payment_intents", ["provider_checkout_id"])

    op.create_table("gateway_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=True),
        sa.Column("integration_id", sa.Uuid(), nullable=True),
        sa.Column("payment_intent_id", sa.Uuid(), nullable=True),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("message", sa.String(512), nullable=False),
        sa.Column("payload_json", sa.String(), nullable=True),
        sa.Column("is_replayable", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_gateway_events_tenant_id", "gateway_events", ["tenant_id"])
    op.create_index("ix_gateway_events_payment_intent_id", "gateway_events", ["payment_intent_id"])

def downgrade() -> None:
    op.drop_table("gateway_events")
    op.drop_table("payment_intents")
    op.drop_table("webhook_deliveries")
    op.drop_table("webhooks")
    op.drop_table("oauth_clients")
    op.drop_table("credentials")
    op.drop_table("integrations")
    op.drop_table("tenants")
    op.drop_table("users")
