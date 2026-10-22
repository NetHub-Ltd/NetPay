# NetPay rebuild milestones

**Last updated:** 2026-10-22  
**Branch:** `work/minimal-netpay-rebuild`  
**Specification:** [`docs/REBUILD_SPEC.md`](../docs/REBUILD_SPEC.md)  
**Status principle:** Do not mark a milestone complete without evidence.

## Milestone R0 — Tracking and repository baseline

| ID | Acceptance criterion | Status |
|---|---|---|
| R0.1 | Rebuild-specific trackers exist on the working branch | VERIFIED — created 2026-10-22 |
| R0.2 | Working/integration branch relationship is recorded | VERIFIED — branch API showed `dev` and working branch at the same known SHA before tracker-only commits |
| R0.3 | Legacy `main` trackers are not copied blindly into the rebuild | VERIFIED — old tracker contents describe the prior STK/C2B product state |
| R0.4 | Trackers are updated before, during, and after meaningful work | ONGOING GATE — must be followed on every task |
| R0.5 | Handoff protocol tells a new agent what to read, how to refresh state, and how to avoid chat-only assumptions | VERIFIED — documented in `.trackers/task.md` and `.trackers/repo-state.md` |
| R0.6 | A new agent can identify current truth, rationale, approval boundaries, blockers, and next safe action from repository records alone | OPEN — perform an explicit handoff-readiness check before calling this verified |

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
| R2.3 | Frontend lint/typecheck and build pass | HISTORICAL REPORT ONLY — a prior successful frontend workflow was reported; currentness not checked |
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
5. A handoff-readiness check confirms the next agent can resume from repository records without chat-only context.
6. Remaining risks and unverified items are visible in the PR/issue report.

## Changelog

- 2026-10-22: Established a new rebuild-specific milestone map. No implementation verification is inferred from tracker creation.
- 2026-10-22: Added explicit handoff criteria. Documentation of the protocol is verified; successful independent resumption remains open until checked.

## Added regression checks — database unavailable (2026-10-22)

| ID | Acceptance criterion | Status |
|---|---|---|
| R2.6 | With the configured PostgreSQL endpoint unavailable, the exact deployed/local API runtime must not report successful startup if DB connectivity is a startup requirement | OPEN — user observed apparent startup; exact runtime and logs not yet captured |
| R2.7 | CI has a negative regression test proving startup fails when PostgreSQL cannot answer `SELECT 1` | OPEN — existing startup test covers only the healthy-database path |
| R2.8 | Container/deployment health semantics distinguish process liveness from dependency readiness | OPEN — Dockerfile healthcheck currently uses `/health/live` |
| R2.9 | Tested database has Alembic head `0002_full_domain_schema` and all 16 expected domain tables | OPEN — source test defines the expected schema; the user's running database has not been inspected |

Model source inventory: 16 SQLModel table classes are declared/exported across grouped modules; file count is not model count. Runtime schema remains separately unverified.


## Issue #180 — database reliability and connection management (2026-10-22)

| ID | Acceptance criterion | Status |
|---|---|---|
| DB.1 | GitHub issue created before tracker and application changes | VERIFIED — [#180](https://github.com/NetHub-Ltd/NetPay/issues/180) |
| DB.2 | Reproduce/investigate Render startup when Aiven is unavailable | OPEN — exact deployment commit/logs/effective host not yet established |
| DB.3 | Negative regression test proves required PostgreSQL failure blocks completed backend startup | VERIFIED IN CI — lifespan test passes when required DB check raises; real Render outage still unverified |
| DB.4 | Separate validated DB connection fields construct async and sync URLs safely | VERIFIED IN CI — URL/reserved-character/driver SSL/legacy bridge tests pass |
| DB.5 | Rename migration directory to `backend/alembic/` and update all references without changing revisions | VERIFIED IN CI — Alembic upgrade and container smoke pass; revision IDs/content preserved |
| DB.6 | Reduce idle/peak connections and account for worker/instance multiplication | IMPLEMENTED + TESTED — default pool size 1, overflow 0; runtime load profile not measured |
| DB.7 | Run tests, migration checks, reference audit, and relevant CI/build checks | VERIFIED — CI #634/#635 success (15 passed, 1 warning; no skipped migration-schema test), backend readiness #188 success, frontend lint/build #81 success |
| DB.8 | Update/re-fetch trackers and issue with exact outcomes | IN PROGRESS — PR #181 and issue #180 updated; final tracker writes/read-back remain |

**Pool decision pending verification:** proposed initial `pool_size=1`, `max_overflow=0`, `pool_pre_ping=True`, `pool_use_lifo=True`, configurable timeout/recycle. This retains one idle connection per active engine after first use; `NullPool` would be required if the goal is to retain no idle connections, at the cost of connection setup per checkout.


### Verification update — 2026-10-22
- CI #615 passed at commit `90951334628987c10cb77fb6f06f80bdedf9fe1f`: 15 passed, 1 warning, no skipped tests; migration application, PostgreSQL/Redis checks, Docker build and container smoke passed.
- Backend readiness #169 and frontend lint/build #61 passed on the same commit.
- Real Render/Aiven DB-off behavior and actual Render schema remain unknown. Do not mark DB.2 or the Render/Aiven portion of schema verification as verified.


## Pull request gate — 2026-10-22

- PR [#181](https://github.com/NetHub-Ltd/NetPay/pull/181) is open, targeting `dev`, not merged.
- CI #634/#635, backend readiness #188, frontend lint/build #81 pass on tree commit `4f0123e9ed1f4d8d2e6d67a9cb86462c261a2e75`.
- GitGuardian security check **FAILS** because it scans six placeholder/test credential occurrences in earlier commits of this PR. Current tree occurrences were removed, but history has not been rewritten. This is a merge blocker until explicitly resolved; preserve history and do not dismiss/rewrite without approval.
- Render/Aiven database-off behavior remains unverified.
