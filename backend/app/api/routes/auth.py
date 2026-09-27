from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import get_current_user, get_session, require_admin
from app.core.logging import logger
from app.core.security import create_test_access_token, hash_password, verify_password
from app.crud.oauth_client import oauth_client_crud
from app.models.user import User
from app.schemas.auth import (
    OAuthClientCreate,
    OAuthClientOut,
    OAuthTokenRequest,
    TokenResponse,
    UserOut,
)
from app.services.ids import new_client_id, new_client_secret

router = APIRouter(tags=["auth"])


@router.post("/auth/login", include_in_schema=False)
async def login_removed() -> None:
    """Password login removed (P2 #25). Use Keycloak / NetHub SSO."""
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail=(
            "Password login has been removed. "
            "Authenticate with Keycloak and call NetPay with the access token "
            "(audience=nethub-backend)."
        ),
    )


@router.get("/auth/me", response_model=UserOut)
async def me(user: Annotated[User, Depends(get_current_user)]) -> User:
    return user


@router.post("/oauth/token", response_model=TokenResponse)
async def oauth_token(
    body: OAuthTokenRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TokenResponse:
    """
    Local client_credentials (M2M). Prefer Keycloak client credentials long-term.
    Issues an HS256 token that get_current_user recognises via the m2m claim.
    """
    if body.grant_type != "client_credentials":
        raise HTTPException(status_code=400, detail="unsupported_grant_type")
    client = await oauth_client_crud.get_active_by_client_id(session, body.client_id)
    if not client or not verify_password(body.client_secret, client.client_secret_hash):
        raise HTTPException(status_code=401, detail="invalid_client")
    token = create_test_access_token(
        str(client.id),
        extra={
            "role": "user",
            "tenant_id": str(client.tenant_id),
            "client_id": client.client_id,
            "m2m": True,
            "email": f"{client.client_id}@m2m.local",
        },
    )
    return TokenResponse(
        access_token=token,
        role="user",
        email=f"{client.client_id}@m2m.local",
        tenant_id=client.tenant_id,
    )


@router.post("/v1/oauth-clients", response_model=OAuthClientOut, status_code=201)
async def create_oauth_client(
    body: OAuthClientCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[User, Depends(require_admin)],
) -> OAuthClientOut:
    cid = new_client_id()
    secret = new_client_secret()
    await oauth_client_crud.create(
        session,
        obj_in={
            "tenant_id": body.tenant_id,
            "client_id": cid,
            "client_secret_hash": hash_password(secret),
            "name": body.name,
        },
    )
    await session.commit()
    return OAuthClientOut(
        client_id=cid,
        client_secret=secret,
        name=body.name,
        tenant_id=body.tenant_id,
    )
