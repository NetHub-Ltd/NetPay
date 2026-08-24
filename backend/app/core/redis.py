from __future__ import annotations
from typing import Optional
import redis.asyncio as redis
from app.core.logging import logger
from app.core.config import settings

_client: Optional[redis.Redis] = None

async def get_redis() -> Optional[redis.Redis]:
    global _client
    if _client is not None:
        return _client
    try:
        _client = redis.from_url(settings.redis_url, decode_responses=True)
        await _client.ping()
        return _client
    except Exception as exc:  # noqa: BLE001
        logger.warning("Redis unavailable: {}", exc)
        _client = None
        return None

async def redis_healthy() -> bool:
    c = await get_redis()
    if not c:
        return False
    try:
        await c.ping()
        return True
    except Exception:  # noqa: BLE001
        return False

async def cache_get(key: str) -> Optional[str]:
    c = await get_redis()
    if not c:
        return None
    try:
        return await c.get(key)
    except Exception:  # noqa: BLE001
        return None

async def cache_set(key: str, value: str, ttl: int = 3500) -> None:
    c = await get_redis()
    if not c:
        return
    try:
        await c.set(key, value, ex=ttl)
    except Exception:  # noqa: BLE001
        pass
