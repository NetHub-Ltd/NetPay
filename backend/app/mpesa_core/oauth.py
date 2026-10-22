"""Daraja OAuth with expiry-aware caching and durable audit evidence."""
import asyncio
import time
from uuid import uuid4

import httpx
from loguru import logger
from redis.asyncio import Redis

from app.core.config import Settings
from app.models.integrations import DarajaIntegration
from app.mpesa_core.audit import ProviderOperationAuditor
from app.mpesa_core.credentials import IntegrationCredentials
from app.mpesa_core.errors import ProviderAuthenticationError, ProviderProtocolError


class OAuthTokenProvider:
    """Acquire one cached token per integration and credential version."""

    def __init__(
        self,
        settings: Settings,
        http_client: httpx.AsyncClient,
        auditor: ProviderOperationAuditor,
        redis_client: Redis | None = None,
    ) -> None:
        self._settings = settings
        self._http = http_client
        self._auditor = auditor
        self._redis = redis_client
        self._local_cache: dict[str, tuple[str, float]] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    @staticmethod
    def _base_url(integration: DarajaIntegration) -> str:
        return (
            "https://api.safaricom.co.ke"
            if integration.environment == "production"
            else "https://sandbox.safaricom.co.ke"
        )

    def _cache_key(self, integration: DarajaIntegration) -> str:
        return f"netpay:mpesa:oauth:{integration.environment}:{integration.id}:v{integration.credential_version}"

    async def _read_cache(self, key: str) -> str | None:
        local = self._local_cache.get(key)
        if local and local[1] > time.monotonic():
            return local[0]
        self._local_cache.pop(key, None)
        if self._redis is not None:
            try:
                token = await self._redis.get(key)
                if isinstance(token, bytes):
                    token = token.decode("utf-8")
                if isinstance(token, str) and token:
                    self._local_cache[key] = (token, time.monotonic() + 20)
                    return token
            except Exception as exc:
                logger.warning("mpesa_token_cache_read_failed error_type={}", type(exc).__name__)
        return None

    async def _write_cache(self, key: str, token: str, ttl: int) -> None:
        self._local_cache[key] = (token, time.monotonic() + ttl)
        if self._redis is not None:
            try:
                await self._redis.set(key, token, ex=ttl)
            except Exception as exc:
                logger.warning("mpesa_token_cache_write_failed error_type={}", type(exc).__name__)

    async def invalidate(self, integration: DarajaIntegration) -> None:
        """Discard a token after an authorization rejection; never retry the payment."""
        key = self._cache_key(integration)
        self._local_cache.pop(key, None)
        if self._redis is not None:
            try:
                await self._redis.delete(key)
            except Exception as exc:
                logger.warning("mpesa_token_cache_invalidate_failed error_type={}", type(exc).__name__)

    async def _acquire_shared_lock(self, key: str) -> tuple[str | None, bool]:
        """Acquire a short Redis lock, waiting for another replica's refreshed token."""
        if self._redis is None:
            return None, True
        lock_key = key + ":refresh-lock"
        try:
            lock_token = uuid4().hex
            if await self._redis.set(lock_key, lock_token, nx=True, ex=15):
                return lock_token, True
            for _ in range(60):
                await asyncio.sleep(0.1)
                cached = await self._read_cache(key)
                if cached:
                    return None, False
                lock_token = uuid4().hex
                if await self._redis.set(lock_key, lock_token, nx=True, ex=15):
                    return lock_token, True
            raise ProviderAuthenticationError("timed out waiting for shared OAuth token refresh")
        except ProviderAuthenticationError:
            raise
        except Exception as exc:
            logger.warning("mpesa_token_lock_unavailable error_type={}", type(exc).__name__)
            return None, True

    async def _release_shared_lock(self, key: str, token: str | None) -> None:
        if self._redis is None or token is None:
            return
        try:
            await self._redis.eval(
                "if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) else return 0 end",
                1,
                key + ":refresh-lock",
                token,
            )
        except Exception as exc:
            logger.warning("mpesa_token_lock_release_failed error_type={}", type(exc).__name__)

    async def get_token(
        self,
        integration: DarajaIntegration,
        credentials: IntegrationCredentials,
    ) -> str:
        """Return a cached token or audit and perform a fresh OAuth exchange."""
        key = self._cache_key(integration)
        cached = await self._read_cache(key)
        if cached:
            logger.debug("mpesa_oauth_cache_hit integration_id={}", integration.integration_id)
            return cached

        local_lock = self._locks.setdefault(key, asyncio.Lock())
        async with local_lock:
            cached = await self._read_cache(key)
            if cached:
                logger.debug("mpesa_oauth_cache_hit_after_lock integration_id={}", integration.integration_id)
                return cached

            lock_token, should_refresh = await self._acquire_shared_lock(key)
            if not should_refresh:
                cached = await self._read_cache(key)
                if cached:
                    return cached
                raise ProviderAuthenticationError("shared OAuth token refresh completed without a cache entry")

            try:
                audit = await self._auditor.start(
                    integration,
                    "oauth_token",
                    {"environment": integration.environment, "grant_type": "client_credentials"},
                )
                try:
                    response = await self._http.get(
                        self._base_url(integration) + "/oauth/v1/generate",
                        params={"grant_type": "client_credentials"},
                        auth=httpx.BasicAuth(credentials.consumer_key, credentials.consumer_secret),
                        timeout=self._settings.mpesa_http_timeout_seconds,
                    )
                except httpx.ConnectError as exc:
                    await self._auditor.finish(
                        audit.id, outcome="not_sent", response_metadata={"error_code": "connect_error"}
                    )
                    raise ProviderAuthenticationError("Daraja OAuth connection could not be established") from exc
                except httpx.TimeoutException as exc:
                    await self._auditor.finish(
                        audit.id, outcome="unknown", response_metadata={"error_code": "timeout"}
                    )
                    raise ProviderAuthenticationError("Daraja OAuth timed out") from exc
                except httpx.HTTPError as exc:
                    await self._auditor.finish(
                        audit.id, outcome="unknown", response_metadata={"error_code": "transport_error"}
                    )
                    raise ProviderAuthenticationError("Daraja OAuth transport failed") from exc

                if response.status_code >= 400:
                    await self._auditor.finish(
                        audit.id,
                        outcome="rejected",
                        http_status=response.status_code,
                        response_metadata={"error_code": "oauth_http_error"},
                    )
                    raise ProviderAuthenticationError("Daraja rejected OAuth credentials")
                try:
                    data = response.json()
                except ValueError as exc:
                    await self._auditor.finish(
                        audit.id,
                        outcome="unknown",
                        http_status=response.status_code,
                        response_metadata={"error_code": "invalid_json"},
                    )
                    raise ProviderProtocolError("Daraja OAuth returned invalid JSON") from exc
                token = data.get("access_token") if isinstance(data, dict) else None
                if not isinstance(token, str) or not token:
                    await self._auditor.finish(
                        audit.id,
                        outcome="rejected",
                        http_status=response.status_code,
                        response_metadata={"error_code": "missing_access_token"},
                    )
                    raise ProviderAuthenticationError("Daraja OAuth response did not contain an access token")
                try:
                    expires_in = int(data.get("expires_in", 3600))
                except (TypeError, ValueError):
                    expires_in = 3600
                ttl = max(1, expires_in - min(60, max(1, expires_in // 10)))
                await self._auditor.finish(
                    audit.id,
                    outcome="accepted",
                    http_status=response.status_code,
                    response_metadata={"expires_in": expires_in},
                )
                # Write the shared cache before releasing the distributed refresh lock.
                await self._write_cache(key, token, ttl)
                logger.info("mpesa_oauth_cache_miss_refresh_success integration_id={}", integration.integration_id)
                return token
            finally:
                await self._release_shared_lock(key, lock_token)
