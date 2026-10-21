"""Redis client lifecycle and connectivity check.

Redis is auxiliary infrastructure. Callers may use it for cache/coordination,
but durable payment and reconciliation state must remain in PostgreSQL.
"""

from redis.asyncio import Redis

from app.config import get_settings


_client: Redis | None = None


def get_redis_client() -> Redis:
    global _client
    if _client is None:
        settings = get_settings()
        _client = Redis.from_url(
            settings.redis_url.get_secret_value(),
            decode_responses=True,
            socket_connect_timeout=settings.redis_connect_timeout_seconds,
            socket_timeout=settings.redis_socket_timeout_seconds,
            health_check_interval=30,
        )
    return _client


async def check_redis() -> None:
    """Raise when Redis cannot answer PING; lifespan decides whether that is fatal."""
    await get_redis_client().ping()


async def dispose_redis() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
