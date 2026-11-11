# Task tracker — NetPay #245 Vercel frontend deployment

**Last updated:** 2026-11-11  
**Active issue:** #248 — public OIDC client + PKCE  
**Implementation branch:** `fix/248-oidc-public-client`  
**Verified base:** dev @ 4ea426f20af6d273e1bd82c5ca2fefdb2f7fa0c5  
**PR target:** dev  
**Status:** implementation in progress; PR/CI handoff pending.

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

**Status:** Implementation committed to `fix/248-oidc-public-client`; PR/CI handoff pending.
**Base:** `dev` @ `4ea426f20af6d273e1bd82c5ca2fefdb2f7fa0c5`.
**Outcome:** Next.js remains the server-side OIDC callback/BFF, but uses a public OIDC client with Authorization Code + PKCE S256. No Zitadel client secret is required.
**Changed behavior:** Token requests include `client_id` in the form body for authorization-code and refresh-token grants; no HTTP Basic auth or client_secret parameter. Auth status/readiness use the public-client settings and still require a sufficiently long `OIDC_TRANSACTION_SECRET`.
**Security boundary:** PKCE transaction remains encrypted in an HttpOnly cookie; access/refresh tokens remain server-side and encrypted in the FastAPI session store. No browser token exposure or live secret/IdP changes.
**Operator contract:** issue #233 now specifies public-client registration; live Zitadel/NetHubKe registration remains pending.
**Tests:** focused Node security tests, frontend lint/typecheck/build and production smoke are required in CI. No local test execution is claimed from the source archive.
**Next action:** open PR #248 against `dev`, monitor all required checks on its latest head SHA, fix attributable failures and update this tracker with evidence.
