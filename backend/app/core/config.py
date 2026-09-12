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
    admin_password: str = "ChangeMeAdmin123!"
    internal_api_key: str = "change-me-internal-worker-secret"
    database_url: str = Field(default="sqlite+aiosqlite:///./data/gateway.db", alias="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    redis_required: bool = Field(default=False, alias="REDIS_REQUIRED")
    access_token_expire_minutes: int = 720
    cors_origins: str = "*"
    log_level: str = "INFO"
    webhook_timeout_seconds: float = 8.0
    max_webhooks_per_tenant: int = 3

    # NetHub AS (Authorization Server) — placeholders only.
    # User auth/registration is owned by NetHub AS, not NetPay.
    # When nethub_as_enabled is true AND validation is implemented, NetPay will
    # validate Bearer tokens from the AS. Default false keeps local HS256 JWT.
    # See docs/auth-model.md.
    nethub_as_enabled: bool = Field(default=False, alias="NETHUB_AS_ENABLED")
    nethub_as_issuer: str = Field(default="", alias="NETHUB_AS_ISSUER")
    nethub_as_jwks_url: str = Field(default="", alias="NETHUB_AS_JWKS_URL")
    nethub_as_audience: str = Field(default="", alias="NETHUB_AS_AUDIENCE")

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
