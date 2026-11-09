# Repository state — NetPay

**Last updated:** 2026-11-09  
**Recorded integration tip:** `82e85cb` on `dev` (PR #231 merged) — **re-fetch before work**

## Branches

| Ref | Role |
|-----|------|
| `main` | Default branch; GHCR release source; older line still tagged (e.g. v1.1.12) — rebuild identity lives on `dev` until promoted |
| `dev` | Integration branch for rebuild + identity |
| Feature branches | `feat/…`, `fix/…`, `chore/…` from latest `dev`; PR back to `dev` |

## Identity status (OBSERVED on dev)

| Capability | State |
|------------|--------|
| NetHubKe client forwarder | Present (`backend/app/identity/`) |
| SPA PKCE + `/config.json` | Present |
| Membership model + admin grant | Present |
| Membership-gated payment/merchant read APIs | **Not done** → #236 |
| Staging IdP + trusted_client registration | **Not done** → #233 |
| Deploy secret docs for NETHUB/OIDC | In progress → #234 |
| Live staging E2E | **Not done** → #238 |

## Deploy status

| Item | State |
|------|--------|
| Dockerfile multi-stage FE→BE | Present |
| `deploy/k8s` migration + API + worker | Present |
| Flux apply | Out of agent scope unless approved |
| Identity keys in deploy README | Updated under #234 |

## Open program issues

- #232 I0 trackers
- #233 I1 ops registration
- #234 I2 deploy contract
- #235 I3 token lifecycle
- #236 I4 membership APIs
- #237 I5 dashboard UI
- #238 I6 staging gate
- #239 I7 optional BFF

## CI (re-verify before relying)

Workflows: `ci.yml`, `backend-readiness.yml`, `frontend-build.yml`, `frontend-lint.yml`, `release.yml` (main only).  
Re-fetch Actions runs for the PR head under test; do not copy historical run IDs as current VERIFIED.

## Agent constraints (summary)

- PAT confidential; never echo
- No direct push to `dev`/`main`
- No production break; propose migration strategies
- Trackers updated when state changes
