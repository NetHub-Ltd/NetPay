"""Settings — one DATABASE_URL drives async app + sync Alembic."""
from __future__ import annotations
from functools import lru_cache
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

def to_sync_url(async_url: str) -> str:
    u = async_url.strip()
    if u.startswith("sqlite+aiosqlite://"):
        return "sqlite://" + u.removeprefix("sqlite+aiosqlite://")
    if u.startswith("postgresql+asyncpg://"):
        return "postgresql://" + u.removeprefix("postgresql+asyncpg://")
    if u.startswith("postgres://"):
        return "postgresql://" + u.removeprefix("postgres://")
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

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
