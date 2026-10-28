# M-Pesa end-to-end verification — repository audit

**Date:** 2026-10-29  
**Issue:** [#216](https://github.com/NetHub-Ltd/NetPay/issues/216)  
**Audited baseline:** `dev` at `3d77327c1d00f713b7ec088492dc91dd953d139c`  
**Task branch:** `test/mpesa-e2e-verification-216`

## Executive finding

The post-merge CI baseline is green, but the current repository does not contain an application-owned STK/C2B payment flow that can be verified end to end. The inspected `backend/app/` tree contains `main.py`, `core/`, `models/`, and `mpesa_core/`; it has no API/router package, application payment service, M2M authentication implementation, or callback route handlers. The Core package provides provider transport and pure callback parsers, not persistence or payment-state transitions.

The README currently describes several features (M2M authentication, encrypted integration onboarding, STK persistence/callback correlation, C2B confirmation, outbox delivery) as implemented. Those claims are not supported by the audited Python application tree at this baseline and should not be treated as implementation evidence until the corresponding modules and tests exist.

## What is present

- `MpesaCore`: app-scoped Daraja HTTP/OAuth client, typed operation adapters, transport/error classification, and callback parsers.
- SQLModel records: `Merchant`, `M2MClient`, `DarajaIntegration`, `Payment`, `PaymentAttempt`, `IdempotencyRecord`, `ProviderRequest`, `ProviderCallback`, `PaymentVerification`, reconciliation records, `EventOutbox`, and webhook delivery/audit records.
- Database constraints for merchant payment references, provider identifiers, idempotency, and callback deduplication.
- Existing tests for Core behavior, schema constraints, a provider-request idempotency uniqueness constraint, startup/readiness, and required-database startup failure.

## What is not established

- No authenticated M2M token/authorization dependency and merchant-scope enforcement in routes.
- No integration onboarding endpoint/service to validate Daraja credentials and encrypt/decrypt them at rest.
- No application service that atomically creates a payment, attempt, and provider request before calling Core.
- No safe state machine applying authoritative provider evidence to a payment.
- No STK callback route that correlates a callback to a known payment, validates amount/merchant context, deduplicates it durably, and commits payment transition plus outbox event atomically.
- No C2B validation/confirmation route or persisted C2B processing path.
- No API-level integration tests proving these flows.
- No authorized Daraja sandbox contract evidence. Provisional API families remain gated as documented in `docs/MPESA_CORE_SPEC.md`.

## Required correctness invariants for the next implementation

1. STK initiation acknowledgement only records provider acceptance; it never marks a payment succeeded.
2. Any request that may have reached Daraja but has no definitive response remains `unknown`/reconcilable; no blind repeat of a financial mutation.
3. A callback must correlate to a known integration/payment/attempt. An integration ID in a URL is only a routing key, not authentication.
4. Callback amount, shortcode, and provider identifiers must be checked against the stored request where the provider supplies the fields.
5. Duplicate callback delivery cannot create a second payment effect or duplicate outbox event.
6. Payment transition and durable event creation commit in one PostgreSQL transaction.
7. Callback acknowledgement semantics are tested separately from business processing; malformed/unmatched callbacks must not cause false success.
8. Merchant-scoped authorization must be enforced server-side for all private integration/payment APIs.
9. PostgreSQL remains required for startup. Redis remains auxiliary and cannot be the only store for payment/callback recovery state.

## Test matrix required before claiming the flow works

| Scenario | Required assertion |
|---|---|
| Valid STK initiation | Payment, attempt and provider-operation evidence are durable; status remains pending/accepted |
| Same merchant idempotency key + same request | Existing result is returned without a second provider mutation |
| Same key + different request hash | Conflict; no provider call |
| Provider rejects before acceptance | Safe failure recorded with sanitized evidence |
| Timeout after possible send | Outcome remains unknown; no blind retry |
| Successful STK callback | Correct known payment transitions once; receipt/amount/phone are validated where present; outbox is committed atomically |
| Duplicate callback | Idempotent acknowledgement; no second transition/event |
| Callback before initiation response is persisted | Durable callback is recoverable and correlated later, or another explicitly tested safe policy is used |
| Unknown checkout/integration | No payment is created or marked successful |
| Invalid callback structure | No state change; safe provider-appropriate acknowledgement behavior |
| C2B confirmation duplicate | Transaction ID/fingerprint dedupe prevents duplicate financial effect |
| C2B wrong shortcode/amount | Not accepted as a valid merchant payment |
| Database fails during callback | No partial payment/outbox commit; callback remains recoverable |
| Merchant A accesses Merchant B resource | Denied independent of client-supplied IDs |
| Required PostgreSQL unavailable at startup | App does not enter serving state |

## Scope boundary

This audit task was approved as a post-merge verification milestone. Since the application-level APIs, M2M authorization and payment service are absent, adding the missing pieces is not merely adding tests; it is implementing the next major product slice described in `docs/REBUILD_SPEC.md`. The rebuild specification permits the implementer to choose route shapes but requires scoped M2M authentication and clear API contracts.

Do not create unauthenticated payment endpoints or pretend that model constraints alone establish payment correctness. The next code change should implement the minimal secured application path (M2M auth + STK initiation + STK callback persistence/state transition), followed by opt-in C2B, with the test matrix above. Keep it on a topic branch and a single PR to `dev`. No production credentials or real transactions.
