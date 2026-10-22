"""Validated settings shared by FastAPI and Alembic.

Database credentials are configured independently. URLs are constructed only
inside this module so driver-specific URLs stay consistent and passwords with
reserved URL characters are encoded safely.
"""
from functools import lru_cache
from typing import Any, Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL, make_url

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

    # Temporary bridge for existing deployment secrets/manifests. New environments
    # should provide DB_* fields; explicit non-local DB_HOST takes precedence.
    database_url: SecretStr | None = Field(default=None, repr=False, exclude=True)

    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "netpay"
    db_user: SecretStr = SecretStr("netpay")
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

    @model_validator(mode="before")
    @classmethod
    def bridge_legacy_database_url(cls, values: Any) -> Any:
        """Read an existing DATABASE_URL only when split settings are not specific.

        This keeps current deployment secrets working during the environment
        variable migration. A configured non-local DB_HOST always wins.
        """
        if not isinstance(values, dict):
            return values
        legacy_value = values.get("database_url")
        if legacy_value is None:
            return values
        raw_url = legacy_value.get_secret_value() if isinstance(legacy_value, SecretStr) else str(legacy_value)
        parsed = make_url(raw_url)
        if parsed.drivername not in {"postgresql+asyncpg", "postgresql+psycopg", "postgresql"}:
            raise ValueError("DATABASE_URL must use PostgreSQL")
        configured_host = values.get("db_host")
        # A localhost default from a copied .env.example must not mask a URL
        # injected by existing Compose/cluster deployment configuration.
        if configured_host not in (None, "", "localhost") and configured_host != parsed.host:
            return values
        values["db_host"] = parsed.host or "localhost"
        values["db_port"] = parsed.port or 5432
        values["db_name"] = parsed.database or "netpay"
        if parsed.username is not None:
            values["db_user"] = parsed.username
        if parsed.password is not None:
            values["db_password"] = parsed.password
        if "sslmode" in parsed.query:
            values["db_ssl_mode"] = parsed.query["sslmode"]
        return values

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
        # asyncpg expects the `ssl` keyword; psycopg uses `sslmode`.
        ssl_parameter = "ssl" if drivername.endswith("+asyncpg") else "sslmode"
        url = URL.create(
            drivername=drivername,
            username=self.db_user.get_secret_value(),
            password=self.db_password.get_secret_value(),
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
            query={ssl_parameter: self.db_ssl_mode},
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
