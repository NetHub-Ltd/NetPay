# NetPay rebuild milestones

**Last updated:** 2026-10-22  
**Branch:** `work/minimal-netpay-rebuild`  
**Specification:** [`docs/REBUILD_SPEC.md`](../docs/REBUILD_SPEC.md)  
**Status principle:** Do not mark a milestone complete without evidence.

## Milestone R0 — Tracking and repository baseline

| ID | Acceptance criterion | Status |
|---|---|---|
| R0.1 | Rebuild-specific trackers exist on the working branch | VERIFIED — created 2026-10-22 |
| R0.2 | Working/integration branch relationship is recorded | VERIFIED — branch API showed `dev` and working branch at the same known SHA |
| R0.3 | Legacy `main` trackers are not copied blindly into the rebuild | VERIFIED — old tracker contents describe the prior STK/C2B product state |
| R0.4 | Future changes update trackers before and after work | OPEN — process commitment; must be followed per task |

## Milestone R1 — Repository and delivery contract

| ID | Acceptance criterion | Status |
|---|---|---|
| R1.1 | Review retained GitHub Actions and their trigger/path behavior | OPEN |
| R1.2 | Verify Docker build context and runtime entrypoint | OPEN |
| R1.3 | Verify GHCR tags, release workflow, and image publishing contract | OPEN |
| R1.4 | Verify frontend and backend `.env.example` files | OPEN |
| R1.5 | Verify no deployment-manifest changes were introduced | OPEN — inspect diff |
| R1.6 | Review branch diff for unintended legacy code or unrelated changes | OPEN |

## Milestone R2 — Application behavior

| ID | Acceptance criterion | Status |
|---|---|---|
| R2.1 | Implementation conforms to `docs/REBUILD_SPEC.md` | OPEN — full acceptance review pending |
| R2.2 | Backend tests and readiness checks pass | UNKNOWN — inspect latest workflow/job evidence |
| R2.3 | Frontend lint/typecheck and build pass | VERIFIED only for the reported successful frontend workflow run; rerun/currentness not yet checked |
| R2.4 | Container smoke test confirms FastAPI serves frontend and API routes correctly | UNKNOWN — inspect latest workflow/job evidence |
| R2.5 | Payment security, idempotency, callback trust, and financial-state rules match the spec | OPEN — requires targeted code/test review |

## Milestone R3 — User experience and operational readiness

| ID | Acceptance criterion | Status |
|---|---|---|
| R3.1 | Landing/dashboard-preview flow is usable and links behave as intended | OPEN — code was reported updated; browser review not evidenced |
| R3.2 | Keyboard focus, skip navigation, and reduced-motion behavior are reviewed | OPEN — implementation reported, independent verification pending |
| R3.3 | Metadata, canonical URL, robots, sitemap, JSON-LD, and social image are validated | OPEN |
| R3.4 | Error, empty, loading, and recovery states are reviewed where applicable | OPEN |
| R3.5 | Release/rollback procedure is documented and consistent with Flux ownership | OPEN |

## Exit gate

Do not call the rebuild complete or merge it until:
1. R1 diff and delivery-contract checks are complete.
2. R2 behavior and required CI checks are verified.
3. R3 user-facing and operational checks are completed or explicitly accepted as out of scope.
4. The task, repository-state, and rollback trackers reflect the same final known state.
5. Remaining risks and unverified items are visible in the PR/issue report.

## Changelog

- 2026-10-22: Established a new rebuild-specific milestone map. No implementation verification is inferred from tracker creation.
