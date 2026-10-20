"""Durable payment event construction."""

from datetime import datetime, timezone
from uuid import uuid4

from app.models import EventOutbox, Payment


def payment_event(payment: Payment, event_type: str) -> EventOutbox:
    event_id = uuid4()
    now = datetime.now(timezone.utc)
    return EventOutbox(
        event_id=event_id,
        merchant_id=payment.merchant_id,
        aggregate_id=payment.id,
        event_type=event_type,
        schema_version=1,
        payload={
            "event_id": str(event_id),
            "payment_id": str(payment.id),
            "merchant_id": str(payment.merchant_id),
            "client_reference": payment.client_reference,
            "amount_minor": payment.amount_minor,
            "currency": payment.currency,
            "status": payment.status,
        },
        delivery_status="pending",
        attempts=0,
        next_attempt_at=now,
        created_at=now,
    )
