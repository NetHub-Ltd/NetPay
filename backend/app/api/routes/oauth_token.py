"""Machine client_credentials token endpoint."""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import get_session
from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.crud.oauth_client import oauth_client_crud

router = APIRouter(prefix="/v1/oauth", tags=["oauth"])


class TokenJsonBody(BaseModel):
    grant_type: str = "client_credentials"
    client_id: str = Field(min_length=3, max_length=64)
    client_secret: str = Field(min_length=8, max_length=256)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    tenant_id: str
    client_id: str


async def _issue_token(
    session: AsyncSession, client_id: str, client_secret: str, grant_type: str
) -> TokenResponse:
    if (grant_type or "client_credentials") != "client_credentials":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="unsupported_grant_type",
        )
    client = await oauth_client_crud.get_active_by_client_id(session, client_id.strip())
    if client is None or not verify_password(client_secret, client.client_secret_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_client")

    expires = int(settings.access_token_expire_minutes) * 60
    token = create_access_token(
        subject=client.client_id,
        extra={
            "typ": "machine",
            "client_id": client.client_id,
            "tenant_id": str(client.tenant_id),
            "name": client.name,
        },
    )
    return TokenResponse(
        access_token=token,
        expires_in=expires,
        tenant_id=str(client.tenant_id),
        client_id=client.client_id,
    )


async def _parse_credentials(request: Request) -> tuple[str, str, str]:
    ctype = (request.headers.get("content-type") or "").lower()
    if "application/json" in ctype:
        try:
            raw: Any = await request.json()
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail="invalid_request") from exc
        body = TokenJsonBody.model_validate(raw)
        return body.client_id, body.client_secret, body.grant_type
    if "application/x-www-form-urlencoded" in ctype or "multipart/form-data" in ctype:
        form = await request.form()
        cid = str(form.get("client_id") or "")
        secret = str(form.get("client_secret") or "")
        grant = str(form.get("grant_type") or "client_credentials")
        if not cid or not secret:
            raise HTTPException(status_code=400, detail="invalid_request")
        return cid, secret, grant
    # Default: try JSON body
    try:
        raw = await request.json()
        body = TokenJsonBody.model_validate(raw)
        return body.client_id, body.client_secret, body.grant_type
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="invalid_request") from exc


@router.post("/token", response_model=TokenResponse)
async def oauth_token(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TokenResponse:
    """Exchange client_id + client_secret for a Bearer token (client_credentials)."""
    client_id, client_secret, grant_type = await _parse_credentials(request)
    return await _issue_token(session, client_id, client_secret, grant_type)
