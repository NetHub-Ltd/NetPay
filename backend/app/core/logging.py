"""
Nethub Logging System
Version: v1.3.1
Changes:
- Level pill only applies to the level badge (not the message)
- Softer green matching FastAPI style
- DEBUG still restricted to app.* only
"""
from __future__ import annotations

import logging
import os
import sys

from loguru import logger as loguru_logger

# ----------------------------
# CONFIG
# ----------------------------
VERSION = "v1.3.1"

_raw_env = (os.getenv("ENV") or os.getenv("ENVIRONMENT") or "development").lower()
ENV = "dev" if _raw_env in ("dev", "development") else _raw_env
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG" if ENV == "dev" else "INFO").upper()

# ----------------------------
# LEVEL STYLING (true pill - badge only)
# ----------------------------
LEVEL_STYLES = {
    "DEBUG": "<white><bg #546E7A>",  # Blue-grey
    "INFO": "<white><bg #2E7D32>",  # Softer FastAPI-like green
    "WARNING": "<white><bg #F9A825>",  # Amber
    "ERROR": "<white><bg #C62828>",  # Red
    "CRITICAL": "<white><bg #6A1B9A>",  # Purple
}
for level_name, style in LEVEL_STYLES.items():
    loguru_logger.level(level_name, color=style)

# ----------------------------
# NOISE CONTROL
# ----------------------------
NOISY_LOGGERS = {
    "watchfiles",
    "uvicorn.access",
    "uvicorn.reload",
    "uvicorn.error",
    "asyncio",
    "passlib",
    "passlib.utils",
    "passlib.registry",
    "passlib.handlers",
    "sqlalchemy",
    "sqlalchemy.engine",
    "sqlalchemy.pool",
    "sqlalchemy.orm",
    "alembic",
    "httpcore",
    "httpx",
    "multipart",
    "python_multipart",
    "concurrent",
    "filelock",
}

ALLOWED_DEBUG_PREFIXES = (
    "app.",
    "__main__",
)


def noise_filter(record: dict) -> bool:
    name = record["name"]
    level = record["level"].name

    # DEBUG → only from our application code
    if level == "DEBUG":
        return any(name.startswith(prefix) for prefix in ALLOWED_DEBUG_PREFIXES)

    # INFO+ → suppress noisy libraries
    if any(name.startswith(noisy) for noisy in NOISY_LOGGERS):
        return False
    return True


# ----------------------------
# INTERCEPT STANDARD LOGGING
# ----------------------------
class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = loguru_logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        loguru_logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())


def setup_intercept() -> None:
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(logging.DEBUG)
    for name in logging.root.manager.loggerDict:
        logger_obj = logging.getLogger(name)
        logger_obj.handlers = []
        logger_obj.propagate = True


# ----------------------------
# LOGGER SETUP
# ----------------------------
def setup_logger():
    loguru_logger.remove()

    loguru_logger.add(
        sys.stdout,
        level=LOG_LEVEL,
        colorize=True,
        filter=noise_filter,
        enqueue=True,
        format=(
            "<level> {level: <8} </level> "
            "<green>{time:HH:mm:ss}</green> "
            "<cyan>{name}</cyan>:<cyan>{line}</cyan> "
            "{message}"
        ),
    )

    log_dir = os.getenv("LOG_DIR", "logs")
    os.makedirs(log_dir, exist_ok=True)
    loguru_logger.add(
        f"{log_dir}/app_{{time:YYYY-MM-DD}}.log",
        level="INFO",
        rotation="10 MB",
        retention="14 days",
        compression="zip",
        serialize=True,
        enqueue=True,
        backtrace=True,
        diagnose=ENV == "dev",
        filter=noise_filter,
    )

    setup_intercept()
    return loguru_logger


def setup_logging() -> None:
    """Idempotent entry used by FastAPI lifespan."""
    setup_logger()
    loguru_logger.info("Logging ready · {} · env={} · level={}", VERSION, ENV, LOG_LEVEL)


# Module-level logger (configured on import for scripts; lifespan re-applies setup)
logger = setup_logger()
