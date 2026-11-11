# Task tracker — NetPay #245 Vercel frontend deployment

**Last updated:** 2026-11-11  
**Active issue:** #245 — align frontend deployment with Vercel  
**Implementation branch:** chore/245-vercel-frontend-deployment  
**Verified base:** dev @ b24acde75ea9a6b8161ea772247410c8d28b45d4  
**PR target:** dev  
**Status:** PR #246 is open; latest-head CI and Vercel checks are authoritative in the linked GitHub checks. Do not request review unless every required check for the latest head is terminal green.

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

- The preceding #239 work established PostgreSQL-backed BFF session persistence with hashed opaque handles and encrypted upstream tokens, confidential server-side OIDC, and the mandatory same-origin BFF.
- Internal session-store routes require `BFF_INTERNAL_SECRET`; the browser never receives upstream tokens or calls FastAPI directly.
- The dashboard BFF allowlist covers the human profile, memberships, merchant summary and merchant payment reads.
- Earlier I0–I6 work remains separate from #245. Operator IdP/NetHubKe registration and live staging evidence remain outstanding under issue #238; this deployment correction does not close that acceptance work.
- The previous PR #244 introduced the frontend container deployment path that #245 now removes. FastAPI behavior and its image/release contract remain unchanged.
