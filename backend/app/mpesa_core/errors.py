"""Typed errors for safe failure handling at the Daraja boundary."""


class MpesaCoreError(Exception):
    """Base class for expected M-Pesa Core failures."""


class ConfigurationError(MpesaCoreError):
    """Required Core configuration is missing or invalid."""


class CredentialsUnavailable(MpesaCoreError):
    """An integration has no decryptable, complete credential set."""


class IntegrationNotReady(MpesaCoreError):
    """The integration is not validated and active."""


class CapabilityDisabled(MpesaCoreError):
    """The requested Daraja capability is not enabled for this integration."""


class AuditPersistenceError(MpesaCoreError):
    """A durable provider-operation audit record could not be written."""


class ProviderAuthenticationError(MpesaCoreError):
    """Daraja OAuth could not provide an access token."""


class ProviderProtocolError(MpesaCoreError):
    """Daraja returned a response that violates the expected contract."""


class UnknownIntegration(MpesaCoreError):
    """A callback references an unknown integration."""


class IdempotencyConflictError(MpesaCoreError):
    """A reused provider-operation key carries a different request fingerprint."""
