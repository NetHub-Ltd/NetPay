"""Envelope ingest from Cloudflare Worker — match intent, update status, fanout."""
from __future__ import annotations

from typing import Any

from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.logging import logger
from app.crud.integration import integration_crud
from app.crud.payment_intent import payment_intent_crud
from app.domain.payment_status import IllegalTransitionError, is_terminal
from app.models.payment_intent import PaymentIntent
from app.schemas.event import EnvelopeIn, ProcessResult
from app.services.events import record_event
from app.services.ledger import post_collection_credit
from app.services.transitions import transition_payment_intent
from app.services.live_hub import publish_notification
from app.services.webhooks import fanout_webhooks



def _extract_c2b(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    # Daraja may nest or send flat confirmation body
    body = payload.get("Body") if isinstance(payload.get("Body"), dict) else payload
    if isinstance(body, dict) and isinstance(body.get("stkCallback"), dict):
        return {}
    return body if isinstance(body, dict) else {}


def _c2b_bill_ref(data: dict[str, Any]) -> str | None:
    for key in ("BillRefNumber", "billRefNumber", "InvoiceNumber", "AccountReference", "account_reference"):
        val = data.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()
    return None


def _c2b_trans_id(data: dict[str, Any]) -> str | None:
    for key in ("TransID", "transID", "TransactionID", "MpesaReceiptNumber"):
        val = data.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()
    return None


def _c2b_amount_minor(data: dict[str, Any]) -> int | None:
    raw = data.get("TransAmount") or data.get("Amount") or data.get("amount")
    if raw is None:
        return None
    try:
        # KES: major units from Daraja → minor
        return int(round(float(str(raw).replace(",", "")) * 100))
    except (TypeError, ValueError):
        return None

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
    """Apply terminal result via state machine; no-op if already same terminal status."""
    if intent.status == status:
        return intent
    if is_terminal(intent.status):
        # Already settled to a different terminal state — do not regress
        logger.info(
            "Skip apply_payment_result intent={} current={} requested={}",
            intent.id,
            intent.status,
            status,
        )
        return intent
    try:
        intent = await transition_payment_intent(
            session,
            intent,
            to_status=status,
            provider_transaction_id=transaction_id,
            failure_reason=failure,
        )
    except IllegalTransitionError as exc:
        logger.warning("Illegal transition on apply_payment_result: {}", exc)
        return intent
    if status == "succeeded":
        await post_collection_credit(session, intent)
    await session.commit()
    await session.refresh(intent)
    meta = None
    if intent.metadata_json:
        try:
            import json as _json
            meta = _json.loads(intent.metadata_json)
        except Exception:
            meta = None
    await fanout_webhooks(
        session,
        intent.tenant_id,
        intent.id,
        {
            "event": "payment.update",
            "intent_id": str(intent.id),
            "status": intent.status,
            "provider_transaction_id": transaction_id,
            "failure_reason": failure,
            "amount_minor": intent.amount_minor,
            "phone": intent.phone,
            "metadata": meta,
        },
        intent=intent,
    )
    # Live SPA notification (WebSocket)
    label = {"succeeded": "Payment paid", "failed": "Payment failed", "expired": "Payment expired"}.get(
        intent.status, f"Payment {intent.status}"
    )
    level = "success" if intent.status == "succeeded" else "error" if intent.status in ("failed", "expired") else "info"
    amount_txt = f"{(intent.amount_minor or 0) / 100:.2f} {intent.currency or 'KES'}"
    try:
        await publish_notification(
            title=label,
            body=f"{amount_txt} · {intent.phone or ''}".strip(" ·"),
            tenant_id=intent.tenant_id,
            intent_id=intent.id,
            level=level,
            href=f"/intents/{intent.id}",
        )
    except Exception:  # noqa: BLE001
        pass
    return intent


async def process_envelope(session: AsyncSession, envelope: EnvelopeIn) -> ProcessResult:
    et_early = (envelope.event_type or "").lower()
    if "heartbeat" in et_early or et_early in {"edge.ping", "edge_ping"}:
        return ProcessResult(
            status="ok",
            message="Edge heartbeat accepted",
        )

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
        if is_terminal(intent.status):
            if intent.status == "expired":
                return ProcessResult(
                    status="ignored",
                    intent_id=intent.id,
                    message="Intent expired; late callback not applied (no auto-succeed)",
                )
            return ProcessResult(
                status="duplicate",
                intent_id=intent.id,
                message="Already settled",
            )
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

    # --- C2B validation: audit only (Safaricom sync response is edge responsibility) ---
    if et in {"c2b_validation", "validation"} or ("validation" in et and "c2b" in et):
        await record_event(
            session,
            tenant_id=integ.tenant_id if integ else None,
            integration_id=integ.id if integ else None,
            category="callback",
            action="c2b.validation",
            message=f"C2B validation audit {envelope.event_id}",
            is_replayable=False,
        )
        return ProcessResult(status="accepted", message="C2B validation recorded")

    # --- C2B confirmation: map to open payment by account reference ---
    if "confirmation" in et or et in {"c2b_confirmation", "c2b.confirmation"}:
        if not integ:
            return ProcessResult(status="not_found", message="Unknown integration for C2B confirmation")
        data = _extract_c2b(envelope.payload)
        bill_ref = _c2b_bill_ref(data)
        trans_id = _c2b_trans_id(data)
        if not bill_ref:
            from app.crud.reconciliation import reconciliation_crud
            await reconciliation_crud.create(
                session,
                obj_in={
                    "tenant_id": integ.tenant_id,
                    "payment_intent_id": None,
                    "kind": "unmatched_provider",
                    "status": "open",
                    "provider_ref": trans_id,
                    "message": "C2B confirmation without BillRefNumber/AccountReference",
                },
            )
            await session.commit()
            return ProcessResult(status="unmatched", message="C2B confirmation missing bill reference")

        intent = await payment_intent_crud.find_open_by_account_reference(
            session, integration_id=integ.id, account_reference=bill_ref
        )
        if not intent:
            from app.crud.reconciliation import reconciliation_crud
            await reconciliation_crud.create(
                session,
                obj_in={
                    "tenant_id": integ.tenant_id,
                    "payment_intent_id": None,
                    "kind": "unmatched_provider",
                    "status": "open",
                    "provider_ref": trans_id or bill_ref,
                    "message": f"C2B confirmation no open payment for reference {bill_ref}",
                },
            )
            await session.commit()
            return ProcessResult(status="unmatched", message=f"No open payment for {bill_ref}")

        if is_terminal(intent.status):
            return ProcessResult(
                status="duplicate",
                intent_id=intent.id,
                message="Already settled",
            )

        # Optional amount check → exception if mismatch
        amt = _c2b_amount_minor(data)
        if amt is not None and intent.amount_minor and abs(amt - intent.amount_minor) > 0:
            from app.crud.reconciliation import reconciliation_crud
            await reconciliation_crud.create(
                session,
                obj_in={
                    "tenant_id": intent.tenant_id,
                    "payment_intent_id": intent.id,
                    "kind": "amount_mismatch",
                    "status": "open",
                    "provider_ref": trans_id,
                    "message": f"C2B amount {amt} minor vs intent {intent.amount_minor}",
                },
            )
            await session.commit()
            return ProcessResult(
                status="amount_mismatch",
                intent_id=intent.id,
                message="Amount mismatch — exception opened",
            )

        # Move through provider_requested if still created
        if intent.status == "created":
            intent = await transition_payment_intent(
                session, intent, to_status="provider_requested"
            )
        await apply_payment_result(
            session, intent, status="succeeded", transaction_id=trans_id
        )
        await record_event(
            session,
            tenant_id=intent.tenant_id,
            integration_id=intent.integration_id,
            payment_intent_id=intent.id,
            category="callback",
            action="c2b.succeeded",
            message=f"C2B paid ref={bill_ref} trans={trans_id}",
            is_replayable=True,
        )
        return ProcessResult(
            status="succeeded",
            intent_id=intent.id,
            ResultCode="0",
            ResultDesc="C2B confirmation applied",
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
