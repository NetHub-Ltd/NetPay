# Application-level M-Pesa API contract

This document describes the initial secured application path implemented for issue #217. It does not claim live Daraja sandbox or production verification; CI uses a deterministic Core substitute.

## Authentication

Provision a merchant and M2M client out of band with `python scripts/provision_m2m_client.py --merchant-name 'Example merchant' --merchant-slug example-merchant`. Store the one-time client secret in the consumer's secret manager.

Set `M2M_TOKEN_SIGNING_SECRET` to a high-entropy secret (at least 32 random bytes) shared by all API instances. Set `MPESA_CREDENTIAL_ENCRYPTION_KEYS` and `MPESA_CREDENTIAL_ACTIVE_KEY_ID` to the Core-managed Fernet keyring. Do not reuse the M2M signing secret as an encryption key.

Exchange client credentials at `POST /api/v1/oauth/token` using JSON or form-encoded `grant_type=client_credentials`, `client_id` and `client_secret`. Optional `scope` may only narrow the provisioned scopes. Access tokens expire after 15 minutes. Clients are reloaded on each protected request so revocation and current scope changes take effect.

Scopes:
- `integrations:write` — create/list integrations and request opt-in C2B registration.
- `payments:write` — initiate STK Push.
- `payments:read` — retrieve payment status.

## Integration onboarding

`POST /api/v1/integrations` requires `integrations:write` and accepts environment, shortcode, product type, optional party-B shortcode, consumer key, consumer secret and passkey. NetPay attempts Daraja OAuth before persisting an active integration. This validates OAuth credentials only; it does not prove product permissions, shortcode entitlement, passkey correctness, or that callback delivery works.

The response contains an opaque integration ID and generated STK/C2B callback URLs, never credential material. `MPESA_PUBLIC_BASE_URL` must be the correct publicly reachable backend origin for the selected environment. STK-only integrations do not register C2B URLs automatically.

## STK initiation

`POST /api/v1/payments/stk` requires `payments:write` and an `Idempotency-Key` header. `amount_minor` is integer KES minor units and must represent a whole KES shilling amount. The request includes the integration ID, Kenyan phone number, merchant reference and description.

NetPay commits payment, attempt, provider-operation and idempotency evidence to PostgreSQL before calling Daraja. Same key + same canonical request returns the existing payment; same key + different request returns `409`. Provider acceptance leaves the payment pending. A connection failure known to occur before transmission is distinguished from an ambiguous response; ambiguous outcomes remain `unknown` and must not be retried automatically.

## Payment status and events

`GET /api/v1/payments/{payment_id}` requires `payments:read` and returns only payments owned by the authenticated merchant. Cross-merchant and nonexistent IDs return `404`.

A valid, correlated STK callback may move a pending/unknown payment to `succeeded` or `failed`. Success requires result code 0, a receipt, and consistency checks against the stored amount/phone and known provider request IDs where present. The callback record, payment transition and durable `EventOutbox` event are committed together. Duplicate callbacks do not repeat the state transition or event.

Public callback paths:
- `POST /callbacks/mpesa/stk/{integration_id}`
- `POST /callbacks/mpesa/c2b/{integration_id}/validation`
- `POST /callbacks/mpesa/c2b/{integration_id}/confirmation`

The integration ID is a routing value, not authentication. Callback payloads remain untrusted. Unmatched STK callbacks are retained for correlation after the initiation response is saved.

## C2B gating

C2B URL registration is explicit at `POST /api/v1/integrations/{integration_id}/c2b/register` and is sandbox-only pending current provider-contract and authorized sandbox verification. An ambiguous registration result is retained as unknown; repeating registration is blocked until reconciliation. STK-only onboarding does not require C2B registration.

The callback handlers remain disabled until opt-in. This implementation is not evidence that Safaricom has accepted URL registration or delivered callbacks. Production C2B is deliberately blocked pending verification.

## Error semantics

- `400` malformed token request or missing/invalid idempotency key.
- `401` invalid client/bearer token.
- `403` insufficient scope or disabled capability.
- `404` resource absent from the authenticated merchant's scope.
- `409` idempotency conflict, duplicate integration, or unresolved prior registration.
- `422` invalid request or definitive provider rejection.
- `502` known pre-send transport failure.
- `202` payment request accepted for processing or provider outcome still unknown.

## Verification boundary

Automated tests must prove route-level behavior, PostgreSQL uniqueness/persistence, merchant isolation, callback deduplication and atomic outbox behavior. CI fakes Daraja; only an explicitly configured, authorized sandbox can prove provider interoperability. See issue #216 for the exhaustive readiness gate.
