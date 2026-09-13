from __future__ import annotations

from app.core.config import settings
from app.services.edge_urls import integration_callback_urls
import json
from decimal import Decimal
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import can_access_tenant, get_current_user, get_session
from app.api.routes.integrations import load_creds
from app.crud.integration import integration_crud
from app.crud.payment_intent import payment_intent_crud
from app.domain.payment_status import IllegalTransitionError, major_units_from_minor
from app.models.payment_intent import PaymentIntent
from app.models.user import User
from app.providers.mpesa import StkPushError, get_access_token, normalize_msisdn, stk_push
from app.crud.ledger import ledger_entry_crud
from app.schemas.ledger import LedgerEntryOut
from app.schemas.payment import IntentCreate, IntentCreateResponse, IntentDetailOut, IntentOut
from app.services.events import record_event
from app.services.processor import apply_payment_result
from app.services.outbound_audit import redact_provider_payload
from app.services.transitions import transition_payment_intent

router = APIRouter(prefix="/v1/payment-intents", tags=["payments"])


@router.get("", response_model=list[IntentOut])
async def list_intents(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[PaymentIntent]:
    return list(
        await payment_intent_crud.list_for_user(
            session,
            tenant_id=user.tenant_id,
            is_admin=user.role == "admin",
        )
    )


@router.get("/{intent_id}", response_model=IntentDetailOut)
async def get_intent(
    intent_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> IntentDetailOut:
    intent = await payment_intent_crud.get(session, intent_id)
    if not intent:
        raise HTTPException(status_code=404, detail="Not found")
    if not can_access_tenant(user, intent.tenant_id):
        raise HTTPException(status_code=403, detail="Forbidden")
    meta = None
    raw_meta = intent.metadata_json or intent.context_json
    if raw_meta:
        try:
            meta = json.loads(raw_meta)
        except Exception:
            meta = None
    return IntentDetailOut(
        id=intent.id,
        tenant_id=intent.tenant_id,
        integration_id=intent.integration_id,
        status=intent.status,
        amount_minor=intent.amount_minor,
        amount=intent.amount,
        currency=intent.currency,
        phone=intent.phone,
        account_reference=intent.account_reference,
        description=intent.description,
        provider_checkout_id=intent.provider_checkout_id,
        provider_merchant_id=intent.provider_merchant_id,
        provider_transaction_id=intent.provider_transaction_id,
        failure_reason=intent.failure_reason,
        idempotency_key=intent.idempotency_key,
        status_callback_url=intent.status_callback_url,
        created_at=intent.created_at,
        metadata=meta,
        stk_request_json=intent.stk_request_json,
        stk_response_json=intent.stk_response_json,
    )


@router.post("", response_model=IntentCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_intent(
    body: IntentCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    idempotency_key: Annotated[Optional[str], Header(alias="Idempotency-Key")] = None,
) -> IntentCreateResponse:
    """
    Create a collection intent and initiate STK Push.

    Requires header Idempotency-Key. Replaying the same key for the same tenant
    returns the original intent without a second provider call.
    """
    if not idempotency_key or not idempotency_key.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key header is required",
        )
    key = idempotency_key.strip()[:128]

    integ = await integration_crud.get_by_public_id(session, body.integration_public_id)
    if not integ:
        raise HTTPException(status_code=404, detail="Integration not found")
    if not can_access_tenant(user, integ.tenant_id):
        raise HTTPException(status_code=403, detail="Forbidden")

    existing = await payment_intent_crud.get_by_idempotency(
        session, tenant_id=integ.tenant_id, idempotency_key=key
    )
    if existing:
        return IntentCreateResponse(
            id=existing.id,
            status=existing.status,
            amount_minor=existing.amount_minor,
            currency=existing.currency,
            provider_checkout_id=existing.provider_checkout_id,
            provider_merchant_id=existing.provider_merchant_id,
            message="Idempotent replay",
            idempotent_replay=True,
        )

    try:
        major = major_units_from_minor(body.amount_minor, currency=body.currency if hasattr(body, "currency") else "KES")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    phone = normalize_msisdn(body.phone)
    amount_major = Decimal(major)
    intent = await payment_intent_crud.create(
        session,
        obj_in={
            "tenant_id": integ.tenant_id,
            "integration_id": integ.id,
            "created_by": user.id,
            "intent_type": "collection",
            "status": "created",
            "amount": amount_major,
            "amount_minor": body.amount_minor,
            "currency": "KES",
            "phone": phone,
            "account_reference": body.account_reference or "PAY",
            "description": body.description or "Payment",
            "context_json": json.dumps(body.context) if body.context else None,
            "metadata_json": json.dumps(body.metadata if body.metadata is not None else body.context)
            if (body.metadata is not None or body.context is not None)
            else None,
            "status_callback_url": body.status_callback_url,
            "provider": "mpesa",
            "idempotency_key": key,
        },
    )
    await session.commit()
    await session.refresh(intent)

    await record_event(
        session,
        tenant_id=integ.tenant_id,
        integration_id=integ.id,
        payment_intent_id=intent.id,
        category="intent",
        action="intent.created",
        message=f"STK {body.amount_minor} minor → {phone}",
    )

    creds = await load_creds(session, integ.id)
    # CallBackURL always edge (or explicit integration override that should still be edge-hosted)
    callback_url = integ.stk_callback_url or integration_callback_urls(integ.public_id)["stk"]
    tx_type = (
        "CustomerBuyGoodsOnline"
        if (integ.type or "").lower() == "till"
        else "CustomerPayBillOnline"
    )
    try:
        token = await get_access_token(
            creds["consumer_key"],
            creds["consumer_secret"],
            integ.environment,  # type: ignore[arg-type]
            session=session,
            tenant_id=integ.tenant_id,
            integration_id=integ.id,
            payment_intent_id=intent.id,
        )
        stk = await stk_push(
            shortcode=integ.shortcode,
            passkey=creds["passkey"],
            phone=phone,
            amount=str(major),
            account_reference=body.account_reference or "PAY",
            description=body.description or "Payment",
            callback_url=callback_url,
            env=integ.environment,  # type: ignore[arg-type]
            token=token,
            transaction_type=tx_type,
            session=session,
            tenant_id=integ.tenant_id,
            integration_id=integ.id,
            payment_intent_id=intent.id,
        )
        # Persist redacted request + full response on intent
        req_json = json.dumps(stk.get("request_body") or {})
        resp_json = json.dumps(stk.get("raw") or {})
        intent.stk_request_json = req_json
        intent.stk_response_json = resp_json
        session.add(intent)
        checkout_id = stk.get("checkout_request_id")
        try:
            intent = await transition_payment_intent(
                session,
                intent,
                to_status="provider_requested",
                provider_checkout_id=checkout_id,
                provider_merchant_id=stk.get("merchant_request_id"),
            )
        except IllegalTransitionError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        await session.commit()
        await session.refresh(intent)
        await record_event(
            session,
            tenant_id=integ.tenant_id,
            integration_id=integ.id,
            payment_intent_id=intent.id,
            category="intent",
            action="stk.requested",
            message=f"Checkout {intent.provider_checkout_id}",
        )
    except HTTPException:
        raise
    except StkPushError as exc:
        try:
            if exc.request_body is not None:
                intent.stk_request_json = json.dumps(exc.request_body)
            intent.stk_response_json = json.dumps(exc.raw or {"error": str(exc)})
            session.add(intent)
            intent = await transition_payment_intent(
                session,
                intent,
                to_status="failed",
                failure_reason=str(exc)[:512],
            )
            await session.commit()
        except IllegalTransitionError:
            await session.rollback()
        raise HTTPException(status_code=502, detail=f"Daraja STK error: {exc}") from exc
    except Exception as exc:  # noqa: BLE001
        try:
            intent.stk_response_json = json.dumps({"error": str(exc)[:1500]})
            session.add(intent)
            intent = await transition_payment_intent(
                session,
                intent,
                to_status="failed",
                failure_reason=str(exc)[:512],
            )
            await session.commit()
        except IllegalTransitionError:
            await session.rollback()
        raise HTTPException(status_code=502, detail=f"Daraja STK error: {exc}") from exc

    return IntentCreateResponse(
        id=intent.id,
        status=intent.status,
        amount_minor=intent.amount_minor,
        currency=intent.currency,
        provider_checkout_id=intent.provider_checkout_id,
        provider_merchant_id=intent.provider_merchant_id,
    )




@router.get("/{intent_id}/ledger", response_model=list[LedgerEntryOut])
async def list_intent_ledger(
    intent_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> list:
    """Append-only ledger rows for a payment intent (tenant-scoped)."""
    intent = await payment_intent_crud.get(session, intent_id)
    if not intent:
        raise HTTPException(status_code=404, detail="Not found")
    if not can_access_tenant(user, intent.tenant_id):
        raise HTTPException(status_code=403, detail="Forbidden")
    return list(await ledger_entry_crud.list_for_intent(session, payment_intent_id=intent_id))

@router.post("/{intent_id}/simulate", response_model=IntentOut)
async def simulate_callback(
    intent_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> PaymentIntent:
    """Dev helper: mark intent succeeded without Daraja."""
    intent = await payment_intent_crud.get(session, intent_id)
    if not intent:
        raise HTTPException(status_code=404, detail="Not found")
    if not can_access_tenant(user, intent.tenant_id):
        raise HTTPException(status_code=403, detail="Forbidden")
    return await apply_payment_result(session, intent, status="succeeded", transaction_id="SIMULATED")
