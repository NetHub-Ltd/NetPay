# NetPay — NetHub payment gateway

NetPay is NetHub's multi-merchant M-Pesa Daraja gateway. It provides merchant-scoped payment APIs, STK Push, callback handling, optional C2B registration, reconciliation and reliable payment events.

## Architecture

NetPay runs as two independent application services:

- **Next.js App Router:** public website, login, merchant dashboard, server-side OIDC and mandatory same-origin HTTP BFF.
- **FastAPI:** payment APIs, M2M authentication, merchant authorization, Daraja integration, callbacks, persistence and encrypted BFF session storage.

Zitadel handles authentication. NetHubKe remains the resource server for human identity/access decisions. The browser receives only an opaque HttpOnly session cookie; IdP tokens remain server-side. Every browser-originated HTTP request to NetPay APIs goes through Next.js. FastAPI continues to enforce merchant membership and business authorization.

M2M clients and Safaricom continue using the existing API and callback contracts. They do not depend on a human browser session.

## Start here

- Engineering rules: [AGENTS.md](AGENTS.md)
- Product and payment specification: [docs/REBUILD_SPEC.md](docs/REBUILD_SPEC.md)
- Verified Daraja capability notes: [docs/DARAJA_CAPABILITIES.md](docs/DARAJA_CAPABILITIES.md)
- Backend setup: [backend/README.md](backend/README.md)
- Frontend setup: [frontend/README.md](frontend/README.md)
- Deployment and migration runbook: [deploy/README.md](deploy/README.md)
- Human identity and BFF contract: [docs/identity-nethub-rs.md](docs/identity-nethub-rs.md)
- Staging acceptance: [docs/ops/STAGING_IDENTITY.md](docs/ops/STAGING_IDENTITY.md)

## Payment foundation

- OAuth client-credentials for merchant M2M clients, hashed client secrets, short-lived scoped bearer tokens and merchant-level authorization.
- Encrypted Daraja integration credentials and NetPay-hosted STK callback URLs.
- STK Push initiation with KES amount validation, idempotency, explicit unknown outcomes, callback correlation, deduplication and guarded state transitions.
- Opt-in C2B URL registration and confirmation handling.
- PostgreSQL-backed event outbox, signed optional merchant webhook delivery, retries/dead-letter state and worker recovery.

## Runtime and local development

Production deploys Next.js independently on Vercel and FastAPI on its own server runtime. The frontend is not built into a container or served as static files by FastAPI.

For local frontend development, copy frontend/.env.example to frontend/.env.local, configure the confidential OIDC client and BFF settings, then run:

    cd frontend
    npm ci
    npm run dev

Run FastAPI separately on port 8000:

    cd backend
    uvicorn app.main:app --reload --port 8000

See the service-specific READMEs and deployment runbook for all required settings and migrations.

## Delivery workflow

Implementation branches start from the latest verified dev and PRs target dev. The repository owner performs the final merge. CI validates backend tests/migrations and its production container, plus frontend lint, strict typecheck, security tests, a real Next.js production build and a non-container production-server smoke test. Live staging acceptance is separate from CI and must be recorded after deployment.
