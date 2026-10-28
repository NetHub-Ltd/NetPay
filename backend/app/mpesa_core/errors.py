"""Stable, secret-safe errors for the Daraja integration boundary."""
from __future__ import annotations

from enum import StrEnum


class RetryDisposition(StrEnum):
    """Whether repeating an operation is safe without further evidence."""

    NEVER = "never"
    SAFE = "safe"
    AFTER_RECONCILIATION = "after_reconciliation"


class OperationOutcome(StrEnum):
    """Provider outcome; acceptance is deliberately distinct from completion."""

    ACCEPTED = "accepted"
    COMPLETED = "completed"
    REJECTED = "rejected"
    NOT_SENT = "not_sent"
    UNKNOWN = "unknown"


class MpesaCoreError(Exception):
    """Base error whose message must never contain credentials or raw payloads."""

    code = "mpesa_core_error"
    retry_disposition = RetryDisposition.NEVER

    def __init__(self, message: str, *, provider_code: str | None = None) -> None:
        super().__init__(message)
        self.safe_message = message
        self.provider_code = provider_code


class InvalidRequest(MpesaCoreError):
    """Input violates a local contract."""

    code = "invalid_request"


class MissingCredential(MpesaCoreError):
    """A required credential or product-specific field is missing."""

    code = "missing_credential"


class CapabilityDisabled(MpesaCoreError):
    """The integration is not configured or permitted to use this operation."""

    code = "capability_disabled"


class OAuthError(MpesaCoreError):
    """Daraja token acquisition failed or returned an invalid response."""

    code = "oauth_error"
    retry_disposition = RetryDisposition.SAFE


class ProviderRejected(MpesaCoreError):
    """Daraja definitively rejected an operation."""

    code = "provider_rejected"


class TransportFailure(MpesaCoreError):
    """The transport failed before request transmission was possible."""

    code = "transport_failure"
    retry_disposition = RetryDisposition.SAFE


class AmbiguousOutcome(MpesaCoreError):
    """The request may have reached Daraja but no definitive response arrived."""

    code = "ambiguous_outcome"
    retry_disposition = RetryDisposition.AFTER_RECONCILIATION


class MalformedProviderResponse(MpesaCoreError):
    """The provider response did not match its documented schema."""

    code = "malformed_provider_response"
    retry_disposition = RetryDisposition.AFTER_RECONCILIATION


class CatalogueContractUnavailable(MpesaCoreError):
    """No verified endpoint contract is available; no request was sent."""

    code = "catalogue_contract_unavailable"
