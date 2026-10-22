"""Machine-to-machine credential hashing, token signing, and principal validation.

Client secrets are never stored in plaintext. Access tokens are short-lived and
every authenticated request re-checks persisted client and merchant status so
revocation takes effect immediately.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Callable, Sequence
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import Settings, get_settings
from app.models.merchants import M2MClient, Merchant

_HASH_ITERATIONS = 600_000
_TOKEN_TYPE = "machine"
_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True, slots=True)
class MachinePrincipal:
    """Verified merchant identity and permission scopes for one M2M request."""

    client_id: str
    merchant_id: UUID
    scopes: frozenset[str]


@dataclass(frozen=True, slots=True)
class CreatedClientCredentials:
    """New client record plus the one-time plaintext secret for the caller."""

    client: M2MClient
    client_secret: str


def _b64encode(value: bytes) -> str:
    """Encode bytes as unpadded URL-safe base64."""
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    """Decode unpadded URL-safe base64."""
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def hash_client_secret(secret: str, *, salt: bytes | None = None) -> str:
    """Hash a client secret using PBKDF2-HMAC-SHA256 with a random per-secret salt."""
    if len(secret) < 32:
        raise ValueError("Client secrets must contain at least 32 characters")
    salt_value = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", secret.encode("utf-8"), salt_value, _HASH_ITERATIONS)
    return "pbkdf2_sha256$" + str(_HASH_ITERATIONS) + "$" + _b64encode(salt_value) + "$" + _b64encode(digest)


def verify_client_secret(secret: str, encoded_hash: str) -> bool:
    """Constant-time verification for supported PBKDF2 client-secret hashes."""
    try:
        algorithm, iteration_text, salt_text, digest_text = encoded_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iteration_text)
        if iterations < 100_000 or iterations > 2_000_000:
            return False
        salt_value = _b64decode(salt_text)
        expected = _b64decode(digest_text)
        actual = hashlib.pbkdf2_hmac("sha256", secret.encode("utf-8"), salt_value, iterations)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError, UnicodeEncodeError):
        return False


async def create_m2m_client(
    session: AsyncSession,
    *,
    merchant_id: UUID,
    scopes: Sequence[str],
    expires_at: datetime | None = None,
) -> CreatedClientCredentials:
    """Persist a client with a hashed secret and return the plaintext secret once."""
    normalized_scopes = sorted(set(scopes))
    if not normalized_scopes or any(not scope or len(scope) > 80 for scope in normalized_scopes):
        raise ValueError("At least one valid scope is required")
    if expires_at is not None and (expires_at.tzinfo is None or expires_at.utcoffset() is None):
        raise ValueError("Client expiry must be timezone-aware")
    client_id = "nmc_" + secrets.token_urlsafe(24)
    client_secret = "nms_" + secrets.token_urlsafe(48)
    client = M2MClient(
        merchant_id=merchant_id,
        client_id=client_id,
        secret_hash=hash_client_secret(client_secret),
        scopes=normalized_scopes,
        status="active",
        expires_at=expires_at,
    )
    session.add(client)
    await session.flush()
    return CreatedClientCredentials(client=client, client_secret=client_secret)


def _signing_key(settings: Settings) -> bytes:
    """Resolve a non-default signing key and fail closed for unsafe production config."""
    raw = settings.secret_key.get_secret_value()
    development_key = "local-dev-secret-key-change-this-32chars"
    if settings.environment == "production" and raw == development_key:
        raise RuntimeError("SECRET_KEY must be explicitly configured in production")
    if len(raw.encode("utf-8")) < 32:
        raise RuntimeError("SECRET_KEY must contain at least 32 bytes")
    return raw.encode("utf-8")


def _json_segment(value: dict[str, object]) -> str:
    """Serialize a JWT segment deterministically."""
    raw = json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return _b64encode(raw)


def issue_machine_access_token(
    *,
    client_id: str,
    merchant_id: UUID,
    scopes: Sequence[str],
    settings: Settings | None = None,
    now: datetime | None = None,
) -> str:
    """Issue a compact HS256 bearer token for an already authenticated active client."""
    config = settings or get_settings()
    key = _signing_key(config)
    issued_at = int((now or datetime.now(UTC)).timestamp())
    expires_at = issued_at + config.machine_token_ttl_minutes * 60
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "typ": _TOKEN_TYPE,
        "aud": config.machine_token_audience,
        "sub": client_id,
        "client_id": client_id,
        "merchant_id": str(merchant_id),
        "scope": sorted(set(scopes)),
        "iat": issued_at,
        "exp": expires_at,
        "jti": secrets.token_urlsafe(16),
    }
    signing_input = _json_segment(header) + "." + _json_segment(payload)
    signature = hmac.new(key, signing_input.encode("ascii"), hashlib.sha256).digest()
    return signing_input + "." + _b64encode(signature)


def decode_machine_access_token(
    token: str,
    *,
    settings: Settings | None = None,
    now: datetime | None = None,
) -> MachinePrincipal:
    """Verify signature, expiry, audience, token type, and typed principal claims."""
    config = settings or get_settings()
    key = _signing_key(config)
    try:
        header_segment, payload_segment, signature_segment = token.split(".")
        signing_input = header_segment + "." + payload_segment
        supplied_signature = _b64decode(signature_segment)
        expected_signature = hmac.new(key, signing_input.encode("ascii"), hashlib.sha256).digest()
        if not hmac.compare_digest(supplied_signature, expected_signature):
            raise ValueError("Invalid token signature")
        header = json.loads(_b64decode(header_segment))
        payload = json.loads(_b64decode(payload_segment))
        if header.get("alg") != "HS256" or header.get("typ") != "JWT":
            raise ValueError("Unsupported token algorithm")
        if payload.get("typ") != _TOKEN_TYPE or payload.get("aud") != config.machine_token_audience:
            raise ValueError("Invalid token audience or type")
        current = int((now or datetime.now(UTC)).timestamp())
        issued_at = payload["iat"]
        expires_at = payload["exp"]
        if not isinstance(issued_at, int) or not isinstance(expires_at, int):
            raise ValueError("Invalid token timestamps")
        if expires_at <= current or issued_at > current + 30:
            raise ValueError("Token is expired or not yet valid")
        client_id = payload["client_id"]
        merchant_id = UUID(payload["merchant_id"])
        scopes = payload["scope"]
        if not isinstance(client_id, str) or not client_id or not isinstance(scopes, list):
            raise ValueError("Invalid token principal")
        if any(not isinstance(scope, str) for scope in scopes):
            raise ValueError("Invalid token scopes")
        if payload.get("sub") != client_id or not payload.get("jti"):
            raise ValueError("Invalid token identity")
        return MachinePrincipal(client_id=client_id, merchant_id=merchant_id, scopes=frozenset(scopes))
    except (KeyError, TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid machine access token") from exc


async def get_machine_principal(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> MachinePrincipal:
    """Authenticate a bearer token and re-check persisted client/merchant status."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="invalid_machine_credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthorized
    try:
        principal = decode_machine_access_token(credentials.credentials)
    except (ValueError, RuntimeError):
        raise unauthorized from None
    factory = getattr(request.app.state, "session_factory", None)
    if factory is None:
        raise HTTPException(status_code=503, detail="database_not_initialized")
    async with factory() as session:
        client_result = await session.exec(
            select(M2MClient).where(
                M2MClient.client_id == principal.client_id,
                M2MClient.merchant_id == principal.merchant_id,
                M2MClient.deleted_at.is_(None),
            )
        )
        client = client_result.first()
        merchant_result = await session.exec(
            select(Merchant).where(
                Merchant.id == principal.merchant_id,
                Merchant.deleted_at.is_(None),
            )
        )
        merchant = merchant_result.first()
        current = datetime.now(UTC)
        if (
            client is None
            or merchant is None
            or client.status != "active"
            or client.revoked_at is not None
            or (client.expires_at is not None and client.expires_at <= current)
            or merchant.status != "active"
            or not principal.scopes.issubset(set(client.scopes))
        ):
            raise unauthorized
    return principal


def require_scopes(*required_scopes: str) -> Callable[..., object]:
    """Build a FastAPI dependency that enforces every required scope."""
    async def dependency(
        principal: MachinePrincipal = Depends(get_machine_principal),
    ) -> MachinePrincipal:
        if not set(required_scopes).issubset(principal.scopes):
            raise HTTPException(status_code=403, detail="insufficient_scope")
        return principal

    return dependency
