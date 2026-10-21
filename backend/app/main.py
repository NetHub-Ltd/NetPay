"""NetPay FastAPI entrypoint and operational health endpoints."""

from contextlib import asynccontextmanager
import os
from pathlib import Path
from collections.abc import AsyncIterator

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.config import get_settings
from app.db import check_database, dispose_engine
from app.logging_config import configure_logging
from app.redis_client import check_redis, dispose_redis
from app.routers.auth import router as auth_router
from app.routers.callbacks import router as callbacks_router
from app.routers.events import router as events_router
from app.routers.integrations import router as integrations_router
from app.routers.payments import router as payments_router

settings = get_settings()
configure_logging(settings.log_level)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting {} in {} mode", settings.app_name, settings.environment)
    try:
        # PostgreSQL is the financial source of truth: do not accept traffic if
        # its configured connection cannot execute a trivial query.
        await check_database()
        logger.info("Database connectivity verified")

        # Redis is auxiliary, so report degradation without blocking API startup.
        try:
            await check_redis()
            logger.info("Redis connectivity verified")
        except Exception as exc:
            logger.warning(
                "Redis unavailable; continuing without Redis-dependent features ({})",
                type(exc).__name__,
            )

        yield
    except Exception as exc:
        logger.error("Application startup or lifespan failed ({})", type(exc).__name__)
        raise
    finally:
        try:
            await dispose_redis()
        finally:
            try:
                await dispose_engine()
            finally:
                logger.info("Stopped {}", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Multi-merchant M-Pesa Daraja gateway API",
    lifespan=lifespan,
)


app.include_router(auth_router)
app.include_router(integrations_router)
app.include_router(payments_router)
app.include_router(callbacks_router)
app.include_router(events_router)

allowed_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
if allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
    )


@app.get("/health/live", tags=["health"], include_in_schema=False)
async def liveness() -> dict[str, str]:
    """Process liveness only; do not depend on external services."""
    return {"status": "ok"}


@app.get("/health/ready", tags=["health"], include_in_schema=False)
async def readiness() -> dict[str, str]:
    """Readiness requires PostgreSQL/DB, not optional Redis."""
    try:
        await check_database()
    except Exception as exc:
        logger.warning("Readiness database check failed: {}", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not_ready", "dependency": "database"},
        ) from exc
    return {"status": "ready"}


@app.get("/health", tags=["health"], include_in_schema=False)
async def health_compatibility() -> dict[str, str]:
    """Compatibility endpoint for existing deployment probes."""
    return await readiness()


@app.get("/api", tags=["meta"])
async def api_root() -> dict[str, str]:
    return {"name": settings.app_name, "status": "running", "docs": "/docs"}


static_dir = Path(os.environ.get("STATIC_DIR", ""))
if static_dir.is_dir() and (static_dir / "index.html").is_file():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="frontend")
