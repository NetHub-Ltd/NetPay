"""Loguru setup — verbose by default for ops diagnosis. Never blocks request handling."""
from __future__ import annotations

import logging
import os
import sys

from loguru import logger as loguru_logger

VERSION = os.getenv("APP_VERSION", "dev")
ENV = os.getenv("ENVIRONMENT", os.getenv("ENV", "development"))
# Default DEBUG so Daraja/register failures are visible in Render logs
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG").upper()


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = loguru_logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        try:
            loguru_logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())
        except Exception:
            pass


def setup_intercept() -> None:
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(logging.DEBUG)
    for name in ("uvicorn", "uvicorn.access", "uvicorn.error", "fastapi", "httpx", "httpcore"):
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True
        logging.getLogger(name).setLevel(logging.DEBUG)
    for name in list(logging.root.manager.loggerDict):
        logger_obj = logging.getLogger(name)
        logger_obj.handlers = []
        logger_obj.propagate = True


def setup_logger():
    loguru_logger.remove()
    loguru_logger.add(
        sys.stdout,
        level=LOG_LEVEL,
        colorize=False,
        enqueue=True,
        backtrace=True,
        diagnose=True,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {name}:{function}:{line} | {message}",
    )
    log_dir = os.getenv("LOG_DIR", "logs")
    try:
        os.makedirs(log_dir, exist_ok=True)
        loguru_logger.add(
            f"{log_dir}/app_{{time:YYYY-MM-DD}}.log",
            level="DEBUG",
            rotation="20 MB",
            retention="14 days",
            compression="zip",
            serialize=True,
            enqueue=True,
            backtrace=True,
            diagnose=True,
        )
    except OSError as exc:
        loguru_logger.warning("File log sink unavailable: {}", exc)

    setup_intercept()
    return loguru_logger


def setup_logging() -> None:
    setup_logger()
    loguru_logger.info("Logging ready · {} · env={} · level={} (no noise filter)", VERSION, ENV, LOG_LEVEL)


logger = setup_logger()
