from __future__ import annotations
import sys
from loguru import logger
from app.core.config import settings

def setup_logging() -> None:
    logger.remove()
    logger.add(sys.stderr, level=settings.log_level, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}")
