# NetPay Minimal Rebuild — Grok Implementation Specification

## Goal and working rules

Rebuild NetPay in place as a small, dependable multi-merchant M-Pesa Daraja gateway. Git history must remain intact. Work only on `work/minimal-netpay-rebuild`, created from `main`. Do not modify `main`, create more branches, or merge until the acceptance criteria pass.

This specification is the source of truth. Read `/AGENTS.md` first. The legacy application source has intentionally been pruned from this branch; inspect retained infrastructure and workflows before implementation. Do not restore the old application.

## Product model

NetPay is multi-merchant. Every merchant provides their own shortcode and Daraja credentials during onboarding:
- consumer key
- consumer secret
- passkey
- environment and shortcode/product details required by Daraja

Validate credentials by attempting the Daraja OAuth token flow. If successful, save the integration securely and generate a stable opaque integration ID. A successful token fetch proves the credentials can authenticate; it does not automatically prove every shortcode/product permission, passkey, or callback setup is valid.

Encrypt credentials at rest. Never log or return secrets, passkeys, access tokens, or authorization headers. Enforce merchant isolation server-side.

The integration ID in a callback URL is a routing identifier, not proof that the callback is authentic. Callbacks must be matched to known payment requests and processed idempotently.

## Daraja capability matrix: core vs conditional vs optional

### Core NetPay service
- Merchant integration creation and credential validation.
- STK Push initiation for websites, POS systems and applications.
- NetPay-hosted STK callback URL, generated and stored automatically for each integration.
- Payment status lookup and provider transaction verification where supported.
- Reconciliation and reliable payment-event publication.
- M2M authentication and merchant-scoped API access.

### Conditional C2B capability
- C2B confirmation and validation handlers.
- Generate and store C2B validation/confirmation URLs when an integration is saved.
- C2B URL registration is opt-in and only happens when a merchant explicitly enables C2B and the shortcode/product supports it.
- A merchant using STK Push only must not be forced to register C2B URLs.
- Show URL registration state, timestamps and errors. Verify requirements and behavior against current official Daraja documentation and sandbox. Do not assume Till and Paybill configurations are identical.
- STK callback URL is supplied by NetPay when initiating STK; the merchant does not host their own callback endpoint.

### Optional merchant-facing features
- Merchant outbound payment-event webhook destination is optional; merchants can use STK without configuring one.
- Dashboard is optional to M2M use and must use the same stable API contracts.

Do not claim transaction verification or reconciliation capability for a transaction type unless the available Daraja APIs support it. Document limitations and fallback behavior.

## Stack and runtime

- Backend: FastAPI, Python, SQLModel/SQLAlchemy async, PostgreSQL/asyncpg, Alembic, Pydantic, pytest, Loguru.
- Frontend: Next.js App Router + TypeScript; no TypeScript `any`. Public marketing/docs pages must be SEO-friendly; private dashboard routes must not be indexed.
- Redis: include as auxiliary infrastructure for coordination, short-lived locks, scheduling/caching, or dispatch where it materially helps reconciliation.
- PostgreSQL is the source of truth for payments, transitions, idempotency, reconciliation history and durable event outbox.
- Redis loss/restart must not lose payment state or permanently lose pending reconciliation/event work; pending work must be recoverable from PostgreSQL.
- No Cloudflare Worker, Celery, Kafka, separate external broker, microservices, PayPal/cards, B2C/B2B payouts or unrelated payment products in this first release.
- A lightweight worker may share the same codebase and image for reconciliation and event delivery.
- Preserve the existing GHCR image/deployment path and multi-architecture image publishing.

## Payment correctness and security invariants

1. Never infer payment success from a successful STK initiation HTTP response.
2. Model pending, succeeded, failed, expired/cancelled where provider evidence supports it, and unresolved/unknown outcomes explicitly. Define legal state transitions and test them.
3. Timeouts and ambiguous outcomes remain unresolved until callback or provider verification provides sufficient evidence.
4. Treat callbacks as untrusted inputs. Integration ID routes a callback but does not authenticate it.
5. Match callback data to known requests/transactions, validate amount and merchant context where provider fields permit, and handle duplicate/out-of-order callbacks idempotently.
6. Retries and duplicate callbacks must not cause duplicate financial effects or duplicate consumer business actions.
7. Commit payment state changes and durable outbox records atomically (transactional outbox).
8. Deliver outbound events with retry/backoff and observable delivery state. Consumers must be given stable event IDs and instructed to deduplicate.
9. Enforce tenant isolation and scoped M2M permissions on every protected operation, not only in the frontend.
10. Use careful timeout/retry rules for provider calls. Never blindly retry a request if it could create a second payment.
11. Log correlation IDs and safe provider metadata only.
12. Keep PII to the minimum required for payment processing and retention.

## Initial API groups

Define typed, documented contracts before implementation. Routes can be chosen by the implementer, but keep these boundaries:
- Integrations: create/validate, inspect status, rotate credentials safely, opt in to C2B and register URLs, inspect registration state.
- Payments: initiate STK Push, retrieve payment status, request/inspect verification where supported.
- Public provider callbacks: STK result callback, C2B confirmation and C2B validation, with strict parsing and correct Daraja acknowledgement behavior.
- Merchant events: configure destinations, inspect delivery attempts, retry failures safely.
- Health/readiness: distinguish process liveness from dependency readiness.

Use consistent typed response/error envelopes. Keep public callback endpoints separate from authenticated M2M APIs.

## Minimal domain model

Propose and document normalized records including:
- Merchant
- DarajaIntegration: environment, shortcode/product type, encrypted credentials, opaque integration ID, enabled capabilities, generated URLs and registration state
- Payment/payment attempt: merchant, integration, amount in integer minor units, currency, phone, provider IDs, canonical status, timestamps
- ProviderCallback: deduplication key, safe selected fields, processing status; avoid unnecessary raw PII
- Verification/reconciliation attempt and discrepancy history
- Idempotency record
- EventOutbox: stable event ID/type/payload/delivery state
- EventDelivery/attempt history
- M2M client and scoped permissions

Use database uniqueness constraints to prevent conflicting integration ownership and duplicate financial effects. Verify actual Daraja constraints before finalizing uniqueness keys. Never use floating point for money.

## Next.js and SEO

- Public, indexable marketing and documentation pages with metadata, canonical URLs, sitemap and robots rules.
- Authenticated private dashboard for integrations, transactions, reconciliation and event delivery.
- Keep private routes out of search indexes.
- Never expose Daraja secrets in frontend code or API responses.
- Dashboard is not required for M2M use.

## Deployment and repository constraints

Retained infrastructure includes GitHub Actions, Dockerfile, compose/Kubernetes deployment files, env examples, and build/release intent. Inspect each before changing it. Preserve CI, GHCR image publishing, version tagging/releases, multi-architecture builds and deployment manifests; adapt paths and runtime only where required by Next.js and the new backend.

Current workflows/build files refer to a Vite SPA and legacy backend paths. Do not pretend they are compatible unchanged after pruning. Update them to run the new backend tests, Next.js lint/build and intended Docker image build. Keep the published image identity `ghcr.io/nethub-ltd/netpay`, image tags/release behavior and deployable runtime contract. Choose and document a deliberate Next.js/FastAPI runtime strategy; don't assume static export is suitable without checking Next.js requirements. Health checks and container startup must match the chosen strategy. Never commit secrets.

## Build sequence

1. Inventory retained GitHub Actions, Dockerfile, compose/Kubernetes manifests, environment variables, README and runtime expectations. Report what to keep/adapt.
2. Propose schema, state machine, API contracts and Daraja capability matrix. Verify uncertain provider behavior with official docs and sandbox.
3. Implement backend foundation: config, DB/migrations, merchant/integration model, credential encryption, M2M auth, tenant isolation, health checks and tests.
4. Implement onboarding + STK Push + callback handling.
5. Implement opt-in C2B registration and callbacks.
6. Implement verification/reconciliation, PostgreSQL-backed recoverable jobs, Redis coordination where useful, transactional outbox and event retries.
7. Implement Next.js public SEO pages and dashboard against stable API contracts.
8. Integrate Tawala as first M2M consumer and test end-to-end.
9. Verify CI, multi-arch image, runtime startup, migrations, health checks and deployment compatibility.
10. Report changed files, commands/tests run, exact results, environment variables, provider assumptions and limitations.

Use reviewable commits on the single branch. Do not merge until acceptance criteria pass.

## Acceptance criteria

- Invalid Daraja credentials cannot create an active integration.
- STK-only merchants can use NetPay without registering C2B URLs.
- Callback URLs are generated/stored automatically; C2B registration is opt-in and status visible.
- Cross-merchant access is denied by automated tests.
- Duplicate/out-of-order callbacks cause no duplicate financial effects.
- Ambiguous provider outcomes are never incorrectly marked paid or failed.
- Reconciliation resumes after Redis restart and records discrepancies.
- Pending events survive app/Redis restarts and retry without duplicate consumer effects.
- Secrets are encrypted at rest and absent from logs/API responses.
- CI tests happy paths and failure paths.
- CI/release workflows test/lint/build the new code and publish the intended image/tags.
- Docker image starts, migrations are documented and health checks work.
- Tawala can initiate a payment and consume its resulting event end-to-end.
- Public Next.js pages are indexable and private dashboard pages are not.
