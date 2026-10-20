# NetPay Architecture Decision Record

Status: proposed baseline for implementation on `work/minimal-netpay-rebuild`.
Scope: first release of the multi-merchant M-Pesa Daraja gateway.

## 1. Retained repository/deployment inventory

Inspected on 2026-10-20:

- `.github/workflows/ci.yml`: retain the branch/PR CI role, Python tests, frontend checks, and least-privilege permissions. Replace legacy SQLite/static-SPA assumptions with tests and builds for the new FastAPI + Next.js architecture.
- `.github/workflows/release.yml`: retain main-only automated patch tags/releases, GHCR publishing, and linux/amd64 + linux/arm64 build. Update checks and Docker build arguments only as needed; do not publish images from the working branch.
- `backend/Dockerfile`: retain the single published image identity and deployment port/health contract where feasible, but replace the Vite `dist/` static-copy design with an explicit production runtime for FastAPI and Next.js. Verify multi-architecture compatibility.
- `deploy/docker-compose.yml`: retain PostgreSQL and Redis services; make PostgreSQL the financial source of truth. Redis must not be a hard requirement for API payment correctness.
- `deploy/k8s/deployment.yaml`: retain the Deployment + Service intent and port 8000. Update the old image name to `ghcr.io/nethub-ltd/netpay`, and use separate liveness/readiness semantics.
- `backend/.env.example`, `backend/pyproject.toml`, and `backend/alembic.ini` remain, but are legacy-shaped and must be reconciled with the new config, dependency and migration layout.
- `backend/app/` and `frontend/` application sources are absent by design after the legacy prune. The current branch is intentionally not buildable until the rebuild is implemented.

## 2. Runtime decisions

- One repository and one release image initially. Run the FastAPI API and Next.js server as supervised processes in the same image/container, or select a documented equivalent that keeps the existing single-image deployment contract. Do not silently serve a Next.js server-rendered app as static files.
- Container listens on port 8000. Reverse proxy routes API and public/dashboard web requests to the same service entry point.
- PostgreSQL is mandatory for production readiness and all durable payment data. Redis is optional auxiliary infrastructure; Redis unavailability must not stop safe payment initiation/status handling or destroy scheduled work.
- Run migrations as an explicit deployment step/job, not implicitly in every API replica at startup.
- Liveness indicates the process is running. Readiness checks required dependencies, especially PostgreSQL, and should not confuse Redis failure with loss of financial durability.
- Keep image identity `ghcr.io/nethub-ltd/netpay`, multi-arch platforms, main-only release automation and current version/tag intent.

## 3. Proposed domain model

Use UUID primary keys unless a provider requires a specific identifier. All records are tenant-scoped where applicable.

- `Merchant`: id, display_name, status, created_at, updated_at.
- `M2MClient`: id, merchant_id, client_id, hashed_secret or public-key metadata, scopes, status, created_at, last_used_at. Return the client secret only once at creation/rotation.
- `DarajaIntegration`: id, merchant_id, opaque public integration_id, environment, shortcode, shortcode_product_type, encrypted consumer_key/consumer_secret/passkey, enabled capabilities, generated STK/C2B URLs, C2B registration status/error/timestamps, credential-validation status, timestamps. Keep encryption key outside the database and support key rotation.
- `Payment`: id, merchant_id, integration_id, client_reference, idempotency key association, amount in integer minor units, currency, normalized phone, status, provider checkout/request/receipt identifiers, safe provider result codes, initiated_at, completed_at, expires_at, timestamps. Never use floating point for money.
- `PaymentAttempt`: id, payment_id, attempt_number, request correlation ID, provider request metadata with secrets/PII excluded, initiation result, ambiguity classification, timestamps. Enforce safe retry rules.
- `ProviderCallback`: id, integration_id, provider callback type, provider/request identifier, dedupe fingerprint, minimal sanitized payload, processing status, received_at, processed_at. Uniqueness constraints must be based on verified Daraja semantics, not assumed globally unique IDs.
- `VerificationAttempt`: id, payment_id, method, outcome, safe response metadata, discrepancy code, attempted_at. Do not promise provider verification for flows unsupported by available Daraja APIs.
- `ReconciliationRun` and `ReconciliationItem`: durable run status, cursor/window, per-payment result, discrepancy and resolution history. Work is claimable/recoverable from PostgreSQL.
- `IdempotencyRecord`: merchant/client scope, key, request hash, resource/result reference, response status and expiry policy. Same key with a different request hash is a conflict.
- `EventOutbox`: stable event UUID, merchant_id, aggregate/payment ID, event type, schema version, minimal payload, created_at, delivery state, next_attempt_at, attempts. Insert in the same DB transaction as the payment transition.
- `EventDeliveryAttempt`: outbox event, destination, attempt number, HTTP status/safe error, timing, next retry. Store no authorization secrets.
- Audit records: actor, merchant scope, action, resource, correlation ID and timestamp; avoid raw credentials and unnecessary PII.

Apply foreign keys, tenant-scoped unique constraints, indexes for callback lookup, pending reconciliation and outbox claims. Do not finalize Daraja-specific uniqueness rules until verified against current docs/sandbox.

## 4. Payment state machine

Canonical states:

- `pending`: initiation accepted or awaiting provider result; not paid.
- `succeeded`: trustworthy provider evidence confirms successful payment.
- `failed`: trustworthy provider evidence confirms failure.
- `cancelled`: explicit supported cancellation evidence.
- `expired`: local/provider expiry policy has elapsed and no late result is being treated as proof of failure; retain enough context to process valid late provider evidence safely.
- `unknown`: provider outcome is ambiguous, e.g. timeout after request may have reached Daraja. This is not equivalent to failed.

Rules:

1. An accepted STK initiation response only records that the request was accepted for processing; it never marks the payment succeeded.
2. Network timeout after a request may have reached Daraja becomes `unknown` (or remains pending with an explicit ambiguous attempt); do not blindly submit a second charge.
3. Callback processing locks/serializes the relevant payment, validates integration/request correlation and any available amount/context, deduplicates, and applies only legal transitions.
4. Duplicate callbacks are acknowledged safely but have no duplicate financial effects. Out-of-order evidence must not regress a terminal state without a documented provider-specific correction policy.
5. Payment status transition and outbox event insertion commit atomically in PostgreSQL.
6. Late provider evidence for a locally expired/unknown payment is recorded and reconciled under an explicit transition policy; never discard it silently.
7. A callback routing token/integration ID is not authentication. Where Daraja provides no callback signature, use correlation, field validation, rate controls, minimal exposure and provider query/reconciliation where supported.

## 5. Initial API contract outline

Use versioned `/api/v1` routes, typed Pydantic request/response models, and a consistent error envelope. Public provider callback routes are separate from M2M-authenticated routes.

- `POST /api/v1/integrations`: validate credential authentication and required fields, then create integration and return opaque integration ID + generated URLs + safe status. Never return secrets.
- `GET /api/v1/integrations`, `GET /api/v1/integrations/{id}`: merchant-scoped safe summaries.
- `POST /api/v1/integrations/{id}/credentials/rotate`: validate replacement credentials before activation; preserve a controlled rollback/audit path without exposing prior secrets.
- `POST /api/v1/integrations/{id}/c2b/enable`: explicit opt-in; validate capability/product support, attempt URL registration, and persist registration outcome.
- `GET /api/v1/integrations/{id}/c2b/status`: safe registration state and errors.
- `POST /api/v1/payments/stk-push`: require idempotency key; validate amount/phone/reference; persist intent before provider call; return payment ID, status and safe provider request identifiers. Never return success merely because initiation was accepted.
- `GET /api/v1/payments/{id}`: merchant-scoped status.
- `POST /api/v1/payments/{id}/verification`: request verification only where supported; otherwise return an explicit unsupported/not-available outcome.
- `POST /cb/stk/{integration_id}`: public STK callback.
- `POST /cb/c2b/confirmation/{integration_id}` and `POST /cb/c2b/validation/{integration_id}`: conditional public handlers, only activated for opt-in integrations.
- `POST /api/v1/event-destinations`, `GET /api/v1/events/deliveries`, and scoped retry endpoint: optional merchant webhook delivery management.
- `GET /health/live` and `GET /health/ready`: process liveness and dependency readiness.

Use OAuth/client-credentials-style M2M auth with hashed client secrets, expiry/rotation and explicit scopes. Never accept a merchant ID from the request as the authority for scope; derive merchant scope from authenticated credentials.

## 6. Daraja capability matrix and verification gates

| Capability | Initial classification | Required behavior |
|---|---|---|
| OAuth access token | Core | Validate integration credentials against the selected environment; short-lived token cache is ephemeral only. |
| STK Push | Core | Server-generated callback URL; safe request correlation; idempotency and ambiguous timeout handling. |
| STK callback | Core | Public NetPay endpoint; strict parse, correlate and deduplicate; initiation acceptance is not payment confirmation. |
| Transaction status query | Conditional by API/product/permissions | Implement only after verifying current Daraja API requirements and response semantics; persist verification attempts. |
| Reconciliation | Core internal capability; provider evidence conditional | Recoverable PostgreSQL-backed work; report unsupported verification clearly rather than fabricating certainty. |
| C2B validation/confirmation | Conditional | Generate URLs automatically; enable/register only after explicit opt-in and confirmed product support. |
| C2B URL registration | Conditional | Verify current official documentation/sandbox requirements for Till vs Paybill and environment; expose registration result. |
| Merchant outbound webhook | Optional | Payment initiation works without a destination; durable outbox, retries and stable event ID. |
| Dashboard | Optional client | Same API contracts and permissions as M2M; never privileged by being a frontend. |

Before coding the provider adapter, verify official Daraja documentation and sandbox behavior for: token endpoint/auth format; STK required fields and callback schema; Till/Paybill product distinctions; URL registration prerequisites; transaction-status API availability/permissions and result semantics; callback acknowledgement requirements; and any idempotency/correlation guarantees. Record evidence and date in a separate provider-notes document. Do not assume a token fetch validates passkey, shortcode permissions or C2B readiness.

## 7. Build and acceptance order

1. Config/logging, DB session, migration baseline, health endpoints and test harness.
2. Merchant, M2M client auth, tenant isolation, integration credential encryption and credential validation.
3. Payment/idempotency schema and STK initiation with mocked Daraja adapter.
4. STK callback normalization, dedupe and atomic state/outbox transaction.
5. Opt-in C2B and registration state machine after provider verification.
6. PostgreSQL-backed reconciliation/outbox worker; Redis coordination only if demonstrably useful.
7. Next.js public SEO pages and private dashboard using the stable API.
8. Tawala M2M integration and end-to-end tests.
9. Update CI, image build, Compose, Kubernetes, environment docs and runtime probes together.
10. Run tests, lint/typecheck/build, migration checks, image build and integration tests; report exact commands/results.

No merge until the acceptance criteria in `docs/REBUILD_SPEC.md` are demonstrated.