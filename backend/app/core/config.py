"""Settings — one DATABASE_URL drives async app + sync Alembic."""
from __future__ import annotations
from functools import lru_cache
from typing import Literal, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

def to_sync_url(async_url: str) -> str:
    """Convert async DATABASE_URL to a sync SQLAlchemy URL for Alembic.

    Always pin Postgres to the psycopg2 driver (``postgresql+psycopg2://``).
    Plain ``postgresql://`` can resolve to the psycopg3 dialect on newer
    SQLAlchemy builds, which requires the separate ``psycopg`` package.
    """
    u = async_url.strip()
    if u.startswith("sqlite+aiosqlite://"):
        return "sqlite://" + u.removeprefix("sqlite+aiosqlite://")
    if u.startswith("postgresql+asyncpg://"):
        return "postgresql+psycopg2://" + u.removeprefix("postgresql+asyncpg://")
    if u.startswith("postgresql+psycopg://"):
        return "postgresql+psycopg2://" + u.removeprefix("postgresql+psycopg://")
    if u.startswith("postgresql://"):
        return "postgresql+psycopg2://" + u.removeprefix("postgresql://")
    if u.startswith("postgres://"):
        return "postgresql+psycopg2://" + u.removeprefix("postgres://")
    return u

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    app_name: str = "NetHub Payment Gateway"
    environment: Literal["development", "test", "production"] = "development"
    secret_key: str = "dev-secret-change-me"
    app_version: str = "1.1.0"
    admin_email: str = "admin@nethub.test"
    # Comma-separated extra emails treated as platform admin (optional)
    admin_emails: str = Field(default="", alias="ADMIN_EMAILS")
    internal_api_key: str = "change-me-internal-worker-secret"
    database_url: str = Field(default="sqlite+aiosqlite:///./data/gateway.db", alias="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    redis_required: bool = Field(default=False, alias="REDIS_REQUIRED")
    access_token_expire_minutes: int = 720
    # Machine (client_credentials) tokens use a shorter default TTL than human sessions.
    machine_token_expire_minutes: int = Field(default=60, alias="MACHINE_TOKEN_EXPIRE_MINUTES")
    machine_token_audience: str = Field(default="netpay", alias="MACHINE_TOKEN_AUDIENCE")
    # Rate limits (requests per window). 0 disables.
    rate_limit_token_per_minute: int = Field(default=30, alias="RATE_LIMIT_TOKEN_PER_MINUTE")
    rate_limit_payment_per_minute: int = Field(default=60, alias="RATE_LIMIT_PAYMENT_PER_MINUTE")
    rate_limit_window_seconds: int = Field(default=60, alias="RATE_LIMIT_WINDOW_SECONDS")
    # OpenAPI /docs — disabled automatically in production unless explicitly enabled.
    openapi_enabled: Optional[bool] = Field(default=None, alias="OPENAPI_ENABLED")
    cors_origins: str = "*"
    log_level: str = "INFO"
    webhook_timeout_seconds: float = 8.0
    stk_timeout_seconds: float = Field(default=120.0, alias="STK_TIMEOUT_SECONDS")
    inbound_event_max_attempts: int = Field(default=5, alias="INBOUND_EVENT_MAX_ATTEMPTS")
    max_webhooks_per_tenant: int = 3
    # Public M-Pesa edge base (no trailing slash). Used for Daraja callback URLs shown in UI.
    edge_public_base_url: str = Field(
        default="https://gateway.nethub.co.ke",
        alias="EDGE_PUBLIC_BASE_URL",
    )
    # Path under edge host for provider callbacks. Must NOT contain the substring "mpesa"
    # (Safaricom rejects callback URLs that include that word).
    edge_callback_path_prefix: str = Field(
        default="/cb",
        alias="EDGE_CALLBACK_PATH_PREFIX",
    )

    # NetHub API — identity only. NetPay forwards Bearer tokens to NetHub and
    # never decodes JWTs or stores user credentials. See docs/auth-model.md.
    nethub_api_base_url: str = Field(default="", alias="NETHUB_API_BASE_URL")
    nethub_api_timeout_seconds: float = Field(default=8.0, alias="NETHUB_API_TIMEOUT_SECONDS")

    # SPA OIDC (public client / PKCE). Served at GET /config.json so the same
    # image works on GHCR, Render, and k3s without rebuilding the frontend.
    # Optional VITE_* bake at image build remains a local-dev fallback only.
    oidc_issuer: str = Field(default="", alias="OIDC_ISSUER")
    oidc_client_id: str = Field(default="", alias="OIDC_CLIENT_ID")
    oidc_redirect_uri: str = Field(default="", alias="OIDC_REDIRECT_URI")
    oidc_scopes: str = Field(
        default="openid profile email offline_access",
        alias="OIDC_SCOPES",
    )

    @field_validator("openapi_enabled", mode="before")
    @classmethod
    def _coerce_optional_bool(cls, v):  # noqa: ANN001
        if v is None or v == "":
            return None
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            low = v.strip().lower()
            if low in ("1", "true", "yes", "on"):
                return True
            if low in ("0", "false", "no", "off"):
                return False
        return v

    @property
    def async_database_url(self) -> str:
        return self.database_url

    @property
    def sync_database_url(self) -> str:
        return to_sync_url(self.database_url)

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def openapi_enabled_effective(self) -> bool:
        """OpenAPI UI enabled unless production (or explicit false)."""
        if self.openapi_enabled is not None:
            return bool(self.openapi_enabled)
        return self.environment != "production"

    def assert_production_secrets(self) -> None:
        """Fail closed when unsafe defaults are used in production."""
        if self.environment != "production":
            return
        if self.secret_key in ("", "dev-secret-change-me", "change-me"):
            raise RuntimeError(
                "SECRET_KEY must be set to a strong value in production "
                "(refusing default dev secret)"
            )
        if self.internal_api_key in ("", "change-me-internal-worker-secret", "change-me"):
            raise RuntimeError(
                "INTERNAL_API_KEY must be set to a strong value in production"
            )

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
