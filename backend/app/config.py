"""Validated application settings."""

from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "NetPay"
    environment: str = "development"
    database_url: str = "sqlite+aiosqlite:///./gateway.db"
    secret_key: SecretStr = Field(default=SecretStr("development-only-change-me"))
    log_level: str = "INFO"
    cors_origins: str = ""

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"production", "prod"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
