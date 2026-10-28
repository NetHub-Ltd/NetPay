"""M2M bearer tokens and credential encryption for application-owned APIs."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import Depends, Header, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import get_settings
from app.core.database import get_session
from app.models.merchants import M2MClient, Merchant


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def hash_client_secret(secret: str, *, salt: bytes | None = None) -> str:
    """Hash a provisioned client secret with PBKDF2; never store the secret itself."""
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", secret.encode(), salt, 310_000)
    return f"pbkdf2_sha256$310000$" + _b64(salt) + "$" + _b64(digest)


def verify_client_secret(secret: str, encoded: str) -> bool:
    """Constant-time verification of the stored PBKDF2 client-secret hash."""
    try:
        algorithm, rounds, salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", secret.encode(), _unb64(salt), int(rounds))
        return hmac.compare_digest(_b64(digest), expected)
    except (ValueError, TypeError):
        return False


def _signing_secret() -> bytes:
    configured = get_settings().m2m_token_signing_secret
    if configured is None or not configured.get_secret_value():
        raise HTTPException(status_code=503, detail="m2m_auth_not_configured")
    return configured.get_secret_value().encode()


def issue_access_token(
    client: M2MClient,
    merchant: Merchant,
    lifetime_seconds: int = 900,
    scopes: list[str] | None = None,
) -> str:
    """Issue a short-lived HS256 JWT scoped to one active M2M client and merchant."""
    now = int(datetime.now(UTC).timestamp())
    header = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    payload = _b64(json.dumps({
        "iss": "netpay",
        "aud": "netpay-api",
        "sub": client.client_id,
        "client_id": str(client.id),
        "merchant_id": str(merchant.id),
        "scope": " ".join(client.scopes if scopes is None else scopes),
        "iat": now,
        "nbf": now,
        "exp": now + lifetime_seconds,
    }, separators=(",", ":"), sort_keys=True).encode())
    signing_input = f"{header}.{payload}".encode("ascii")
    signature = hmac.new(_signing_secret(), signing_input, hashlib.sha256).digest()
    return f"{header}.{payload}.{_b64(signature)}"


def decode_access_token(token: str) -> dict[str, Any]:
    """Verify signature, issuer, audience and temporal claims before trusting identity."""
    try:
        header, payload, signature = token.split(".")
        signing_input = f"{header}.{payload}".encode("ascii")
        expected = hmac.new(_signing_secret(), signing_input, hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _unb64(signature)):
            raise ValueError
        header_data = json.loads(_unb64(header))
        claims = json.loads(_unb64(payload))
        now = int(datetime.now(UTC).timestamp())
        if header_data != {"alg": "HS256", "typ": "JWT"}:
            raise ValueError
        if claims.get("iss") != "netpay" or claims.get("aud") != "netpay-api":
            raise ValueError
        if int(claims.get("exp", 0)) <= now or int(claims.get("nbf", 0)) > now:
            raise ValueError
        if not claims.get("sub") or not claims.get("client_id") or not claims.get("merchant_id"):
            raise ValueError
        return claims
    except HTTPException:
        raise
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=401, detail="invalid_bearer_token") from exc



class Principal:
    """Authenticated merchant/client scope derived only from a verified token."""

    def __init__(self, claims: dict[str, Any], client: M2MClient) -> None:
        self.client = client
        self.client_id = client.id
        self.merchant_id = client.merchant_id
        self.scopes = frozenset(client.scopes)


def require_scopes(*required_scopes: str):
    """Build a dependency that validates a bearer token and reloads current client state."""
    async def dependency(
        request: Request,
        authorization: str | None = Header(default=None),
        session: AsyncSession = Depends(get_session),
    ) -> Principal:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="bearer_token_required", headers={"WWW-Authenticate": "Bearer"})
        claims = decode_access_token(authorization[7:].strip())
        try:
            client_uuid = UUID(claims["client_id"])
        except (ValueError, TypeError):
            raise HTTPException(status_code=401, detail="invalid_bearer_token") from None
        client = await session.get(M2MClient, client_uuid)
        if client is None or client.client_id != claims["sub"] or client.status != "active" or client.revoked_at is not None:
            raise HTTPException(status_code=401, detail="m2m_client_inactive")
        now = datetime.now(UTC)
        if client.expires_at is not None and client.expires_at <= now:
            raise HTTPException(status_code=401, detail="m2m_client_expired")
        if str(client.merchant_id) != claims["merchant_id"]:
            raise HTTPException(status_code=401, detail="m2m_scope_mismatch")
        merchant = await session.get(Merchant, client.merchant_id)
        if merchant is None or merchant.status != "active" or merchant.deleted_at is not None:
            raise HTTPException(status_code=403, detail="merchant_inactive")
        token_scopes = set(str(claims.get("scope", "")).split())
        if not token_scopes.issubset(set(client.scopes)) or not set(required_scopes).issubset(token_scopes):
            raise HTTPException(status_code=403, detail="insufficient_scope")
        return Principal(claims, client)
    return dependency
