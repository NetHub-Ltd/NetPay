"""Application logging — loguru + stdlib intercept.

Must never swallow ERROR/CRITICAL. Request handling must not depend on log sinks.
"""
from __future__ import annotations

import logging
import os
import sys

from loguru import logger as loguru_logger

VERSION = os.getenv("APP_VERSION", "dev")
ENV = os.getenv("ENVIRONMENT", os.getenv("ENV", "development"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Libraries that spam at INFO; we still keep their WARNING+
NOISY_INFO_PREFIXES = (
    "uvicorn.access",
    "uvicorn.error",  # only quiet at INFO; errors pass (level check below)
    "uvicorn",
    "fastapi",
    "asyncio",
    "httpcore",
    "httpx",
    "multipart",
    "python_multipart",
    "concurrent",
    "filelock",
    "alembic",
)

ALLOWED_DEBUG_PREFIXES = (
    "app.",
    "__main__",
)


def noise_filter(record: dict) -> bool:
    """Filter log records without blocking errors or app logs."""
    name = str(record.get("name") or "")
    level = record["level"].name

    # Never drop failures
    if level in ("WARNING", "ERROR", "CRITICAL"):
        return True

    # DEBUG only from our code
    if level == "DEBUG":
        return any(name.startswith(prefix) for prefix in ALLOWED_DEBUG_PREFIXES)

    # INFO: suppress noisy libraries, keep app + everything else
    if level == "INFO":
        for noisy in NOISY_INFO_PREFIXES:
            if name == noisy or name.startswith(noisy + "."):
                return False
        return True

    return True


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = loguru_logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        # Non-blocking: enqueue sinks; never raise into request path
        try:
            loguru_logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())
        except Exception:
            pass


def setup_intercept() -> None:
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(logging.INFO)
    for name in list(logging.root.manager.loggerDict):
        logger_obj = logging.getLogger(name)
        logger_obj.handlers = []
        logger_obj.propagate = True


def setup_logger():
    loguru_logger.remove()

    # Console — synchronous-safe enqueue so logging never blocks the event loop long-term
    loguru_logger.add(
        sys.stdout,
        level=LOG_LEVEL,
        colorize=True,
        filter=noise_filter,
        enqueue=True,
        format=(
            "<level>{level: <8}</level> "
            "<green>{time:HH:mm:ss}</green> "
            "<cyan>{name}</cyan>:<cyan>{line}</cyan> "
            "{message}"
        ),
    )

    log_dir = os.getenv("LOG_DIR", "logs")
    try:
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
            diagnose=ENV in ("dev", "development", "test"),
            filter=noise_filter,
        )
    except OSError:
        # Disk issues must not prevent the app from starting or handling requests
        loguru_logger.add(sys.stderr, level="ERROR", format="{message}")

    setup_intercept()
    return loguru_logger


def setup_logging() -> None:
    setup_logger()
    loguru_logger.info("Logging ready · {} · env={} · level={}", VERSION, ENV, LOG_LEVEL)


logger = setup_logger()
