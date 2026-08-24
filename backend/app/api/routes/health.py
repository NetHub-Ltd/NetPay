from __future__ import annotations
from fastapi import APIRouter
from sqlalchemy import text
from sqlmodel import select
from app.core.config import settings
from app.core.db import AsyncSessionLocal
from app.core.redis import redis_healthy
from app.models.user import User
from app.schemas.health import HealthOut

router = APIRouter(tags=["health"])

@router.get("/health", response_model=HealthOut)
async def health() -> HealthOut:
    db_ok = False
    admin_ready = False
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            db_ok = True
            r = await session.exec(select(User).where(User.role == "admin").limit(1))
            admin_ready = r.first() is not None
    except Exception:  # noqa: BLE001
        db_ok = False
    redis_ok = await redis_healthy()
    redis_status = "ok" if redis_ok else ("required_missing" if settings.redis_required else "optional_unavailable")
    status = "ok" if db_ok and admin_ready and (redis_ok or not settings.redis_required) else "degraded"
    return HealthOut(status=status, database=db_ok, redis=redis_status, admin_ready=admin_ready,
                     environment=settings.environment, version=settings.app_version)
