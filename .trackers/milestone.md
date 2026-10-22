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


### User decision — preserve Git history (2026-10-22)
- **VERIFIED:** User explicitly chose to preserve Git history. No history rewrite, force-push, or squash/rebase is authorized for resolving the PR #181 GitGuardian finding.
- PR #181 remains open/unmerged until the existing GitGuardian finding is reviewed and the required security gate is green.
- Fresh branch-associated workflow runs at `b81c1ca77b8de12ebe29cae3c18f4ab9d0335a84`: CI #643, readiness #197, frontend lint #90, frontend build #89 all completed successfully. GitGuardian's current result still needs separate verification; do not infer it from these workflow runs.


## New-chat handoff — 2026-10-22 21:05 UTC

- **User decision (VERIFIED):** Preserve Git history. Do not rebase, squash, force-push, reset, rewrite commits, or dismiss GitGuardian findings as a shortcut.
- PR #181 remains open against `dev`, unmerged: https://github.com/NetHub-Ltd/NetPay/pull/181. Issue #180: https://github.com/NetHub-Ltd/NetPay/issues/180.
- Implementation/config/test changes described above are in the working branch; no deployment manifests, Flux resources, `dev`, `main`, or production database were changed.
- Last confirmed green run set on prior tip `b81c1ca77b8de12ebe29cae3c18f4ab9d0335a84`: CI #643, readiness #197, frontend lint #90, frontend build #89.
- Subsequent tracker-only commit `d2d9eb371f4f6f9d8928fdf0dc22c8d814f169f2` had queued runs CI #651, readiness #205, frontend lint #98, frontend build #97 at last query. Recheck latest live branch and outcomes.
- GitGuardian: prior evidence reports six findings from earlier PR commits; current check status was not returned by workflow-run API. Review exact findings and preserve history. Do not merge until the required security gate passes.
- Render/Aiven database-off behavior and actual deployed schema remain **UNKNOWN**.
- Next milestone action: refresh live refs/checks, inspect GitGuardian finding context, and record verified outcomes before any merge/release decision.


## Live verification refresh — 2026-10-23

| ID | Acceptance criterion | Updated status |
|---|---|---|
| DB.3 | Negative startup regression | **VERIFIED IN CI** — CI #656 succeeded on recorded commit `5efc356fc4a217f78a5d7851e53ed9f52f93869a`; this remains a mocked failure-path test, not proof from Render |
| DB.4 | Separate DB fields and safe URL construction | **VERIFIED IN CI** — CI #656 succeeded; reserved-character test value is among active GitGuardian detections and still requires security review |
| DB.5 | Alembic directory and migration checks | **VERIFIED IN CI** — CI #656 succeeded; real Aiven schema remains unknown |
| DB.6 | Conservative pool | **IMPLEMENTED + CI GREEN** — runtime multi-worker/instance connection budget not measured |
| R2.2 | Backend tests/readiness | **VERIFIED** — CI #656 and readiness #210 succeeded |
| R2.3 | Frontend lint/build | **VERIFIED** — lint #103 and build #102 succeeded |
| R2.4 | Container smoke | **VERIFIED VIA CI #656** — smoke step outcome included in CI run success; deployment runtime is separate |
| SEC.1 | GitGuardian required security gate | **BLOCKED/UNKNOWN CURRENT CHECK** — live PR bot comment lists three detections (two PostgreSQL Credentials in a test URL value, one Generic Password in smoke-test env); prior tracker said six. Reconcile dashboard/check status; do not merge |
| DB.2 / R2.6 / R2.9 | Render DB-off behavior and actual Aiven schema | **UNKNOWN** — no deployment logs/metadata or schema query |
| R1.1–R1.6, R2.1, R2.5, R3.x | Broader rebuild acceptance | **OPEN** — current successful workflow results do not close the full diff, delivery, payment-security, browser UX, metadata, and release/rollback review |

Evidence refresh date: 2026-10-23. Runs above are associated with recorded commit `5efc356fc4a217f78a5d7851e53ed9f52f93869a`; branch head SHA was not exposed by branch search and must be re-queried.


## Security foundation — issue #183 (2026-10-23)

| Criterion | Status |
|---|---|
| Authenticated provider credential encryption primitive | IMPLEMENTED; unit tests added; latest head results pending |
| No default/ephemeral encryption key | IMPLEMENTED; missing/invalid key fails closed on use |
| M2M client-secret hashing and one-time generation helper | IMPLEMENTED; unit tests added; latest head results pending |
| Signed, short-lived token claims with audience/type/expiry/client/merchant/scopes | IMPLEMENTED; unit tests added; latest head results pending |
| Persisted client/merchant status and revocation rechecked on protected requests | IMPLEMENTED in dependency; route-level database integration tests still needed |
| OAuth token endpoint and safe identity endpoint | IMPLEMENTED; endpoint tests and full provisioning workflow remain open |
| Render environment secrets configured for new features | UNKNOWN — not changed or independently inspected |
| Current latest CI on head `14134f360865c9d360e702abaa4306400cecaf25` | QUEUED at last read; refresh before marking verified |

PR [#184](https://github.com/NetHub-Ltd/NetPay/pull/184) is a draft against `dev`. This phase is a foundation only; merchant onboarding, Daraja OAuth validation, STK Push, callback processing, reconciliation and event delivery remain later milestones.
