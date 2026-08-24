"""NetHub Payment Gateway v1.1 — FastAPI entrypoint."""
from __future__ import annotations
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.api.routes import auth, events, health, integrations, internal, payments, tenants, webhooks
from app.core.config import settings
from app.core.db import engine
from app.core.logging import logger, setup_logging
from app.services.bootstrap import startup_sequence

def _resolve_static_dir() -> Path:
    """SPA build output. Prefer STATIC_DIR env, else backend/static next to app/."""
    import os
    override = os.environ.get("STATIC_DIR")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[1] / "static"

STATIC_DIR = _resolve_static_dir()

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Starting {} v{}", settings.app_name, settings.app_version)
    boot = await startup_sequence()
    logger.info("Startup complete: {}", boot)
    yield
    await engine.dispose()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Multi-tenant M-Pesa orchestration. Clients never talk to Daraja.",
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(tenants.router)
app.include_router(integrations.router)
app.include_router(webhooks.router)
app.include_router(payments.router)
app.include_router(events.router)
app.include_router(internal.router)

if STATIC_DIR.is_dir():
    assets = STATIC_DIR / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/")
    async def spa_index():
        index = STATIC_DIR / "index.html"
        if index.is_file():
            return FileResponse(index)
        return {"message": "NetHub Payment Gateway", "docs": "/docs"}

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str, request: Request):
        # Do not swallow API/docs paths
        blocked = ("api", "v1", "auth", "oauth", "health", "internal", "docs", "redoc", "openapi.json", "assets")
        first = full_path.split("/", 1)[0]
        if first in blocked:
            return {"detail": "Not Found"}
        index = STATIC_DIR / "index.html"
        if index.is_file():
            return FileResponse(index)
        return {"detail": "Not Found"}
