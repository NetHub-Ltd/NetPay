"""Public SPA configuration — no secrets."""
from __future__ import annotations

from app.core.config import get_settings


def public_spa_config() -> dict:
    """Runtime SPA config (no secrets). Used by the static dashboard for OIDC + API origin."""
    settings = get_settings()
    issuer = (settings.oidc_issuer or "").strip().rstrip("/")
    client_id = (settings.oidc_client_id or "").strip()
    redirect = (settings.oidc_redirect_uri or "").strip()
    scopes = (settings.oidc_scopes or "").strip() or "openid profile email offline_access"
    nethub = (settings.nethub_api_base_url or "").strip().rstrip("/")
    configured = bool(issuer and client_id and redirect)
    return {
        "oidc_issuer": issuer,
        "oidc_client_id": client_id,
        "oidc_redirect_uri": redirect,
        "oidc_scopes": scopes,
        "oidc_configured": configured,
        "nethub_api_configured": bool(nethub),
        "auth_mode": "spa_pkce",
    }
