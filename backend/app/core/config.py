"""Validated settings shared by FastAPI and Alembic."""
from functools import lru_cache
from typing import Literal
from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Centralized settings with secret-safe connection string handling."""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore", hide_input_in_errors=True)
    environment: Literal["development", "test", "staging", "production"] = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    database_url: SecretStr = SecretStr("postgresql+asyncpg://netpay:netpay@localhost:5432/netpay")
    redis_url: SecretStr = SecretStr("redis://localhost:6379/0")
    redis_enabled: bool = True
    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: SecretStr) -> SecretStr:
        """Require the async PostgreSQL driver used by the API."""
        if not value.get_secret_value().startswith(("postgresql+asyncpg://", "postgres+asyncpg://")):
            raise ValueError("DATABASE_URL must use PostgreSQL with asyncpg")
        return value
    @field_validator("redis_url")
    @classmethod
    def validate_redis_url(cls, value: SecretStr) -> SecretStr:
        """Reject unsupported Redis URL schemes."""
        if not value.get_secret_value().startswith(("redis://", "rediss://", "unix://")):
            raise ValueError("REDIS_URL must use a Redis URL scheme")
        return value
    def alembic_database_url(self) -> str:
        """Convert runtime async URL to synchronous psycopg URL for migrations."""
        value = self.database_url.get_secret_value()
        if value.startswith("postgresql+asyncpg://"):
            return value.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
        return value.replace("postgres+asyncpg://", "postgresql+psycopg://", 1)

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached, validated settings."""
    return Settings()
