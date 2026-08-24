"""Envelope ingest from Cloudflare Worker — match intent, update status, fanout."""
from __future__ import annotations

from typing import Any

from loguru import logger
from sqlmodel.ext.asyncio.session import AsyncSession

from app.crud.integration import integration_crud
from app.crud.payment_intent import payment_intent_crud
from app.models.payment_intent import PaymentIntent
from app.schemas.event import EnvelopeIn, ProcessResult
from app.services.events import record_event
from app.services.webhooks import fanout_webhooks


def _extract_stk(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    body = payload.get("Body") or payload
    if isinstance(body, dict):
        cb = body.get("stkCallback") or body
        if isinstance(cb, dict):
            return cb
    return payload if isinstance(payload, dict) else {}


async def apply_payment_result(
    session: AsyncSession,
    intent: PaymentIntent,
    *,
    status: str,
    transaction_id: str | None = None,
    failure: str | None = None,
) -> PaymentIntent:
    update: dict[str, Any] = {"status": status}
    if transaction_id:
        update["provider_transaction_id"] = transaction_id
    if failure:
        update["failure_reason"] = failure[:512]
    intent = await payment_intent_crud.update(session, db_obj=intent, obj_in=update)
    await session.commit()
    await session.refresh(intent)
    await fanout_webhooks(
        session,
        intent.tenant_id,
        intent.id,
        {
            "event": "payment.update",
            "intent_id": str(intent.id),
            "status": status,
            "provider_transaction_id": transaction_id,
            "failure_reason": failure,
        },
    )
    return intent


async def process_envelope(session: AsyncSession, envelope: EnvelopeIn) -> ProcessResult:
    public_id = None
    if isinstance(envelope.integration, dict):
        public_id = envelope.integration.get("public_id") or envelope.integration.get("id")
    integ = None
    if public_id:
        integ = await integration_crud.get_by_public_id(session, str(public_id), include_deleted=True)

    et = envelope.event_type.lower()
    if "stk" in et or "callback" in et:
        cb = _extract_stk(envelope.payload)
        checkout_id = cb.get("CheckoutRequestID") or cb.get("checkoutRequestID")
        result_code = cb.get("ResultCode")
        result_desc = cb.get("ResultDesc") or ""
        if not checkout_id:
            return ProcessResult(status="ignored", message="No CheckoutRequestID")
        intent = await payment_intent_crud.get_by_checkout_id(session, str(checkout_id))
        if not intent:
            return ProcessResult(status="not_found", message=f"No intent for {checkout_id}")
        if intent.status in ("succeeded", "failed"):
            return ProcessResult(status="duplicate", intent_id=intent.id, message="Already settled")
        ok = str(result_code) in ("0", "00")
        tx_id = None
        items = (
            cb.get("CallbackMetadata", {}).get("Item", [])
            if isinstance(cb.get("CallbackMetadata"), dict)
            else []
        )
        for it in items if isinstance(items, list) else []:
            if isinstance(it, dict) and it.get("Name") == "MpesaReceiptNumber":
                tx_id = str(it.get("Value"))
        if ok:
            await apply_payment_result(session, intent, status="succeeded", transaction_id=tx_id)
            await record_event(
                session,
                tenant_id=intent.tenant_id,
                integration_id=intent.integration_id,
                payment_intent_id=intent.id,
                category="callback",
                action="stk.succeeded",
                message=f"STK paid {checkout_id}",
                is_replayable=True,
            )
            return ProcessResult(
                status="succeeded",
                intent_id=intent.id,
                ResultCode="0",
                ResultDesc=result_desc,
            )
        await apply_payment_result(session, intent, status="failed", failure=result_desc)
        await record_event(
            session,
            tenant_id=intent.tenant_id,
            integration_id=intent.integration_id,
            payment_intent_id=intent.id,
            category="callback",
            action="stk.failed",
            message=result_desc or "STK failed",
            is_replayable=True,
        )
        return ProcessResult(
            status="failed",
            intent_id=intent.id,
            ResultCode=str(result_code),
            ResultDesc=result_desc,
        )

    logger.info("Envelope event_type={} public_id={} — recorded", envelope.event_type, public_id)
    await record_event(
        session,
        tenant_id=integ.tenant_id if integ else None,
        integration_id=integ.id if integ else None,
        category="callback",
        action=envelope.event_type,
        message=f"Envelope {envelope.event_id}",
        is_replayable=True,
    )
    return ProcessResult(status="accepted", message="Recorded")
