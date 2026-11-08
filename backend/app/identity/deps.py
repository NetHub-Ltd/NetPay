"""FastAPI dependencies for human (IdP → NetHubKe) authentication."""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from app.identity.nethub_client import NetHubIdentityError, resolve_human
from app.identity.principal import HumanPrincipal


def _bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="bearer_token_required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization[7:].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="bearer_token_required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


async def get_human_principal(
    authorization: Annotated[str | None, Header()] = None,
) -> HumanPrincipal:
    """
    Human routes only: forward IdP Bearer to NetHubKe.
    Do not use for M2M merchant APIs (see payments.security.require_scopes).
    """
    token = _bearer_token(authorization)
    try:
        principal = await resolve_human(token)
    except NetHubIdentityError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None,
        ) from exc
    if not principal.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="account_disabled")
    return principal
