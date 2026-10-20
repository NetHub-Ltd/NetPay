"""NetPay FastAPI entrypoint and operational health endpoints."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from loguru import logger

from app.config import get_settings
from app.db import check_database, dispose_engine
from app.routers.auth import router as auth_router
from app.routers.callbacks import router as callbacks_router
from app.routers.integrations import router as integrations_router
from app.routers.payments import router as payments_router

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Starting {} in {} mode", settings.app_name, settings.environment)
    try:
        yield
    finally:
        await dispose_engine()
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


@app.get("/", tags=["meta"])
async def root() -> dict[str, str]:
    return {"name": settings.app_name, "status": "running", "docs": "/docs"}
