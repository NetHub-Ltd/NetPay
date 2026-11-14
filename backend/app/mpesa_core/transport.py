"""Bounded asynchronous HTTP transport and OAuth lifecycle for Daraja."""
from __future__ import annotations

import asyncio
import base64
import hashlib
import json
from collections import OrderedDict
from typing import Any

import httpx
from loguru import logger
from pydantic import SecretStr

from app.mpesa_core.errors import (
    AmbiguousOutcome,
    InvalidRequest,
    MalformedProviderResponse,
    MissingCredential,
    OAuthError,
    ProviderRejected,
    RetryDisposition,
    TransportFailure,
)
from app.mpesa_core.schemas import DarajaOperation, IntegrationContext
from app.mpesa_core.validation import validate_context


_SANDBOX = "https://sandbox.safaricom.co.ke"
_PRODUCTION = "https://api.safaricom.co.ke"
_MAX_RESPONSE_BYTES = 1_000_000
_RESPONSE_CHUNK_BYTES = 64 * 1024
_MAX_CACHED_TOKENS = 1_024
_TOKEN_LOCK_STRIPES = 64
_TOKEN_SAFETY_MARGIN_SECONDS = 30


class _ResponseTooLarge(Exception):
    """Raised when a provider response exceeds the in-memory read limit."""


class DarajaTransport:
    """Own pooled HTTP access, bounded OAuth cache, and safe error mapping."""

    def __init__(
        self,
        settings: object | None = None,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        timeout = (
            timeout_seconds
            if timeout_seconds is not None
            else getattr(settings, "mpesa_http_timeout_seconds", 10.0)
        )
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout, connect=min(timeout, 5.0)),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            transport=transport,
        )
        self._tokens: OrderedDict[str, tuple[str, float]] = OrderedDict()
        self._token_locks = tuple(asyncio.Lock() for _ in range(_TOKEN_LOCK_STRIPES))
        self._closed = False

    @property
    def closed(self) -> bool:
        return self._closed

    async def aclose(self) -> None:
        """Close the connection pool and discard process-local tokens."""
        if not self._closed:
            self._closed = True
            self._tokens.clear()
            await self._client.aclose()

    @staticmethod
    def _base_url(context: IntegrationContext) -> str:
        return _SANDBOX if context.environment == "sandbox" else _PRODUCTION

    @staticmethod
    def _cache_key(context: IntegrationContext) -> str:
        credentials = context.credentials
        digest = hashlib.sha256()
        for value in (
            context.environment,
            credentials.consumer_key.get_secret_value(),
            credentials.consumer_secret.get_secret_value(),
            str(credentials.credential_version),
        ):
            encoded = value.encode("utf-8")
            digest.update(len(encoded).to_bytes(4, "big"))
            digest.update(encoded)
        return digest.hexdigest()

    @staticmethod
    def _secret(value: SecretStr | None, field: str) -> str:
        if value is None or not value.get_secret_value():
            raise MissingCredential(f"required credential '{field}' is missing")
        return value.get_secret_value()

    @staticmethod
    async def _read_limited(response: httpx.Response) -> bytes:
        content_length = response.headers.get("content-length")
        if content_length is not None:
            try:
                if int(content_length) > _MAX_RESPONSE_BYTES:
                    raise _ResponseTooLarge
            except ValueError:
                pass

        content = bytearray()
        async for chunk in response.aiter_bytes(chunk_size=_RESPONSE_CHUNK_BYTES):
            if len(content) + len(chunk) > _MAX_RESPONSE_BYTES:
                raise _ResponseTooLarge
            content.extend(chunk)
        return bytes(content)

    @staticmethod
    def _json_object(content: bytes) -> dict[str, Any]:
        try:
            body = json.loads(content)
        except (ValueError, TypeError):
            raise ValueError from None
        if not isinstance(body, dict):
            raise ValueError
        return body

    def _cached_token(self, key: str, now: float) -> str | None:
        cached = self._tokens.get(key)
        if cached is None:
            return None
        if cached[1] - _TOKEN_SAFETY_MARGIN_SECONDS <= now:
            del self._tokens[key]
            return None
        self._tokens.move_to_end(key)
        return cached[0]

    async def token(self, context: IntegrationContext) -> str:
        """Return a cached token or coalesce a refresh on a bounded lock stripe."""
        if self._closed:
            raise InvalidRequest("mpesa_core client is closed")
        validate_context(context)
        key = self._cache_key(context)
        loop = asyncio.get_running_loop()
        cached = self._cached_token(key, loop.time())
        if cached is not None:
            return cached

        lock = self._token_locks[int(key[:8], 16) % len(self._token_locks)]
        async with lock:
            cached = self._cached_token(key, loop.time())
            if cached is not None:
                return cached

            consumer_key = self._secret(context.credentials.consumer_key, "consumer_key")
            consumer_secret = self._secret(context.credentials.consumer_secret, "consumer_secret")
            url = self._base_url(context) + "/oauth/v1/generate?grant_type=client_credentials"
            basic = base64.b64encode(f"{consumer_key}:{consumer_secret}".encode()).decode("ascii")
            try:
                async with self._client.stream(
                    "GET", url, headers={"Authorization": f"Basic {basic}"}
                ) as response:
                    status_code = response.status_code
                    content = await self._read_limited(response)
            except _ResponseTooLarge:
                raise OAuthError("Daraja authorization response exceeded the supported size") from None
            except httpx.HTTPError as exc:
                logger.warning(
                    "daraja_oauth_transport_error environment={} error_type={}",
                    context.environment,
                    type(exc).__name__,
                )
                raise OAuthError("Daraja authorization request failed") from None

            if status_code < 200 or status_code >= 300:
                logger.warning(
                    "daraja_oauth_rejected environment={} http_status={}",
                    context.environment,
                    status_code,
                )
                raise OAuthError("Daraja authorization was rejected")
            try:
                body = self._json_object(content)
                token = body["access_token"]
                expires_in = int(body["expires_in"])
                if not isinstance(token, str) or not token or expires_in <= 0:
                    raise ValueError
            except (ValueError, TypeError, KeyError):
                raise OAuthError("Daraja authorization response was invalid") from None

            self._tokens[key] = (token, loop.time() + expires_in)
            self._tokens.move_to_end(key)
            while len(self._tokens) > _MAX_CACHED_TOKENS:
                self._tokens.popitem(last=False)
            return token

    async def request(
        self,
        context: IntegrationContext,
        operation: DarajaOperation,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], int]:
        """Send one provider request, bounding the body before JSON decoding."""
        if self._closed:
            raise InvalidRequest("mpesa_core client is closed")
        token = await self.token(context)
        url = self._base_url(context) + path
        try:
            async with self._client.stream(
                method,
                url,
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json=payload,
            ) as response:
                status_code = response.status_code
                content = await self._read_limited(response)
        except _ResponseTooLarge:
            logger.warning(
                "daraja_response_too_large operation={} environment={} integration={}",
                operation.value,
                context.environment,
                context.integration_id,
            )
            raise MalformedProviderResponse("Daraja response exceeded the supported size") from None
        except (httpx.ConnectError, httpx.ConnectTimeout):
            logger.warning(
                "daraja_transport_not_sent operation={} environment={} integration={}",
                operation.value,
                context.environment,
                context.integration_id,
            )
            raise TransportFailure("Daraja connection could not be established") from None
        except (httpx.TimeoutException, httpx.NetworkError):
            logger.warning(
                "daraja_transport_unknown operation={} environment={} integration={}",
                operation.value,
                context.environment,
                context.integration_id,
            )
            raise AmbiguousOutcome("Daraja outcome is unknown; reconcile before retrying") from None
        except httpx.HTTPError as exc:
            logger.warning(
                "daraja_transport_error operation={} error_type={}",
                operation.value,
                type(exc).__name__,
            )
            raise AmbiguousOutcome("Daraja outcome is unknown; reconcile before retrying") from None

        try:
            body = self._json_object(content)
        except ValueError:
            logger.warning(
                "daraja_malformed_response operation={} http_status={}",
                operation.value,
                status_code,
            )
            raise MalformedProviderResponse("Daraja returned an invalid response") from None

        if status_code < 200 or status_code >= 300:
            code = _safe_provider_code(body.get("errorCode") or body.get("ResponseCode"))
            logger.warning(
                "daraja_http_rejection operation={} http_status={} provider_code={}",
                operation.value,
                status_code,
                code,
            )
            if status_code == 429:
                raise ProviderRejected(
                    "Daraja rate-limited the request",
                    provider_code=code,
                    http_status=status_code,
                    retry_disposition=RetryDisposition.SAFE,
                )
            if status_code == 408 or status_code >= 500:
                raise AmbiguousOutcome(
                    "Daraja returned a server error; reconcile before retrying",
                    provider_code=code,
                    http_status=status_code,
                )
            raise ProviderRejected(
                "Daraja rejected the request",
                provider_code=code,
                http_status=status_code,
            )

        code = _safe_provider_code(body.get("ResponseCode"))
        if code is not None and code != "0":
            logger.info("daraja_operation_rejected operation={} provider_code={}", operation.value, code)
            raise ProviderRejected(
                "Daraja rejected the operation",
                provider_code=code,
                http_status=status_code,
            )
        return body, status_code


def _safe_provider_code(value: object) -> str | None:
    """Keep provider codes bounded and free of arbitrary echoed payload text."""
    candidate = str(value) if isinstance(value, (str, int)) else None
    if candidate is None:
        return None
    return candidate if candidate.isascii() and all(
        char.isalnum() or char in "_.-" for char in candidate
    ) and 1 <= len(candidate) <= 64 else "untrusted_provider_code"
