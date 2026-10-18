# NetPay Minimal Rebuild — Implementation Brief for Grok

## Purpose

Rebuild NetPay in place as a small, dependable, multi-merchant M-Pesa Daraja gateway. Preserve Git history. Implement on `work/minimal-netpay-rebuild`, created from `main`. Do not modify `main` directly or merge until the new implementation passes its acceptance criteria.

This document is the source of truth for implementation scope. Read `/AGENTS.md` first.

## Product boundary

NetPay serves multiple merchants. During onboarding, a merchant supplies their own shortcode and Daraja credentials:
- consumer key
- consumer secret
- passkey
- environment and shortcode/product details needed by Daraja

NetPay attempts to fetch an OAuth token to validate that the credentials can authenticate. On success, persist the integration securely and generate a stable, opaque integration ID. The integration ID identifies the configured merchant integration in NetPay callback URLs; it is a routing identifier, not authentication proof.

Encrypt sensitive credentials at rest. Never log or return secrets, passkeys, access tokens, or authorization headers. Keep merchant and integration access strictly scoped.

## Daraja capability model: distinguish core, conditional and optional

Do not make every Daraja capability mandatory for every merchant.

### Core NetPay service
- Merchant integration creation and credential validation.
- STK Push initiation for merchant websites, POS systems and applications.
- A NetPay-hosted STK callback URL, generated and stored automatically for each integration.
- Payment status lookup and provider transaction verification where supported.
- Reconciliation and reliable payment-event publication.
- M2M authentication and merchant-scoped API access.

### Conditional C2B capabilities
- C2B confirmation and validation handlers.
- C2B URL registration, only when the merchant chooses to enable C2B and their shortcode/product supports the relevant registration.
- Generate and persist the C2B validation and confirmation URLs when an integration is saved, but do not automatically register them merely because the merchant saved credentials.
- Provide an explicit enable/register flow and show registration status/errors.
- A merchant using only STK Push must not be forced to register C2B URLs.
- Confirm behavior and requirements against the current official Daraja documentation and sandbox; don't assume all Till/Paybill products behave identically.

### Optional merchant-facing features
- Merchant-configured outbound payment-event webhooks. The feature is supported by NetPay, but a merchant does not have to configure an event destination to initiate and reconcile a payment.
- A merchant dashboard. It must use the same stable API contracts as M2M clients.

STK callback URLs are passed with the STK initiation request; NetPay hosts them. Do not require merchants to host their own callbacks.

## Minimal technology and runtime architecture

- Backend: FastAPI, Python, SQLModel/SQLAlchemy async, PostgreSQL/asyncpg, Alembic, Pydantic, pytest, Loguru.
- Frontend: Next.js App Router + TypeScript. Use server-rendered/static public pages for SEO and private authenticated dashboard routes. Avoid TypeScript `any`.
- Redis: include it as an auxiliary operational dependency for coordination, short-lived locks, scheduling/caching, or work dispatch where it demonstrably helps reconciliation.
- PostgreSQL remains the source of truth for payments, state transitions, idempotency, reconciliation history, and durable event outbox.
- Redis loss/restart must not lose payment state or permanently lose pending reconciliation/event work. Pending work must be recoverable from PostgreSQL.
- Do not add Celery, Kafka, another external broker, microservices, or a Cloudflare Worker in this initial rebuild.
- A lightweight worker/process may share the same codebase and container image for reconciliation and event delivery.
- Keep the app deployable through the existing GHCR image and deployment path.

## Payment correctness and security invariants

1. Never infer payment success from a successful STK initiation HTTP response.
2. Model pending, succeeded, failed, expired/cancelled where provider evidence supports it, and unresolved/unknown outcomes explicitly. Define legal state transitions and test them.
3. Timeouts and ambiguous outcomes remain unresolved until callback or provider verification supplies sufficient evidence.
4. Treat callbacks as untrusted inputs. The integration ID routes the request but does not authenticate it.
5. Match callbacks to known requests/transactions, validate amount and merchant context where the provider supplies the fields, and handle duplicate/out-of-order callbacks idempotently.
6. A duplicate callback or retry must not cause duplicate ledger effects or duplicate merchant business actions.
7. Use database transactions for payment state changes and the durable outbox record (transactional outbox pattern).
8. Deliver outbound events with retries/backoff and observable delivery state. Receiving consumers must be instructed to deduplicate events using stable event IDs/idempotency keys.
9. Apply tenant isolation to every read/write and M2M client permission. Never rely only on frontend checks.
10. Use safe timeout/retry rules for provider calls. Do not blindly retry an operation if it could create a second payment.
11. Log correlation IDs and safe provider metadata, never credentials or sensitive authentication material.
12. Avoid claiming an API can verify or reconcile a transaction if Daraja does not expose the required capability for that transaction type. Document limitations and fallback behavior.

## Initial API capabilities

Design typed, documented contracts before implementation. Exact routes may be chosen by Grok, but keep resource boundaries clear:
- Integrations: create/validate, get status, update/rotate credentials safely, opt in to C2B and register URLs, inspect registration status.
- Payments: initiate STK Push, retrieve payment status, request/inspect verification where supported.
- Provider callbacks: STK result callback, C2B confirmation, C2B validation, each with strict schema/acknowledgement behavior.
- Merchant events: configure destinations, inspect deliveries, safely retry failed deliveries.
- Health/readiness: distinguish process liveness from dependency readiness.

Use consistent response envelopes and typed errors. Keep public provider callback endpoints separate from authenticated M2M endpoints.

## Minimal domain records

Propose and document a normalized schema including at least:
- Merchant
- DarajaIntegration (environment, shortcode/product type, encrypted credentials, opaque integration ID, enabled capabilities, URL values and registration state)
- Payment / payment attempt (merchant, integration, amount in minor units, currency, phone, provider IDs, canonical status, timestamps)
- ProviderCallback (received payload/selected safe fields, deduplication key, processing state; avoid storing unnecessary personal data)
- Verification/reconciliation attempt and discrepancy history
- Idempotency record
- EventOutbox (durable event ID, type, payload, delivery state)
- EventDelivery/attempt history
- M2M client and scoped permissions

Enforce uniqueness constraints that prevent conflicting integrations and duplicate financial effects. Verify real Daraja shortcode/product constraints before choosing the exact uniqueness key. Store money as integer minor units, never floating-point.

## Next.js / SEO scope

- Public, indexable marketing and documentation pages with useful metadata, canonical URLs, sitemap and robots rules.
- Authenticated private merchant dashboard for integrations, transaction status, reconciliation and event delivery.
- Keep private dashboard routes out of search indexing.
- Never put Daraja secrets in frontend code or expose them in API responses.
- The dashboard must not be a prerequisite for M2M API use.

## Deployment and repository constraints

Inspect the repository and existing workflows before changing them. Preserve Git history and retain the existing GitHub Actions workflows for CI, GHCR image publishing, multi-architecture Docker builds, tagging/releases, plus the existing deployment manifests/compose contract where still applicable.

The current workflow and image build expect a Python backend under `backend/`, a frontend under `frontend/`, and `backend/Dockerfile`. The frontend is changing from Vite/React SPA to Next.js, so adapt the Dockerfile, CI and release workflow to the new architecture without removing the CI/release/image publishing behavior. Do not leave workflows pointing at deleted paths. Ensure a single reproducible image/deployment strategy; if Next.js needs a runtime process alongside FastAPI, document how both run and health checks work, or use a deliberate build/export/proxy arrangement if technically appropriate. Do not assume a static export is suitable without checking Next.js requirements.

Keep deployment configuration compatible where practical; document unavoidable environment variable or runtime-command changes. Do not add secrets to repository files.

## Build order

1. Inspect current repository, GitHub Actions, Docker build, compose/manifests, environment variables and existing operational contract. Summarize keep/replace/change before edits.
2. Propose schema, payment state machine, route contracts and Daraja capability matrix. Verify uncertain provider behaviors with official docs and sandbox tests.
3. Build foundation: configuration, DB/migrations, merchant/integration model, encryption, M2M auth, tenant isolation, health checks, tests.
4. Build onboarding + STK Push + callback handling.
5. Build opt-in C2B registration and callbacks.
6. Build verification/reconciliation, PostgreSQL-backed recoverable work, Redis coordination where useful, transactional outbox and outbound event retries.
7. Build Next.js public SEO pages and dashboard against the stable API.
8. Integrate Tawala as the first M2M consumer and test end-to-end.
9. Verify CI, multi-arch image, runtime startup, migrations, health checks and deployment compatibility.
10. Report final changes, commands/tests run, known limitations, required env vars and any provider sandbox assumptions.

Work in small, reviewable slices on this one branch. Do not create extra feature branches. Do not modify `main`. Do not merge until acceptance criteria pass.

## Acceptance criteria

- Invalid Daraja credentials cannot create an active integration.
- STK-only merchants can use NetPay without registering C2B URLs.
- Callback URLs are generated/stored automatically; C2B URL registration is opt-in and its state is visible.
- Cross-merchant access is denied by API tests.
- Duplicate/out-of-order callbacks do not create duplicate financial effects.
- Ambiguous provider outcomes are not incorrectly marked successful or failed.
- Reconciliation can resume after Redis restart and can record discrepancies.
- Pending events survive app/Redis restarts and retry without duplicate consumer effects.
- Credentials are encrypted at rest and absent from logs/API responses.
- CI tests cover happy paths and failure paths.
- Existing CI/release workflows still lint/test/build the new code and publish the intended image/tags.
- Docker image starts successfully, migrations are documented, health checks work.
- Tawala can initiate a payment and consume the resulting event end-to-end.
- Public Next.js pages are indexable; private dashboard is not.
