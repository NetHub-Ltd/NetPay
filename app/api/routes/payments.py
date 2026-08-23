from __future__ import annotations
import json
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.api.deps import can_access_tenant, get_current_user, get_session
from app.api.routes.integrations import load_creds
from app.models.integration import Integration
from app.models.payment_intent import PaymentIntent
from app.models.user import User
from app.providers.mpesa import get_access_token, normalize_msisdn, stk_push
from app.schemas.payment import IntentCreate, IntentCreateResponse, IntentOut
from app.services.events import record_event
from app.services.processor import apply_payment_result

router = APIRouter(prefix="/v1/payment-intents", tags=["payments"])

@router.get("", response_model=list[IntentOut])
async def list_intents(session: Annotated[AsyncSession, Depends(get_session)], user: Annotated[User, Depends(get_current_user)]) -> list[PaymentIntent]:
    q = select(PaymentIntent).order_by(PaymentIntent.created_at.desc()).limit(80)
    if user.role != "admin":
        if not user.tenant_id:
            return []
        q = q.where(PaymentIntent.tenant_id == user.tenant_id)
    result = await session.exec(q)
    return list(result.all())

@router.get("/{intent_id}", response_model=IntentOut)
async def get_intent(intent_id: UUID, session: Annotated[AsyncSession, Depends(get_session)], user: Annotated[User, Depends(get_current_user)]) -> PaymentIntent:
    result = await session.exec(select(PaymentIntent).where(PaymentIntent.id == intent_id))
    intent = result.first()
    if not intent:
        raise HTTPException(status_code=404, detail="Not found")
    if not can_access_tenant(user, intent.tenant_id):
        raise HTTPException(status_code=403, detail="Forbidden")
    return intent

@router.post("", response_model=IntentCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_intent(body: IntentCreate, session: Annotated[AsyncSession, Depends(get_session)], user: Annotated[User, Depends(get_current_user)]) -> IntentCreateResponse:
    result = await session.exec(select(Integration).where(Integration.public_id == body.integration_public_id, Integration.deleted_at.is_(None)))  # type: ignore
    integ = result.first()
    if not integ:
        raise HTTPException(status_code=404, detail="Integration not found")
    if not can_access_tenant(user, integ.tenant_id):
        raise HTTPException(status_code=403, detail="Forbidden")
    phone = normalize_msisdn(body.phone)
    intent = PaymentIntent(
        tenant_id=integ.tenant_id, integration_id=integ.id, created_by=user.id,
        amount=body.amount, phone=phone, account_reference=body.account_reference or "PAY",
        description=body.description or "Payment",
        context_json=json.dumps(body.context) if body.context else None, status="created",
    )
    session.add(intent)
    await session.commit()
    await session.refresh(intent)
    await record_event(session, tenant_id=integ.tenant_id, integration_id=integ.id, payment_intent_id=intent.id,
                       category="intent", action="intent.created", message=f"STK {body.amount} KES → {phone}")
    creds = await load_creds(session, integ.id)
    token = await get_access_token(creds["consumer_key"], creds["consumer_secret"], integ.environment)  # type: ignore
    callback_url = integ.stk_callback_url or f"https://gateway.nethub.co.ke/mpesa/cb/{integ.public_id}/stk"
    try:
        stk = await stk_push(
            shortcode=integ.shortcode, passkey=creds["passkey"], phone=phone, amount=str(int(body.amount)),
            account_reference=body.account_reference or "PAY", description=body.description or "Payment",
            callback_url=callback_url, env=integ.environment, token=token,  # type: ignore
        )
        intent.status = "provider_requested"
        intent.provider_checkout_id = stk.get("checkout_request_id")
        intent.provider_merchant_id = stk.get("merchant_request_id")
        session.add(intent)
        await session.commit()
        await session.refresh(intent)
        await record_event(session, tenant_id=integ.tenant_id, integration_id=integ.id, payment_intent_id=intent.id,
                           category="intent", action="stk.requested", message=f"Checkout {intent.provider_checkout_id}")
    except Exception as exc:  # noqa: BLE001
        intent.status = "failed"
        intent.failure_reason = str(exc)[:512]
        session.add(intent)
        await session.commit()
        raise HTTPException(status_code=502, detail=f"Daraja STK error: {exc}") from exc
    return IntentCreateResponse(id=intent.id, status=intent.status, provider_checkout_id=intent.provider_checkout_id,
                                provider_merchant_id=intent.provider_merchant_id)

@router.post("/{intent_id}/simulate", response_model=IntentOut)
async def simulate_callback(intent_id: UUID, session: Annotated[AsyncSession, Depends(get_session)], user: Annotated[User, Depends(get_current_user)]) -> PaymentIntent:
    """Dev helper: mark intent succeeded without Daraja."""
    result = await session.exec(select(PaymentIntent).where(PaymentIntent.id == intent_id))
    intent = result.first()
    if not intent:
        raise HTTPException(status_code=404, detail="Not found")
    if not can_access_tenant(user, intent.tenant_id):
        raise HTTPException(status_code=403, detail="Forbidden")
    return await apply_payment_result(session, intent, status="succeeded", transaction_id="SIMULATED")
