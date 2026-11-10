# Task tracker — NetPay #239 implementation

**Last updated:** 2026-11-10  
**Active issue:** #239 — independent Next.js deployment, mandatory BFF and server-side identity  
**Implementation branch:** feat/239-nextjs-bff-runtime  
**Verified base:** dev @ 5792662c22b7d4a5059f329d7b61427ca48769b5  
**PR target:** dev  
**Status:** implementation in progress; no PR or live staging acceptance yet.

## Approved outcome

The repository owner approved one focused implementation issue and one PR. NetPay will run as two independent services:
- Next.js App Router as a standalone Node.js server with server-side OIDC, opaque sessions, login/dashboard and mandatory same-origin HTTP BFF.
- FastAPI as an independent API service retaining payment/domain authorization, merchant membership, M2M and Safaricom callback contracts.

The browser must never receive IdP access/refresh tokens or call FastAPI directly for application API operations. FastAPI remains the authoritative merchant authorization boundary.

WSS readiness is included in ingress/security documentation. No realtime gateway or broker will be introduced until a concrete product requirement exists.

## Delivery work packages

1. Independent Next.js runtime, Docker image and deployment.
2. FastAPI separation from static frontend serving/build.
3. Server-side OIDC Authorization Code + PKCE and encrypted server-side session persistence.
4. Mandatory allowlisted Next.js BFF for browser HTTP API calls.
5. Branded login, visible Sign in navigation and protected dashboard.
6. Ingress routing for app, M2M API and Safaricom callbacks; WSS readiness design.
7. Security, integration, browser, container and staging verification.
8. Update only affected documentation and trackers.

## Current implementation notes

- Feature branch was created from verified dev commit 5792662c22b7d4a5059f329d7b61427ca48769b5.
- BFF session persistence uses a PostgreSQL table with hashed session handles and Fernet-encrypted upstream tokens.
- Internal session-store endpoints require BFF_INTERNAL_SECRET and are not intended for public ingress.
- Frontend uses a confidential OIDC client; callback and token exchange are server-side.
- Browser API allowlist currently covers human profile, memberships, merchant summary and merchant payments used by the dashboard.
- Next.js and FastAPI Docker images and CI jobs are being separated.
- Current code changes have not yet been validated by GitHub Actions; no tests are claimed as passing.
- Render deployment and operator OIDC configuration remain post-merge tasks.

## I0–I6 boundary

Do not mark I0–I6 staging acceptance complete as a side effect of #239 implementation. Earlier PRs delivered most code and CI coverage, but operator IdP/NetHubKe configuration and live staging evidence remain outstanding. Issue #238 stays open until its live evidence is recorded. Final BFF acceptance is a separate post-merge staging gate.

## Quality gates

- Backend: migrations, complete smoke suite, BFF encryption/auth/session tests, payment/M2M regression.
- Frontend: lint, strict typecheck, production build, Next server container smoke, browser login/dashboard journeys.
- Deployment: independent API/frontend images, Compose/Kubernetes config, Render staging runbook, health/readiness.
- Security: no browser tokens, no direct browser FastAPI calls, CSRF/logout, state/nonce/PKCE, cookie attributes, allowlist, session expiry/rotation/concurrency, no cross-merchant leakage.
- Staging: run the updated two-origin identity probe after owner merge/deployment and record evidence.

## Approval boundaries

- PRs target dev; repository owner performs final merge.
- No direct push to dev/main, no release, no Flux/cluster apply and no production secret changes.
- Do not claim live staging acceptance before the owner merge and resulting deployment are verified.
