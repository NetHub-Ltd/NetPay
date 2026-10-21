# NetPay database schema

## Purpose

This document describes the initial durable persistence boundary for NetPay's
multi-merchant Daraja gateway. PostgreSQL is authoritative for payment state,
provider evidence, reconciliation work, and outbound events. Redis is only an
auxiliary coordination mechanism.

## Shared table contract

All SQLModel table models inherit `BaseMixin`:

- `id`: application-generated UUID primary key.
- `created_at`: timezone-aware UTC instant.
- `updated_at`: timezone-aware UTC instant, refreshed by SQLAlchemy on ORM updates.
- `deleted_at`: nullable soft-deletion timestamp; `NULL` means active.

The mixin does not automatically filter deleted rows. Application queries must
explicitly scope active records, and immutable financial evidence/audit records
must not expose ordinary delete operations. PostgreSQL stores these timestamps
as `TIMESTAMP WITH TIME ZONE` (`timestamptz`); normalize values to UTC at
application boundaries and reject naive datetimes.

## Tables

| Table / model | Responsibility |
|---|---|
| `merchant` / `Merchant` | Tenant identity, status, default currency, contact details and non-critical attributes |
| `m2mclient` / `M2MClient` | Merchant-scoped machine credentials; only a one-way secret hash is stored |
| `darajaintegration` / `DarajaIntegration` | Encrypted provider credentials, environment, shortcode, callback URLs and optional C2B registration state |
| `payment` / `Payment` | Canonical merchant-owned payment and verified outcome |
| `paymentattempt` / `PaymentAttempt` | Individual provider execution attempts |
| `idempotencyrecord` / `IdempotencyRecord` | Request identity and safe replay metadata |
| `providercallback` / `ProviderCallback` | Deduplicated inbound provider evidence |
| `providerrequest` / `ProviderRequest` | Outbound provider request/response metadata with secrets removed |
| `paymentverification` / `PaymentVerification` | Appendable history of transaction-status verification |
| `reconciliationrun` / `ReconciliationRun` | Bounded reconciliation job and summary |
| `reconciliationitem` / `ReconciliationItem` | Matched, unmatched and discrepant provider records |
| `eventoutbox` / `EventOutbox` | Durable domain events committed with payment changes |
| `webhookendpoint` / `WebhookEndpoint` | Multi-endpoint merchant event subscription configuration |
| `eventdelivery` / `EventDelivery` | Current delivery state for one event/endpoint pair |
| `eventdeliveryattempt` / `EventDeliveryAttempt` | Append-only delivery attempt evidence |
| `eventdestination` / `EventDestination` | Compatibility table for the existing single-destination API |
| `auditlog` / `AuditLog` | Append-only security-sensitive administrative history |

The compatibility `EventDestination` table remains because the current API and
worker depend on it. The new `WebhookEndpoint` and `EventDelivery` tables
establish the normalized multi-endpoint model; switching the dispatcher to that
model is a separate behavior change and must be tested before the compatibility
path is retired.

## Financial and provider invariants

- Monetary values are integer minor units; never use binary floating point.
  Provider-specific accepted precision must be validated before making a request.
- A successful STK initiation response is not proof of payment success.
- An ambiguous timeout stays unresolved until authoritative evidence resolves it.
- Match STK results using the provider request identifiers and the correct
  integration/attempt. Match C2B with provider transaction identity where
  available. Never match only by amount and phone.
- Callback deduplication keys must use stable, flow-specific identifiers.
  The integration ID is routing data, not authentication.
- Idempotency conflicts are arbitrated by PostgreSQL uniqueness constraints.
  Reusing a key with a different canonical request is a conflict.
- Payment state and its outbox event must be written in the same transaction.
- Provider evidence, reconciliation findings and audit history are preserved;
  corrections are represented as new evidence/resolution, not silent erasure.
- Never cascade-delete a merchant's payment or provider history.

## Migration and runtime conventions

- Application sessions use SQLAlchemy async sessions with `asyncpg`.
- Alembic may use the synchronous `psycopg2` URL derived from the same
  `DATABASE_URL` setting.
- Revision `0002_durable_domain_records` is additive and leaves revision
  `0001_initial_domain` intact.
- Run migrations before the schema drift checker. The checker currently
  verifies table and column presence; it does not prove all constraints,
  indexes or state-machine behavior are correct.
- Migration validation, callback concurrency tests, idempotency race tests,
  tenant-isolation tests and outbox transaction tests are required before
  considering this schema production-ready.

## Deliberately deferred

The double-entry ledger is not created until NetPay holds merchant balances,
owes funds, accounts for fees, or performs settlement accounting. Payouts,
automated reversals, broker infrastructure and unrelated payment products are
outside the initial scope.
