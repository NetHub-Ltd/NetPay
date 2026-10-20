"""Optional merchant webhook destination management."""

import asyncio
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import MerchantPrincipal, require_scope
from app.crypto import encrypt_secret
from app.db import get_session
from app.models import EventDestination
from app.schemas import EventDestinationCreated, EventDestinationPublic, EventDestinationUpdate
from app.webhooks.url_validation import UnsafeWebhookURL, validate_public_https_url

router = APIRouter(prefix="/api/v1/event-destination", tags=["events"])


@router.put("", response_model=EventDestinationCreated)
async def set_event_destination(
    payload: EventDestinationUpdate,
    principal: MerchantPrincipal = Depends(require_scope("events:write")),
    session: AsyncSession = Depends(get_session),
) -> EventDestinationCreated:
    """Create or replace the merchant's single destination and rotate its secret."""
    try:
        await asyncio.to_thread(validate_public_https_url, payload.url)
    except UnsafeWebhookURL as exc:
        raise HTTPException(status_code=422, detail={"code": "unsafe_webhook_url", "message": str(exc)}) from exc

    result = await session.exec(
        select(EventDestination).where(EventDestination.merchant_id == principal.merchant_id)
    )
    destination = result.first()
    signing_secret = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    if destination is None:
        destination = EventDestination(
            merchant_id=principal.merchant_id,
            url=payload.url,
            signing_secret_ciphertext=encrypt_secret(signing_secret),
            enabled=True,
            created_at=now,
            updated_at=now,
        )
    else:
        destination.url = payload.url
        destination.signing_secret_ciphertext = encrypt_secret(signing_secret)
        destination.enabled = True
        destination.updated_at = now
    session.add(destination)
    await session.commit()
    await session.refresh(destination)
    return EventDestinationCreated(
        id=destination.id,
        url=destination.url,
        enabled=destination.enabled,
        created_at=destination.created_at,
        updated_at=destination.updated_at,
        signing_secret=signing_secret,
    )


@router.get("", response_model=EventDestinationPublic)
async def get_event_destination(
    principal: MerchantPrincipal = Depends(require_scope("events:read")),
    session: AsyncSession = Depends(get_session),
) -> EventDestination:
    result = await session.exec(
        select(EventDestination).where(EventDestination.merchant_id == principal.merchant_id)
    )
    destination = result.first()
    if destination is None:
        raise HTTPException(status_code=404, detail={"code": "event_destination_not_found", "message": "No webhook destination is configured"})
    return destination


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def disable_event_destination(
    principal: MerchantPrincipal = Depends(require_scope("events:write")),
    session: AsyncSession = Depends(get_session),
) -> Response:
    result = await session.exec(
        select(EventDestination).where(EventDestination.merchant_id == principal.merchant_id)
    )
    destination = result.first()
    if destination is not None:
        destination.enabled = False
        destination.updated_at = datetime.now(timezone.utc)
        session.add(destination)
        await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
