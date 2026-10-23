# NetPay database schema

## Source of truth

PostgreSQL is authoritative for merchant configuration, payment state, provider
evidence, reconciliation history, idempotency, audit records, and durable event
delivery. Redis is auxiliary and must never be the only place where pending
financial or delivery work exists.

## Shared record contract

All 16 SQLModel tables inherit a UUID primary key and timezone-aware UTC
`created_at`, `updated_at`, and nullable `deleted_at` lifecycle fields.
The timestamp factory returns aware UTC instants. Database timestamps use
PostgreSQL `TIMESTAMP WITH TIME ZONE`. Monetary values are integers in minor
units; currency is stored separately.

Soft deletion is not an automatic query filter. Callers must scope active rows
explicitly. Payment, callback, reconciliation, outbox, delivery-attempt, and
audit evidence must not be hard-deleted by ordinary application operations.

## Tables

| Table | Responsibility |
|---|---|
| `merchant` | Merchant identity and default currency |
| `providerintegration` (`DarajaIntegration`) | Merchant-scoped Daraja environment, encrypted credentials, shortcode/product configuration, generated callback URLs and opt-in C2B registration state |
| `m2mclient` | Hashed machine-client secret, merchant ownership, scopes, expiry and revocation |
| `payment` | Canonical payment intent, amount, currency, provider identifiers and verified status |
| `paymentattempt` | Attempt-level status, correlation ID and safe error metadata |
| `idempotencyrecord` | Merchant/client request fingerprint and replay snapshot |
| `providercallback` | Deduplicated provider callback evidence and processing status |
| `paymentverification` | Historical provider verification evidence |
| `providerrequest` | Safe request/response metadata for outbound provider operations |
| `reconciliationrun` | Bounded reconciliation window and execution result |
| `reconciliationitem` | Individual match or discrepancy and resolution details |
| `eventoutbox` | Transactional, stable-ID event records |
| `webhookendpoint` | Merchant-owned event destination and encrypted signing-secret material |
| `eventdelivery` | Current state and retry schedule for an event/endpoint pair |
| `eventdeliveryattempt` | Append-only HTTP delivery attempt history |
| `auditevent` (`AuditLog`) | Security-sensitive actor/action/resource audit evidence |

## Safety invariants

- An accepted STK initiation request is not payment success.
- Provider callbacks are untrusted; an integration ID is a routing identifier,
  not authentication. Match callbacks to known payment attempts and process
  duplicates idempotently.
- A callback fingerprint and provider event key are database-unique within an
  integration.
- Idempotency keys are unique within a merchant. Request hashes are stored so
  reusing a key with a different request can be rejected.
- Payment amounts must be positive integer minor units.
- Reconciliation windows must have a start before their end; reported amounts
  cannot be negative.
- Outbox state is stored in PostgreSQL so dispatch can resume after Redis or
  application restarts.
- Daraja consumer keys, consumer secrets, passkeys and webhook signing secrets
  are ciphertext or secret references only; plaintext must never be logged or
  returned from an API.
- C2B URL registration is optional and must only be attempted when a merchant
  explicitly enables C2B. STK-only integrations remain valid.

## Migration workflow

Use `alembic upgrade head` to apply the versioned schema. The initial revision
is retained; `0002_full_domain_schema` expands existing records and creates
the remaining domain tables without dropping the original foundation tables.
The backend uses an async SQLAlchemy/SQLModel engine and request-scoped
`AsyncSession` instances. Alembic uses the same validated database URL through
the synchronous psycopg driver.
