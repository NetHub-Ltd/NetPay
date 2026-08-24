"""
Nethub Logging System
Version: v1.3.2
Changes:
- Aligned columns: time | level | location | message
- Short module names (drop leading app.)
- Level pill on badge only; plain message text
- DEBUG restricted to app.* / __main__
"""
from __future__ import annotations

import logging
import os
import sys

from loguru import logger as loguru_logger

# ----------------------------
# CONFIG
# ----------------------------
VERSION = "v1.3.2"

_raw_env = (os.getenv("ENV") or os.getenv("ENVIRONMENT") or "development").lower()
ENV = "dev" if _raw_env in ("dev", "development") else _raw_env
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG" if ENV == "dev" else "INFO").upper()

# ----------------------------
# LEVEL STYLING (badge only)
# ----------------------------
LEVEL_STYLES = {
    "DEBUG": "<white><bg #546E7A>",
    "INFO": "<white><bg #2E7D32>",
    "WARNING": "<white><bg #F9A825>",
    "ERROR": "<white><bg #C62828>",
    "CRITICAL": "<white><bg #6A1B9A>",
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


def _short_name(name: str) -> str:
    """app.api.routes.auth → routes.auth; app.services.bootstrap → services.bootstrap"""
    if name.startswith("app."):
        parts = name.split(".")
        # drop "app"; keep last two segments when deep
        rest = parts[1:]
        if len(rest) >= 2:
            return ".".join(rest[-2:])
        return rest[0] if rest else name
    if name == "__main__":
        return "main"
    return name


def noise_filter(record: dict) -> bool:
    name = record["name"]
    level = record["level"].name

    if level == "DEBUG":
        return any(name.startswith(prefix) for prefix in ALLOWED_DEBUG_PREFIXES)

    if any(name.startswith(noisy) for noisy in NOISY_LOGGERS):
        return False
    return True


def _patch_record(record: dict) -> None:
    record["extra"]["where"] = f"{_short_name(record['name'])}:{record['line']}"


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
    for name in list(logging.root.manager.loggerDict):
        logger_obj = logging.getLogger(name)
        logger_obj.handlers = []
        logger_obj.propagate = True


# ----------------------------
# CONSOLE FORMAT
# time │ LEVEL    │ where          │ message
# ----------------------------
CONSOLE_FORMAT = (
    "<green>{time:HH:mm:ss}</green>"
    " <dim>│</dim> "
    "<level> {level: <7} </level>"
    " <dim>│</dim> "
    "<cyan>{extra[where]: <22}</cyan>"
    " <dim>│</dim> "
    "{message}"
)


def setup_logger():
    loguru_logger.remove()
    loguru_logger.configure(patcher=_patch_record)

    loguru_logger.add(
        sys.stdout,
        level=LOG_LEVEL,
        colorize=True,
        filter=noise_filter,
        enqueue=True,
        format=CONSOLE_FORMAT,
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
    loguru_logger.info(
        "Logging ready · {} · env={} · level={}",
        VERSION,
        ENV,
        LOG_LEVEL,
    )


logger = setup_logger()
