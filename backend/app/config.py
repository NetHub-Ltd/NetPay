"""Validated application settings."""

from functools import lru_cache
from typing import Self

from cryptography.fernet import Fernet
from pydantic import Field, SecretStr, model_validator
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
    credential_encryption_key: SecretStr | None = None
    public_base_url: str = "http://localhost:8000"
    log_level: str = "INFO"
    cors_origins: str = ""

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"production", "prod"}

    @model_validator(mode="after")
    def require_production_secrets(self) -> Self:
        if self.is_production:
            if not self.public_base_url.startswith("https://"):
                raise ValueError("PUBLIC_BASE_URL must use HTTPS in production")
            if len(self.secret_key.get_secret_value()) < 32 or self.secret_key.get_secret_value() == "development-only-change-me":
                raise ValueError("SECRET_KEY must be at least 32 characters and non-default in production")
            if self.credential_encryption_key is None:
                raise ValueError("CREDENTIAL_ENCRYPTION_KEY is required in production")
            try:
                Fernet(self.credential_encryption_key.get_secret_value().encode("ascii"))
            except (ValueError, UnicodeEncodeError) as exc:
                raise ValueError("CREDENTIAL_ENCRYPTION_KEY must be a valid Fernet key") from exc
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
