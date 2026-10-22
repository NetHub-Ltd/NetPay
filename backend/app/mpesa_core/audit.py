"""Durable provider-operation audit with strict metadata redaction."""
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import Enum
from typing import Mapping
from uuid import UUID

from loguru import logger
from pydantic import SecretStr
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.integrations import DarajaIntegration
from app.models.operations import ProviderRequest
from app.mpesa_core.errors import AuditPersistenceError, IdempotencyConflictError


_SECRET_PARTS = (
    "secret", "password", "passkey", "securitycredential", "accesstoken",
    "authorization", "bearer", "privatekey", "consumerkey", "consumersecret",
)
_PHONE_PARTS = ("phonenumber", "phone_number", "msisdn")


def _json_safe(value: object) -> object:
    """Convert common Python values into JSON-safe values without exposing secrets."""
    if isinstance(value, SecretStr):
        return "[REDACTED]"
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): redact_value(str(key), item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def redact_value(key: str, value: object) -> object:
    """Redact sensitive keys and mask phone numbers before durable storage/logging."""
    normalized = key.lower().replace("-", "").replace("_", "")
    if any(part in normalized for part in _SECRET_PARTS):
        return "[REDACTED]"
    if any(part.replace("_", "") in normalized for part in _PHONE_PARTS):
        digits = "".join(char for char in str(value) if char.isdigit())
        return f"***{digits[-4:]}" if digits else "[REDACTED]"
    return _json_safe(value)


def redact_metadata(value: Mapping[str, object]) -> dict[str, object]:
    """Return a new JSON-safe metadata dictionary with sensitive values removed."""
    return {str(key): redact_value(str(key), item) for key, item in value.items()}


class ProviderOperationAuditor:
    """Write a durable started record before sending a request, then finalize it."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def start(
        self,
        integration: DarajaIntegration,
        operation: str,
        request_metadata: Mapping[str, object],
        *,
        payment_id: UUID | None = None,
        payment_attempt_id: UUID | None = None,
        idempotency_key: str | None = None,
    ) -> ProviderRequest:
        """Commit an audit record before a provider request can be sent."""
        canonical = {
            str(key): value
            for key, value in request_metadata.items()
            if str(key).lower().replace("_", "") not in {"password", "timestamp", "securitycredential"}
        }
        request_hash = (
            hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()
            if idempotency_key
            else None
        )
        try:
            async with self._session_factory() as session:
                row = ProviderRequest(
                    merchant_id=integration.merchant_id,
                    integration_id=integration.id,
                    payment_id=payment_id,
                    payment_attempt_id=payment_attempt_id,
                    operation=operation,
                    idempotency_key=idempotency_key,
                    request_hash=request_hash,
                    outcome="started",
                    request_metadata=redact_metadata(request_metadata),
                    response_metadata={},
                )
                session.add(row)
                try:
                    await session.commit()
                except IntegrityError:
                    await session.rollback()
                    if not idempotency_key:
                        raise
                    existing_result = await session.exec(
                        select(ProviderRequest).where(
                            ProviderRequest.integration_id == integration.id,
                            ProviderRequest.operation == operation,
                            ProviderRequest.idempotency_key == idempotency_key,
                        )
                    )
                    existing = existing_result.first()
                    if existing is None:
                        raise
                    if existing.request_hash != request_hash:
                        logger.warning(
                            "mpesa_idempotency_conflict operation={} integration_id={}",
                            operation, integration.integration_id,
                        )
                        raise IdempotencyConflictError(
                            "idempotency key was already used for a different provider request"
                        )
                    setattr(existing, "_idempotency_reused", True)
                    return existing
                await session.refresh(row)
                return row
        except IdempotencyConflictError:
            raise
        except Exception as exc:
            logger.error(
                "mpesa_audit_start_failed operation={} integration_id={} error_type={}",
                operation,
                integration.integration_id,
                type(exc).__name__,
            )
            raise AuditPersistenceError("provider operation was not sent because audit persistence failed") from exc

    async def finish(
        self,
        audit_id: UUID,
        *,
        outcome: str,
        http_status: int | None = None,
        provider_request_id: str | None = None,
        response_metadata: Mapping[str, object] | None = None,
    ) -> None:
        """Finalize an existing audit record without storing raw provider payloads."""
        try:
            async with self._session_factory() as session:
                row = await session.get(ProviderRequest, audit_id)
                if row is None:
                    raise LookupError("provider audit record disappeared")
                row.outcome = outcome
                row.http_status = http_status
                row.provider_request_id = provider_request_id
                row.response_metadata = redact_metadata(response_metadata or {})
                row.completed_at = datetime.now(UTC)
                session.add(row)
                await session.commit()
        except Exception as exc:
            logger.error("mpesa_audit_finish_failed audit_id={} error_type={}", str(audit_id), type(exc).__name__)
            raise AuditPersistenceError("provider result could not be durably audited") from exc
