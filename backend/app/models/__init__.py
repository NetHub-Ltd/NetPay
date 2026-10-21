"""Register the complete NetPay SQLModel schema for runtime and Alembic."""

from app.models.attempts import PaymentAttempt
from app.models.base import BaseMixin
from app.models.delivery import EventDeliveryAttempt
from app.models.events import EventOutbox
from app.models.integrations import DarajaIntegration
from app.models.merchants import M2MClient, Merchant
from app.models.operations import (
    AuditLog,
    EventDelivery,
    PaymentVerification,
    ProviderRequest,
    ReconciliationItem,
    ReconciliationRun,
    WebhookEndpoint,
)
from app.models.payments import IdempotencyRecord, Payment, ProviderCallback

__all__ = [
    "AuditLog",
    "BaseMixin",
    "DarajaIntegration",
    "EventDelivery",
    "EventDeliveryAttempt",
    "EventOutbox",
    "IdempotencyRecord",
    "M2MClient",
    "Merchant",
    "Payment",
    "PaymentAttempt",
    "PaymentVerification",
    "ProviderCallback",
    "ProviderRequest",
    "ReconciliationItem",
    "ReconciliationRun",
    "WebhookEndpoint",
]
