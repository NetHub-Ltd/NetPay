from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import can_access_tenant, get_current_user, get_session, user_can_access_tenant
from app.crud.integration import credential_crud, integration_crud
from app.models.integration import Integration
from app.schemas.principal import Principal
from app.providers.mpesa import get_access_token_meta, redact_token, register_c2b_urls
from app.schemas.integration import IntegrationCreate, IntegrationOut, RegisterUrlsRequest
from app.services.events import record_event
from app.services.ids import new_id

router = APIRouter(prefix="/v1/integrations", tags=["integrations"])


async def load_creds(session: AsyncSession, integration_id: UUID) -> dict[str, str]:
    return await credential_crud.map_for_integration(session, integration_id)


@router.get("", response_model=list[IntegrationOut])
async def list_integrations(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[Principal, Depends(get_current_user)],
    tenant_id: UUID | None = None,
) -> list[Integration]:
    """Optional tenant_id scopes shortcodes to one business."""
    if tenant_id is not None:
        if not await user_can_access_tenant(session, user, tenant_id):
            raise HTTPException(status_code=403, detail="Forbidden")
        return list(
            await integration_crud.list_active(
                session, tenant_id=tenant_id, is_admin=False
            )
        )
    if user.is_admin:
        return list(
            await integration_crud.list_active(
                session, tenant_id=None, is_admin=True
            )
        )
    from sqlmodel import col, or_, select
    from app.models.tenant import Tenant

    clauses = [col(Tenant.created_by) == user.id]
    if user.tenant_id is not None:
        clauses.append(col(Tenant.id) == user.tenant_id)
    stmt = (
        select(Tenant.id)
        .where(col(Tenant.deleted_at).is_(None))
        .where(or_(*clauses))
    )
    tenant_ids = list((await session.exec(stmt)).all())
    if not tenant_ids:
        return []
    items: list[Integration] = []
    for tid in tenant_ids:
        items.extend(
            await integration_crud.list_active(
                session, tenant_id=tid, is_admin=False
            )
        )
    return items


@router.get("/{integration_id}", response_model=IntegrationOut)
async def get_integration(
    integration_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[Principal, Depends(get_current_user)],
) -> Integration:
    integ = await integration_crud.get(session, integration_id)
    if not integ or getattr(integ, "deleted_at", None) is not None:
        raise HTTPException(status_code=404, detail="Shortcode not found")
    if not await user_can_access_tenant(session, user, integ.tenant_id):
        raise HTTPException(status_code=403, detail="Forbidden")
    return integ


@router.post("", response_model=IntegrationOut, status_code=status.HTTP_201_CREATED)
async def create_integration(
    body: IntegrationCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[Principal, Depends(get_current_user)],
) -> Integration:
    if not await user_can_access_tenant(session, user, body.tenant_id):
        raise HTTPException(status_code=403, detail="Forbidden")
    from app.crud.tenant import tenant_crud
    biz = await tenant_crud.get(session, body.tenant_id)
    if not biz or getattr(biz, "deleted_at", None) is not None:
        raise HTTPException(status_code=404, detail="Business not found")
    if (biz.status or "").lower() != "active":
        raise HTTPException(
            status_code=400,
            detail="This business is inactive. Activate it before adding shortcodes.",
        )

    # Validate Daraja credentials for the chosen environment before persisting.
    try:
        _token, expires_in = await get_access_token_meta(
            body.consumer_key.strip(),
            body.consumer_secret.strip(),
            body.environment,  # type: ignore[arg-type]
            session=session,
            tenant_id=body.tenant_id,
            skip_cache=True,  # always hit Daraja when saving credentials
        )
        from app.core.logging import logger
        logger.info(
            "Credential check before shortcode save env={} token_redacted={} expires_in={}",
            body.environment,
            redact_token(_token),
            expires_in,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=400,
            detail=(
                "Could not verify M-Pesa API credentials for this environment. "
                f"Check consumer key/secret and sandbox vs live. ({str(exc)[:240]})"
            ),
        ) from exc

    pub = new_id("gw")
    integ = await integration_crud.create(
        session,
        obj_in={
            "tenant_id": body.tenant_id,
            "public_id": pub,
            "shortcode": body.shortcode,
            "type": body.type,
            "environment": body.environment,
            "confirmation_url": body.confirmation_url,
            "validation_url": body.validation_url,
            "stk_callback_url": body.stk_callback_url,
            "status": "pending_setup",
        },
    )
    await session.commit()
    await session.refresh(integ)
    for kind, val in [
        ("consumer_key", body.consumer_key),
        ("consumer_secret", body.consumer_secret),
        ("passkey", body.passkey),
    ]:
        await credential_crud.create(
            session,
            obj_in={"integration_id": integ.id, "kind": kind, "value": val},
        )
    await session.commit()
    await record_event(
        session,
        tenant_id=body.tenant_id,
        integration_id=integ.id,
        category="integration",
        action="integration.created",
        message=f"Integration {pub}",
    )
    return integ


@router.post("/{integration_id}/register-urls", response_model=dict)
async def register_urls(
    integration_id: UUID,
    body: RegisterUrlsRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[Principal, Depends(get_current_user)],
) -> dict[str, Any]:
    integ = await integration_crud.get(session, integration_id)
    if not integ:
        raise HTTPException(status_code=404, detail="Not found")
    if not await user_can_access_tenant(session, user, integ.tenant_id):
        raise HTTPException(status_code=403, detail="Forbidden")
    creds = await load_creds(session, integ.id)
    if not creds.get("consumer_key") or not creds.get("consumer_secret"):
        raise HTTPException(
            status_code=400,
            detail="Missing Daraja consumer key/secret for this shortcode. Edit credentials and try again.",
        )
    try:
        token, expires_in = await get_access_token_meta(
            creds["consumer_key"],
            creds["consumer_secret"],
            integ.environment,  # type: ignore[arg-type]
            session=session,
            tenant_id=integ.tenant_id,
            integration_id=integ.id,
            skip_cache=True,
        )
        from app.core.logging import logger
        logger.info(
            "C2B register pre-flight OAuth env={} integration={} token_redacted={} expires_in={}",
            integ.environment,
            integration_id,
            redact_token(token),
            expires_in,
        )
        result = await register_c2b_urls(
            shortcode=integ.shortcode,
            confirmation_url=body.confirmation_url,
            validation_url=body.validation_url,
            response_type=body.response_type,
            env=integ.environment,  # type: ignore[arg-type]
            token=token,
            session=session,
            tenant_id=integ.tenant_id,
            integration_id=integ.id,
        )
    except RuntimeError as exc:
        from app.core.logging import logger
        msg = str(exc)
        logger.exception("register-urls failed integration={} err={}", integration_id, msg)
        source = "daraja"
        stage = "c2b_registerurl"
        if "OAuth" in msg or "oauth" in msg.lower():
            stage = "oauth"
        elif "must use HTTPS" in msg or "must be an absolute" in msg or "ResponseType must" in msg:
            source = "netpay"
            stage = "preflight"
        elif "HTTP" in msg and "failed" in msg.lower():
            source = "network"
        detail = {
            "message": msg[:600],
            "source": source,
            "stage": stage,
            "hint": (
                "NetPay rejected the request before calling Daraja."
                if source == "netpay"
                else "HTTP/transport problem reaching Safaricom — often sandbox outage."
                if source == "network"
                else "Safaricom/Daraja rejected or errored. Sandbox is often unstable; retry later."
            ),
            "environment": integ.environment,
            "shortcode": integ.shortcode,
        }
        raise HTTPException(status_code=502, detail=detail) from exc
    await integration_crud.update(
        session,
        db_obj=integ,
        obj_in={
            "confirmation_url": body.confirmation_url,
            "validation_url": body.validation_url,
            "status": "connected",
        },
    )
    await session.commit()
    await record_event(
        session,
        tenant_id=integ.tenant_id,
        integration_id=integ.id,
        category="integration",
        action="c2b.urls_registered",
        message="Daraja C2B URLs registered",
    )
    return {
        "ok": True,
        "message": "C2B confirmation and validation URLs registered with Daraja.",
        "daraja": result,
        "oauth": {
            "token_redacted": redact_token(token),
            "expires_in": expires_in,
            "environment": integ.environment,
        },
        "urls": {
            "confirmation_url": body.confirmation_url,
            "validation_url": body.validation_url,
            "response_type": body.response_type,
        },
    }






@router.post("/{integration_id}/path-check", response_model=dict)
async def path_check(
    integration_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[Principal, Depends(get_current_user)],
) -> dict[str, Any]:
    """Prove NetPay side without relying on Daraja registerurl uptime."""
    import httpx
    from app.core.config import settings
    from app.core.logging import logger
    from app.services.edge_status import get_edge_connection_status
    from app.services.edge_urls import integration_callback_urls
    from app.services.live_hub import publish_notification

    integ = await integration_crud.get(session, integration_id)
    if not integ or getattr(integ, "deleted_at", None) is not None:
        raise HTTPException(status_code=404, detail="Not found")
    if not await user_can_access_tenant(session, user, integ.tenant_id):
        raise HTTPException(status_code=403, detail="Forbidden")

    steps: list[dict[str, Any]] = []
    overall_ok = True

    oauth_step: dict[str, Any] = {"id": "oauth", "label": "Daraja login (OAuth)"}
    try:
        creds = await load_creds(session, integ.id)
        token, expires_in = await get_access_token_meta(
            creds["consumer_key"],
            creds["consumer_secret"],
            integ.environment,  # type: ignore[arg-type]
            session=session,
            tenant_id=integ.tenant_id,
            integration_id=integ.id,
            skip_cache=True,
        )
        oauth_step.update(
            {
                "ok": True,
                "source": "daraja",
                "token_redacted": redact_token(token),
                "expires_in": expires_in,
                "environment": integ.environment,
            }
        )
    except Exception as exc:  # noqa: BLE001
        overall_ok = False
        oauth_step.update(
            {
                "ok": False,
                "source": "daraja",
                "error": str(exc)[:400],
                "hint": "Credentials or Daraja OAuth failed — not NetPay business logic.",
            }
        )
    steps.append(oauth_step)

    urls = integration_callback_urls(integ.public_id)
    steps.append(
        {
            "id": "urls",
            "label": "Callback URLs NetPay would send to Daraja",
            "ok": True,
            "source": "netpay",
            "urls": urls,
            "edge_base": settings.edge_public_base_url.rstrip("/"),
        }
    )

    edge = await get_edge_connection_status(session)
    edge_ok = edge.get("status") in ("connected", "quiet", "never")
    if edge.get("status") == "errors":
        overall_ok = False
        edge_ok = False
    steps.append(
        {
            "id": "edge_inbound",
            "label": "Edge → NetPay (recent inbound)",
            "ok": edge_ok,
            "source": "netpay",
            "edge": edge,
            "hint": edge.get("label"),
        }
    )

    probe: dict[str, Any] = {"id": "edge_http", "label": "HTTP reach edge public base", "source": "network"}
    try:
        base = settings.edge_public_base_url.rstrip("/")
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            res = await client.get(base)
        probe.update({"ok": res.status_code < 500, "status_code": res.status_code, "url": base})
        if res.status_code >= 500:
            overall_ok = False
    except Exception as exc:  # noqa: BLE001
        overall_ok = False
        probe.update({"ok": False, "error": str(exc)[:300], "url": settings.edge_public_base_url})
    steps.append(probe)

    try:
        await publish_notification(
            title="Path check",
            body=f"Live channel OK for shortcode {integ.shortcode}. If you see this toast, NetPay → browser works.",
            level="success" if overall_ok else "info",
            tenant_id=integ.tenant_id,
            intent_id=None,
            href=f"/integrations/{integ.id}",
            status="path_check",
        )
        steps.append(
            {
                "id": "live_toast",
                "label": "Live notification to this session",
                "ok": True,
                "source": "netpay",
                "hint": "You should see a toast now. If not, WebSocket may be offline.",
            }
        )
    except Exception as exc:  # noqa: BLE001
        overall_ok = False
        steps.append({"id": "live_toast", "label": "Live notification", "ok": False, "source": "netpay", "error": str(exc)[:200]})

    logger.info("path-check integration={} overall_ok={}", integration_id, overall_ok)
    return {
        "ok": overall_ok,
        "message": (
            "NetPay-side checks look healthy. Daraja registerurl can still fail when sandbox is down."
            if overall_ok
            else "One or more checks failed — see steps for source (netpay vs daraja vs network)."
        ),
        "steps": steps,
        "how_to_read": {
            "netpay": "Our validation or infrastructure",
            "daraja": "Safaricom OAuth or registerurl response",
            "network": "Transport/DNS/TLS to edge or Safaricom",
        },
    }

@router.post("/{integration_id}/disconnect", response_model=dict)
async def disconnect_urls(
    integration_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[Principal, Depends(get_current_user)],
) -> dict[str, Any]:
    """
    Clear NetPay's record of C2B URL registration (status → pending_setup).

    Daraja has no public unregister API. In sandbox you can re-register new URLs.
    In production, changing registered URLs requires Safaricom support.
    This only updates NetPay state so the product no longer treats the shortcode as connected.
    """
    integ = await integration_crud.get(session, integration_id)
    if not integ or getattr(integ, "deleted_at", None) is not None:
        raise HTTPException(status_code=404, detail="Not found")
    if not await user_can_access_tenant(session, user, integ.tenant_id):
        raise HTTPException(status_code=403, detail="Forbidden")
    await integration_crud.update(
        session,
        db_obj=integ,
        obj_in={
            "confirmation_url": None,
            "validation_url": None,
            "status": "pending_setup",
        },
    )
    await session.commit()
    await record_event(
        session,
        tenant_id=integ.tenant_id,
        integration_id=integ.id,
        category="integration",
        action="c2b.urls_disconnected",
        message="Local C2B URL registration cleared (Daraja may still hold previous URLs)",
    )
    return {
        "ok": True,
        "message": (
            "NetPay no longer treats this shortcode as connected. "
            "Sandbox: re-register anytime. Production: Daraja may still send to old URLs "
            "until Safaricom clears them."
        ),
        "environment": integ.environment,
    }

@router.delete("/{integration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_integration(
    integration_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[Principal, Depends(get_current_user)],
) -> None:
    """Retire a paybill/till setup (soft-delete). Callbacks for old checkouts may still settle."""
    integ = await integration_crud.get(session, integration_id)
    if not integ or getattr(integ, "deleted_at", None) is not None:
        raise HTTPException(status_code=404, detail="Not found")
    if not await user_can_access_tenant(session, user, integ.tenant_id):
        raise HTTPException(status_code=403, detail="Forbidden")
    await integration_crud.soft_delete(session, id=integration_id)
    await session.commit()
    await record_event(
        session,
        tenant_id=integ.tenant_id,
        integration_id=integ.id,
        category="integration",
        action="integration.retired",
        message=f"Retired shortcode {integ.shortcode} ({integ.public_id})",
    )
