"""NetPay API and database/cache lifecycle."""
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine
from app.core.cache import check_redis, create_redis_client
from app.core.config import Settings, get_settings
from app.core.database import check_database, create_database_engine, create_session_factory
from app import models  # noqa: F401 - register SQLModel metadata
from app.api.oauth import router as oauth_router
from app.api.provisioning import router as provisioning_router

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
app.include_router(oauth_router)
app.include_router(provisioning_router)

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

# Serve the prebuilt Next.js export only after API, docs, and health routes are registered.
# In backend-only development the export may not exist; the API remains runnable.
frontend_static_dir = Path(__file__).resolve().parent / "static"
if frontend_static_dir.is_dir():
    # Next.js exports this generated PNG without a file extension. Expose a stable,
    # correctly typed URL for social crawlers that expect a conventional image path.
    generated_og_image = frontend_static_dir / "opengraph-image"
    if generated_og_image.is_file():
        @app.get("/opengraph-image", include_in_schema=False)
        async def open_graph_image() -> FileResponse:
            return FileResponse(generated_og_image, media_type="image/png")

    app.mount("/", StaticFiles(directory=frontend_static_dir, html=True), name="frontend")
else:
    logger.info("frontend_static=not_built path={}", str(frontend_static_dir))
