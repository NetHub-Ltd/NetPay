# Repository state — NetPay

**Last updated:** 2026-11-10  
**Verified integration baseline:** dev @ 5792662c22b7d4a5059f329d7b61427ca48769b5  
**Implementation branch:** feat/239-nextjs-bff-runtime  
**Implementation state:** in progress; awaiting CI and PR review.

## Branch and delivery model

| Ref | Role |
|---|---|
| main | Release source; GHCR release workflow remains main-only |
| dev | Integration branch; PR target |
| feat/239-nextjs-bff-runtime | Approved #239 implementation branch from verified dev baseline |

The owner performs the final merge. No direct push to dev/main, no rebase/squash/reset/force-push and no production deployment by the agent.

## Current architecture target

| Component | Target |
|---|---|
| Next.js | Independent Node.js server, standalone output, public site/login/dashboard and HTTP BFF |
| FastAPI | Independent API service; payment/domain logic, M2M, merchant authorization, callbacks and BFF session persistence |
| OIDC | Confidential server-side Authorization Code + PKCE |
| Browser session | Opaque HttpOnly cookie; no IdP tokens in JavaScript/storage |
| Session persistence | PostgreSQL hash of session handle; Fernet-encrypted access/refresh tokens |
| Browser API | Same-origin Next.js BFF only |
| M2M / Safaricom | Existing API and callback contracts retained |
| WSS | Ingress readiness documented; no gateway until a concrete realtime use case |

## I0–I6 identity work

PRs #240–#243 delivered the majority of I0–I6 code and CI work. The following remain separate operator/live acceptance items:
- I1: actual confidential IdP registration and NetHubKe trusted-client configuration/evidence.
- I6 / issue #238: live staging browser and API evidence; CI alone is insufficient.
- Existing M2M/payment regression evidence must be recorded as part of staging acceptance.

Do not mark I0–I6 live acceptance complete from this #239 PR. Keep #238 open until evidence is recorded.

## #239 implementation

- Issue #239 was re-scoped and approved on 2026-11-10 as mandatory independent Next.js + BFF + server-side identity.
- Branch feat/239-nextjs-bff-runtime created from dev SHA 5792662c22b7d4a5059f329d7b61427ca48769b5.
- Changes are in progress. Initial CI on an earlier PR head passed frontend lint/typecheck/build and backend readiness, but found two test-fixture/assertion issues plus a frontend container-smoke failure. The test issues are corrected; local Node security-helper tests pass 7/7. A fresh full CI run on the current head remains outstanding.
- PR #244 is open against dev. No live staging deployment has been performed.
- Render staging currently needs an independently deployed frontend service and operator-managed OIDC/runtime configuration after merge.

## CI and deployment

Preserve the FastAPI image identity ghcr.io/nethub-ltd/netpay and release behavior; add ghcr.io/nethub-ltd/netpay-frontend. CI must build/test both independently. Kubernetes and Compose now target separate services in this branch. Render configuration is documented as a two-service operator rollout; no live settings are assumed.

## Evidence rules

Use OBSERVED / VERIFIED / INFERRED / PROPOSED / UNKNOWN. CI results verify CI only. Live staging, operator configuration and deployment status require direct evidence. Never record secrets, access tokens, refresh tokens or session cookies.
