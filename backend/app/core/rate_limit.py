"""Rate limiter for M2M surfaces (token + payment-intent create).

- Prefer Redis (shared across replicas).
- When REDIS_REQUIRED is true (or environment=production): do **not** silently
  fall back to in-process memory — return 503 so under-limiting cannot hide.
- When Redis is optional (local/dev): memory fallback is allowed.
"""
from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock
from typing import Optional

from fastapi import HTTPException, Request, status

from app.core.config import settings
from app.core.logging import logger

_buckets: dict[str, list[float]] = defaultdict(list)
_lock = Lock()


def _redis_required() -> bool:
    return bool(settings.redis_required) or settings.environment == "production"


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip() or "unknown"
    if request.client:
        return request.client.host or "unknown"
    return "unknown"


def _memory_hit(key: str, limit: int, window: int) -> tuple[bool, int]:
    now = time.time()
    with _lock:
        cutoff = now - window
        stamps = [t for t in _buckets[key] if t > cutoff]
        if len(stamps) >= limit:
            retry = max(1, int(window - (now - stamps[0]))) if stamps else window
            _buckets[key] = stamps
            return False, retry
        stamps.append(now)
        _buckets[key] = stamps
        return True, 0


async def _redis_hit(key: str, limit: int, window: int) -> Optional[tuple[bool, int]]:
    """Return (allowed, retry_after) or None if Redis unavailable."""
    from app.core.redis import get_redis

    r = await get_redis()
    if r is None:
        return None
    try:
        now = time.time()
        pipe = r.pipeline()
        pipe.zremrangebyscore(key, 0, now - window)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        pipe.expire(key, window + 1)
        results = await pipe.execute()
        count = int(results[2])
        if count > limit:
            oldest = await r.zrange(key, 0, 0, withscores=True)
            retry = window
            if oldest:
                retry = max(1, int(window - (now - float(oldest[0][1]))))
            return False, retry
        return True, 0
    except Exception as exc:  # noqa: BLE001
        logger.warning("rate_limit redis error: {}", exc)
        return None


async def enforce_rate_limit(
    request: Request,
    *,
    bucket: str,
    limit: int,
    identity: Optional[str] = None,
) -> None:
    """Raise 429 if over limit. limit<=0 disables."""
    if limit <= 0:
        return
    window = max(1, int(settings.rate_limit_window_seconds))
    ip = _client_ip(request)
    key = f"rl:{bucket}:{identity or ip}"

    result = await _redis_hit(key, limit, window)
    if result is None:
        if _redis_required():
            logger.error(
                "rate_limit unavailable (Redis required) bucket={} key_suffix={}",
                bucket,
                identity or ip,
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="rate_limit_unavailable",
                headers={"Retry-After": "5"},
            )
        result = _memory_hit(key, limit, window)

    allowed, retry = result
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="rate_limit_exceeded",
            headers={"Retry-After": str(retry)},
        )
