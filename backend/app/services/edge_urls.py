"""Build public edge callback URLs (Safaricom-safe paths)."""
from __future__ import annotations

from app.core.config import settings


def edge_base() -> str:
    return settings.edge_public_base_url.rstrip("/")


def callback_prefix() -> str:
    prefix = settings.edge_callback_path_prefix.strip() or "/cb"
    if not prefix.startswith("/"):
        prefix = "/" + prefix
    return prefix.rstrip("/") or "/cb"


def integration_callback_urls(public_id: str) -> dict[str, str]:
    """STK / confirmation / validation URLs without the substring mpesa in the path."""
    root = f"{edge_base()}{callback_prefix()}/{public_id}"
    return {
        "stk": f"{root}/stk",
        "confirmation": f"{root}/confirmation",
        "validation": f"{root}/validation",
    }
