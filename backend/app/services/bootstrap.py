"""Startup: Alembic migrate, health probes, admin bootstrap."""
from __future__ import annotations
import sys
from pathlib import Path
from app.core.logging import logger
from sqlalchemy import create_engine, text
from sqlmodel import Session, select
from app.core.config import settings
from app.core.security import hash_password
from app.models.user import User

def run_alembic_upgrade() -> None:
    from alembic import command
    from alembic.config import Config
    root = Path(__file__).resolve().parents[2]
    cfg = Config(str(root / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", settings.sync_database_url)
    cfg.set_main_option("script_location", str(root / "alembic"))
    if settings.sync_database_url.startswith("sqlite:///"):
        path = settings.sync_database_url.removeprefix("sqlite:///")
        if path.startswith("./"):
            path = str(root / path[2:])
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    logger.info("Alembic upgrade head → {}", settings.sync_database_url.split("@")[-1])
    command.upgrade(cfg, "head")

def probe_database_sync() -> bool:
    try:
        engine = create_engine(settings.sync_database_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error("Database health check failed: {}", exc)
        return False

def ensure_admin() -> None:
    engine = create_engine(settings.sync_database_url)
    with Session(engine) as session:
        existing = session.exec(select(User).where(User.email == settings.admin_email.lower())).first()
        if existing:
            if existing.role != "admin":
                existing.role = "admin"
                session.add(existing)
                session.commit()
            logger.info("Admin present: {}", settings.admin_email)
            return
        session.add(User(
            email=settings.admin_email.lower(),
            hashed_password=hash_password(settings.admin_password),
            display_name="Admin",
            role="admin",
            is_active=True,
        ))
        session.commit()
        logger.info("Admin created: {}", settings.admin_email)
    engine.dispose()

async def startup_sequence() -> dict:
    run_alembic_upgrade()
    if not probe_database_sync():
        logger.error("FATAL: database unreachable")
        if settings.environment == "production":
            sys.exit(1)
        raise RuntimeError("Database unreachable")
    from app.core.redis import redis_healthy
    redis_ok = await redis_healthy()
    if settings.redis_required or settings.environment == "production":
        if not redis_ok:
            logger.error("FATAL: Redis unreachable")
            sys.exit(1)
    elif not redis_ok:
        logger.warning("Redis unavailable — continuing (REDIS_REQUIRED=false)")
    ensure_admin()
    return {"database": True, "redis": "ok" if redis_ok else "unavailable", "admin_ready": True}
