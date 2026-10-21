"""Bridge standard-library and Uvicorn logging into Loguru."""

import logging
import sys

from loguru import logger


class InterceptHandler(logging.Handler):
    """Forward stdlib log records without duplicating them."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        logger.opt(exception=record.exc_info, depth=6).log(level, record.getMessage())


def configure_logging(level: str) -> None:
    """Configure one Loguru sink and route framework logs through it."""
    normalized = level.upper()
    if normalized == "WARN":
        normalized = "WARNING"

    logger.remove()
    logger.add(
        sys.stderr,
        level=normalized,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {name}:{function}:{line} - {message}",
        backtrace=False,
        diagnose=False,
    )

    intercept = InterceptHandler()
    logging.basicConfig(handlers=[intercept], level=0, force=True)
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        framework_logger = logging.getLogger(name)
        framework_logger.handlers = [intercept]
        framework_logger.propagate = False
