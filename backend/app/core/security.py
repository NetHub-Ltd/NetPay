"""Token validation and client-secret hashing.

End-user authentication is owned by Keycloak. NetPay validates access tokens
and never issues interactive login JWTs for humans.

In ENVIRONMENT=test (or when JWKS is not configured), HS256 tokens signed with
SECRET_KEY are accepted so unit tests do not need a live Keycloak.
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
from app.core.logging import logger

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
    """Mint an HS256 token for tests / local fallback when JWKS is unset."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=minutes or settings.access_token_expire_minutes
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": expire,
        "iss": settings.nethub_as_issuer or "https://test-keycloak/realms/nethub",
        "aud": settings.nethub_as_audience or "nethub-backend",
    }
    if extra:
        payload.update(extra)
    return jose_jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM_HS)


def _decode_hs256(token: str) -> dict[str, Any]:
    return jose_jwt.decode(
        token,
        settings.secret_key,
        algorithms=[ALGORITHM_HS],
        audience=settings.nethub_as_audience or "nethub-backend",
        options={"verify_aud": bool(settings.nethub_as_audience)},
    )


def _decode_keycloak_rs256(token: str) -> dict[str, Any]:
    """Validate against Keycloak JWKS (production path)."""
    if not settings.nethub_as_jwks_url or not settings.nethub_as_issuer:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Keycloak JWKS/issuer not configured",
        )
    try:
        import jwt as pyjwt
        from jwt import PyJWKClient
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PyJWT required for Keycloak validation",
        ) from exc

    try:
        jwks_client = PyJWKClient(
            uri=settings.nethub_as_jwks_url,
            cache_jwk_set=True,
            lifespan=300,
        )
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        return pyjwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.nethub_as_audience or "nethub-backend",
            issuer=settings.nethub_as_issuer,
            options={"verify_aud": True, "verify_iss": True},
            leeway=10,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Keycloak token validation failed: {}", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Validate a Bearer access token.

    - Production / configured JWKS: RS256 via Keycloak
    - Test or missing JWKS: HS256 signed with SECRET_KEY (test tokens only)
    """
    use_keycloak = (
        settings.nethub_as_enabled
        and bool(settings.nethub_as_jwks_url)
        and bool(settings.nethub_as_issuer)
        and not settings.is_test
    )
    if use_keycloak:
        return _decode_keycloak_rs256(token)

    try:
        return _decode_hs256(token)
    except JWTError as exc:
        logger.warning("HS256 token validation failed: {}", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc


def subject_as_uuid(payload: dict[str, Any]) -> UUID:
    raw = payload.get("sub")
    if raw is None:
        raise HTTPException(status_code=401, detail="Token missing sub")
    try:
        return UUID(str(raw))
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Token sub is not a UUID") from exc
