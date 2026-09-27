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
    app_version: str = "1.2.0"
    admin_email: str = "admin@nethub.test"
    # Break-glass bootstrap only — not used for interactive login after SSO hard cut.
    admin_password: str = "ChangeMeAdmin123!"
    admin_keycloak_id: str = Field(
        default="00000000-0000-4000-8000-000000000001",
        alias="ADMIN_KEYCLOAK_ID",
    )
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
    edge_public_base_url: str = Field(
        default="https://gateway.nethub.co.ke",
        alias="EDGE_PUBLIC_BASE_URL",
    )
    edge_callback_path_prefix: str = Field(
        default="/cb",
        alias="EDGE_CALLBACK_PATH_PREFIX",
    )

    # Keycloak = Authentication only. NetPay validates JWTs as a resource server.
    # Audience MUST be nethub-backend (NetHub API rejects other audiences).
    # Default enabled — local password login has been removed (P2 #25 hard cut).
    nethub_as_enabled: bool = Field(default=True, alias="NETHUB_AS_ENABLED")
    nethub_as_issuer: str = Field(default="", alias="NETHUB_AS_ISSUER")
    nethub_as_jwks_url: str = Field(default="", alias="NETHUB_AS_JWKS_URL")
    nethub_as_audience: str = Field(default="nethub-backend", alias="NETHUB_AS_AUDIENCE")

    # NetHub API — authorization + user context. Same Keycloak token is forwarded.
    nethub_api_base_url: str = Field(default="", alias="NETHUB_API_BASE_URL")

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
    def is_test(self) -> bool:
        return self.environment == "test"

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
