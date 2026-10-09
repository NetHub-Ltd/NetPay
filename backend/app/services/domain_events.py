"""Domain events after payment settlement.

Webhooks and live UI are equal subscribers. Errors in one must not block others.
"""
from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.logging import logger
from app.models.payment_intent import PaymentIntent
from app.services.live_hub import publish_notification
from app.services.webhooks import fanout_webhooks


async def publish_payment_settled(
    session: AsyncSession,
    intent: PaymentIntent,
    *,
    transaction_id: str | None = None,
    failure: str | None = None,
) -> None:
    """Notify all sinks that a payment intent reached a terminal-ish update."""
    meta = None
    if intent.metadata_json:
        try:
            import json as _json

            meta = _json.loads(intent.metadata_json)
        except Exception:
            meta = None

    payload: dict[str, Any] = {
        "event": "payment.update",
        "intent_id": str(intent.id),
        "status": intent.status,
        "provider_transaction_id": transaction_id,
        "failure_reason": failure,
        "amount_minor": intent.amount_minor,
        "phone": intent.phone,
        "metadata": meta,
    }

    # 1) Merchant webhooks (isolated)
    try:
        await fanout_webhooks(
            session,
            intent.tenant_id,
            intent.id,
            payload,
            intent=intent,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception(
            "domain_event webhook fanout failed intent={} err={}",
            intent.id,
            exc,
        )

    # 2) Live SPA operators (isolated)
    label = {
        "succeeded": "Payment paid",
        "failed": "Payment failed",
        "expired": "Payment expired",
    }.get(intent.status, f"Payment {intent.status}")
    level = (
        "success"
        if intent.status == "succeeded"
        else "error"
        if intent.status in ("failed", "expired")
        else "info"
    )
    amount_txt = f"{(intent.amount_minor or 0) / 100:.2f} {intent.currency or 'KES'}"
    try:
        await publish_notification(
            title=label,
            body=f"{amount_txt} · {intent.phone or ''}".strip(" ·"),
            tenant_id=intent.tenant_id,
            intent_id=intent.id,
            level=level,
            href=f"/intents/{intent.id}",
            status=intent.status,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception(
            "domain_event live notify failed intent={} err={}",
            intent.id,
            exc,
        )
