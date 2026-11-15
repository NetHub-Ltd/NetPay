# Task tracker — NetPay #222 public theme and conversion polish

**Last updated:** 2026-11-14
**Active issue:** #222 — centralize light/dark themes and polish public conversion
**Implementation branch:** `feat/frontend-theme-conversion`
**Verified base:** `dev` @ `f9674f9ad9693e9d496ab79901c667b13f9fec68`
**PR target:** `dev`
**Status:** implementation and local validation complete; draft PR #271 is open and CI is pending.

## Current scope and decisions

- Establish one semantic light/dark theme system in `frontend/app/globals.css`, with light as the clean-storage default and an accessible persisted theme control.
- Polish the public product and developer journeys for accurate product positioning, responsive behavior, accessibility, SEO and conversion clarity.
- Keep claims grounded in the rebuild specification; add no fabricated proof, analytics, backend/payment changes or unsupported capabilities.
- Keep `/theme-test` noindex and out of the sitemap; do not claim a ranking or conversion uplift without measurement.

## Evidence and remaining work

- `cd frontend && npm ci --no-audit --no-fund` — completed successfully.
- `cd frontend && npm test && npm run lint && npm run typecheck` — passed; 21 tests.
- `cd frontend && npm audit --audit-level=moderate && npm audit --omit=dev --audit-level=moderate` — both reported zero vulnerabilities.
- `cd frontend && NEXT_PUBLIC_SITE_URL=https://netpay.nethub.co.ke npm run build` — passed on Next.js 16.4.6.
- `cd frontend && NEXT_PUBLIC_SITE_URL=https://netpay.nethub.co.ke npm run smoke:production` — passed, including fail-closed readiness and BFF/logout protections.
- Browser QA covered 9 routes at 320, 360, 390, 768, 1024 and 1440 CSS px in both themes; axe reported zero violations, with no overflow or browser errors. Theme persistence, keyboard navigation and mobile menu were checked.
- Rendered metadata check passed: unique titles, descriptions, canonical/index rules, single H1s, structured data, sitemap and robots behavior.
- Remaining: verify required GitHub checks for PR #271's latest head SHA; keep it in draft until they pass.
- No merge, deployment, or live payment operation is in scope.

---

## Historical task tracker — NetPay #187 M-Pesa Core quality pass

**Last updated:** 2026-11-14
**Active issue:** #187 — complete M-Pesa Core quality pass
**Implementation branch:** `feat/187-mpesa-core-quality`
**Verified base:** `dev` @ `4246fbbce6361dea8d4c3506960a90aec2859ec9`
**PR target:** `dev`
**Status:** draft PR #265 open against `dev`; local validation complete; GitHub checks pending. Detailed provider operation contracts remain unverified where official docs are inaccessible.

## Approved scope

- Verify each existing Daraja operation contract against current official documentation; record unavailable/uncertain operations as gated rather than guessing.
- Bound response streaming and OAuth cache state while preserving async connection pooling and concurrent token refresh.
- Require operation-specific response fields before returning accepted outcomes; retain unknown outcomes for ambiguous requests and never blindly retry financial mutations.
- Improve typed operation/capability/result boundaries and simplify transport/operation module ownership without moving merchant authorization or idempotency out of the application layer.
- Add positive and negative tests for operation responses, failure classification, capability denial, redaction, cache lifecycle, and credential key rotation.

## Evidence and remaining work

- Official Daraja catalogue checked; detailed operation pages could not be independently retrieved. Existing provisional production capability gates remain unchanged; no uncertain contract was newly enabled.
- Added bounded streaming reads, bounded OAuth token/lock state, an operation enum/response registry, and stricter acknowledgement validation.
- Backend: `python3.12 -m alembic upgrade head`; `python3.12 -m pytest -q tests` — 107 passed.
- Container: `docker build -t ghcr.io/nethub-ltd/netpay:ci -f backend/Dockerfile .`; `bash backend/scripts/container_startup_smoke.sh` — passed.
- Frontend: `npm ci --no-audit --no-fund`, lint, strict typecheck, security tests (17 passed), production build, and production-server smoke — passed.
- Remaining: GitHub CI/Vercel checks and provider-contract verification; no merge, deployment, production credentials, or live financial operation.

---

## Historical task tracker — #245 Vercel frontend deployment

## Approved outcome

Next.js App Router is deployed independently on Vercel with its normal server runtime, server-side OIDC, opaque sessions and same-origin BFF. FastAPI retains its independent runtime, payment/domain authorization, merchant membership, M2M and Safaricom callback contracts.

Vercel Root Directory is `frontend`; keep the Next.js framework preset and default build/output settings. Do not enable static export or use a frontend Docker image. Vercel must be able to reach the configured FastAPI origin from its server runtime.

The first deployment pass uses system font stacks so the build does not depend on fetching Google Fonts. Branded local fonts are deferred to a later iteration.

## Implementation scope

1. Replace Google-hosted next/font imports with system sans/monospace stacks.
2. Remove Next.js standalone output configuration; retain server rendering, Route Handlers, BFF and server-side OIDC.
3. Remove frontend Docker build/release paths while preserving the FastAPI Docker image and release.
4. Run frontend install, lint, strict typecheck, security tests, production build and production-server smoke tests without Docker.
5. Update deployment docs, frontend docs, repository instructions and this tracker.
6. Keep backend behavior, payment contracts, BFF security and FastAPI deployment unchanged.

## Verification

- Frontend: npm ci, npm run lint, npm run typecheck, npm test, npm run build, npm run smoke:production; the host-process smoke verifies login, robots/sitemap, non-secret OIDC status, fail-closed readiness, unauthenticated BFF rejection and logout CSRF.
- Backend: existing migration, smoke-test and FastAPI container CI remain intact.
- GitHub Actions and Vercel checks must reach terminal green on the latest PR head before requesting review.
- Vercel project settings, private Vercel-to-FastAPI reachability for the BFF session-store routes and a live deployment are operator-side acceptance steps after merge; CI alone does not prove them.

## Approval boundaries

- PR targets dev; repository owner performs final merge.
- No direct push to dev/main, no release, production deployment or secret changes.
- No frontend Docker image, GHCR frontend package, static export or Docker-based full-stack deployment.
- No changes to FastAPI runtime or backend container behavior.

## Historical #239 / I0–I6 context retained

- The preceding #239 work established PostgreSQL-backed BFF session persistence with hashed opaque handles and encrypted upstream tokens, public-client server-side OIDC, and the mandatory same-origin BFF.
- Internal session-store routes require `BFF_INTERNAL_SECRET`; the browser never receives upstream tokens or calls FastAPI directly.
- The dashboard BFF allowlist covers the human profile, memberships, merchant summary and merchant payment reads.
- Earlier I0–I6 work remains separate from #245. Operator IdP/NetHubKe registration and live staging evidence remain outstanding under issue #238; this deployment correction does not close that acceptance work.
- The previous PR #244 introduced the frontend container deployment path that #245 now removes. FastAPI behavior and its image/release contract remain unchanged.


## Public OIDC client correction — #248

**Status:** Implementation committed; draft PR #249 open. Latest head `60ae8398c0b453467dffe540ba718282b0b2d405`; Vercel READY, GitGuardian success, GitHub Actions queued.
**Base:** `dev` @ `4ea426f20af6d273e1bd82c5ca2fefdb2f7fa0c5`.
**Outcome:** Next.js remains the server-side OIDC callback/BFF, but uses a public OIDC client with Authorization Code + PKCE S256. No Zitadel client secret is required.
**Changed behavior:** Token requests include `client_id` in the form body for authorization-code and refresh-token grants; no HTTP Basic auth or client_secret parameter. Auth status/readiness use the public-client settings and still require a sufficiently long `OIDC_TRANSACTION_SECRET`.
**Security boundary:** PKCE transaction remains encrypted in an HttpOnly cookie; access/refresh tokens remain server-side and encrypted in the FastAPI session store. No browser token exposure or live secret/IdP changes.
**Operator contract:** issue #233 now specifies public-client registration; live Zitadel/NetHubKe registration remains pending.
**Tests:** focused Node security tests, frontend lint/typecheck/build and production smoke are required in CI. No local test execution is claimed from the source archive.
**Next action:** monitor PR #249 checks on the latest head SHA, fix attributable failures, and update this tracker with terminal CI evidence.
