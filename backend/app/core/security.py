"""Secrets hashing and test-only token helpers.

NetPay does **not** validate Keycloak JWTs via JWKS.
Authentication is Keycloak; authorization + identity context come from
NetHub API when NetPay forwards the Bearer token.

Production path: no JWT crypto in NetPay.
Test path: HS256 tokens signed with SECRET_KEY exist only so unit tests
can run without a live NetHub/Keycloak.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

from fastapi import HTTPException, status
from jose import JWTError
from jose import jwt as jose_jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM_HS = "HS256"


def hash_password(password: str) -> str:
    """Hash a secret (OAuth client secrets only — not end-user passwords)."""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_test_access_token(
    subject: str,
    *,
    extra: Optional[dict[str, Any]] = None,
    minutes: Optional[int] = None,
) -> str:
    """Mint an HS256 token for unit tests only (ENVIRONMENT=test)."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=minutes or settings.access_token_expire_minutes
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": expire,
        "aud": "nethub-backend",
    }
    if extra:
        payload.update(extra)
    return jose_jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM_HS)


def decode_test_token(token: str) -> dict[str, Any]:
    """Decode HS256 test tokens. Production must not rely on this."""
    if not settings.is_test:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Local token decode is test-only; configure NETHUB_API_BASE_URL",
        )
    try:
        return jose_jwt.decode(
            token,
            settings.secret_key,
            algorithms=[ALGORITHM_HS],
            options={"verify_aud": False},
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc


def subject_as_uuid(raw: Any) -> UUID:
    if raw is None:
        raise HTTPException(status_code=401, detail="Missing subject")
    try:
        return UUID(str(raw))
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Subject is not a UUID") from exc
