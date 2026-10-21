"""NetPay API and database/cache lifecycle."""
from contextlib import asynccontextmanager
from typing import AsyncIterator
from fastapi import FastAPI, HTTPException, Request
from loguru import logger
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine
from app.core.cache import check_redis, create_redis_client
from app.core.config import Settings, get_settings
from app.core.database import check_database, create_database_engine, create_session_factory
from app import models  # noqa: F401 - register SQLModel metadata

@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Initialize required PostgreSQL and optional Redis; dispose clients on shutdown."""
    settings: Settings = get_settings()
    engine: AsyncEngine = create_database_engine(settings)
    redis_client: Redis | None = None
    application.state.engine = engine
    application.state.session_factory = create_session_factory(engine)
    application.state.redis = None
    try:
        await check_database(engine)
        logger.info("database_connectivity=ok")
        if settings.redis_enabled:
            candidate = create_redis_client(settings)
            try:
                await check_redis(candidate)
                redis_client = candidate
                application.state.redis = candidate
                logger.info("redis_connectivity=ok")
            except Exception as exc:
                logger.warning("redis_connectivity=unavailable error_type={}", type(exc).__name__)
                await candidate.aclose()
        yield
    finally:
        if redis_client is not None:
            await redis_client.aclose()
        await engine.dispose()
        application.state.engine = None
        application.state.session_factory = None
        application.state.redis = None

app = FastAPI(title="NetPay API", version="0.2.0", description="NetPay payment gateway API.", docs_url="/docs", redoc_url=None, lifespan=lifespan)

@app.get("/health/live", tags=["health"], summary="Liveness probe")
async def liveness() -> dict[str, str]:
    """Report process liveness without external dependency calls."""
    return {"status": "ok"}

@app.get("/health/ready", tags=["health"], summary="Dependency readiness")
async def readiness(request: Request) -> dict[str, str]:
    """Require PostgreSQL and report Redis separately as an auxiliary dependency."""
    engine: AsyncEngine | None = getattr(request.app.state, "engine", None)
    if engine is None:
        raise HTTPException(status_code=503, detail="database_not_initialized")
    try:
        await check_database(engine)
    except Exception as exc:
        logger.error("database_readiness=failed error_type={}", type(exc).__name__)
        raise HTTPException(status_code=503, detail="database_unavailable") from exc
    redis_client: Redis | None = getattr(request.app.state, "redis", None)
    redis_status = "disabled" if not get_settings().redis_enabled else "unavailable"
    if redis_client is not None:
        try:
            await check_redis(redis_client)
            redis_status = "ok"
        except Exception as exc:
            logger.warning("redis_readiness=failed error_type={}", type(exc).__name__)
    return {"status": "ok", "database": "ok", "redis": redis_status}
