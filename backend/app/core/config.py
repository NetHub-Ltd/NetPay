"""Validated settings shared by FastAPI and Alembic.

Database credentials are configured independently. URLs are constructed only
inside this module so driver-specific URLs stay consistent and passwords with
reserved URL characters are encoded safely.
"""
from functools import lru_cache
from typing import Literal

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL

SSLMode = Literal["disable", "allow", "prefer", "require", "verify-ca", "verify-full"]


class Settings(BaseSettings):
    """Centralized, validated runtime settings with secret-safe representations."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        hide_input_in_errors=True,
    )

    environment: Literal["development", "test", "staging", "production"] = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "netpay"
    db_user: str = "netpay"
    db_password: SecretStr = SecretStr("netpay")
    db_ssl_mode: SSLMode = "prefer"

    # Conservative defaults for a small Render/Aiven test service. Each process
    # owns a separate pool, so total connections scale with workers and instances.
    db_pool_size: int = 1
    db_max_overflow: int = 0
    db_pool_timeout: float = 10.0
    db_pool_recycle: int = 1800

    redis_url: SecretStr = SecretStr("redis://localhost:6379/0")
    redis_enabled: bool = True

    @field_validator("db_port")
    @classmethod
    def validate_db_port(cls, value: int) -> int:
        """Require a valid TCP port."""
        if not 1 <= value <= 65535:
            raise ValueError("DB_PORT must be between 1 and 65535")
        return value

    @field_validator("db_pool_size")
    @classmethod
    def validate_pool_size(cls, value: int) -> int:
        """Disallow a pool with no capacity."""
        if value < 1:
            raise ValueError("DB_POOL_SIZE must be at least 1")
        return value

    @field_validator("db_max_overflow")
    @classmethod
    def validate_max_overflow(cls, value: int) -> int:
        """Disallow negative overflow limits."""
        if value < 0:
            raise ValueError("DB_MAX_OVERFLOW cannot be negative")
        return value

    @field_validator("db_pool_timeout")
    @classmethod
    def validate_pool_timeout(cls, value: float) -> float:
        """Require a positive checkout timeout."""
        if value <= 0:
            raise ValueError("DB_POOL_TIMEOUT must be positive")
        return value

    @field_validator("db_pool_recycle")
    @classmethod
    def validate_pool_recycle(cls, value: int) -> int:
        """Require a positive connection recycle interval."""
        if value <= 0:
            raise ValueError("DB_POOL_RECYCLE must be positive")
        return value

    @field_validator("redis_url")
    @classmethod
    def validate_redis_url(cls, value: SecretStr) -> SecretStr:
        """Reject unsupported Redis URL schemes."""
        if not value.get_secret_value().startswith(("redis://", "rediss://", "unix://")):
            raise ValueError("REDIS_URL must use a Redis URL scheme")
        return value

    def _database_url(self, drivername: str) -> str:
        """Build a driver-specific URL without manual credential escaping."""
        url = URL.create(
            drivername=drivername,
            username=self.db_user,
            password=self.db_password.get_secret_value(),
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
            query={"sslmode": self.db_ssl_mode},
        )
        return url.render_as_string(hide_password=False)

    def async_database_url(self) -> str:
        """Return the asyncpg URL used by the FastAPI engine."""
        return self._database_url("postgresql+asyncpg")

    def alembic_database_url(self) -> str:
        """Return the synchronous psycopg URL used by Alembic."""
        return self._database_url("postgresql+psycopg")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached, validated settings."""
    return Settings()
