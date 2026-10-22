# Task: Minimal NetPay rebuild — tracking baseline

**Last updated:** 2026-10-22  
**Branch:** `work/minimal-netpay-rebuild`  
**Base/integration branch:** `dev`  
**Application baseline commit:** `5bcbf865837cedc258e6a11d483b12a28f7f2ccc`

## Goal

Track the approved minimal NetPay rebuild with evidence-based progress, acceptance criteria, and explicit separation between verified results and outstanding checks.

## Priority 0 — Agent handoff and continuity

**The repository must contain enough current information for a new agent or chat to resume safely without relying on hidden conversation history or asking the user to repeat established context.** Trackers, milestones, and linked issues are operational project state, not optional paperwork.

Before starting work, every agent must:
1. Read this file, `.trackers/repo-state.md`, `.trackers/milestone.md`, and `.trackers/rollback.md`.
2. Read `AGENTS.md`, `docs/REBUILD_SPEC.md`, and the applicable current shared skills from `https://github.com/NetHub-Ltd/skills-.git`.
3. Inspect the live branch refs and linked PR/issue state rather than trusting a potentially stale recorded SHA.
4. Identify the current milestone, last verified result, unresolved blockers/decisions, next safe action, and approval boundaries before changing application code.

During and after work, agents must update the relevant trackers and linked issue with meaningful decisions, exact evidence, changed state, blockers, and the next action. Re-fetch remote changes to confirm persistence. If the handoff state is missing, stale, or contradictory, reconcile it before proceeding with application changes. Never fill gaps with assumptions or use chat history as the only record of a decision.

A handoff is not complete merely because files exist: another agent must be able to determine **what is true, why, what remains, what is approved, and what to do next** from the repository and linked GitHub records.

## Scope and constraints

- Rebuild against `docs/REBUILD_SPEC.md`; do not restore pruned legacy application code.
- Work on `work/minimal-netpay-rebuild`; do not push directly to `dev` or `main`.
- Target future review PRs at `dev` once the working branch has commits not already on `dev`.
- Do not modify deployment manifests; Flux owns deployment reconciliation.
- Preserve frontend and backend `.env.example` files.
- Preserve CI, GHCR release/image publishing, and runtime contracts unless an approved change requires otherwise.
- Do not merge until all acceptance criteria are met.
- Keep this tracker current before work, during meaningful state changes, and after work.

## Current status

- [x] Tracker baseline created for the rebuild branch.
- [x] Record the known branch and PR/issue context.
- [x] Record known successful CI and frontend-build runs as historical reports, not fresh verification.
- [x] Make agent handoff/continuity a first-class operating requirement.
- [ ] Review full rebuild diff/commit range for unintended changes.
- [ ] Verify backend test/readiness checks from actual latest workflow results.
- [ ] Verify container smoke-test result from actual latest workflow results.
- [ ] Confirm frontend and backend `.env.example` files are present and fit current app configuration.
- [ ] Confirm release/GHCR workflow contract remains intact.
- [ ] Confirm acceptance criteria in `docs/REBUILD_SPEC.md` are satisfied.
- [ ] Perform browser-based visual/interaction review; not yet evidenced in this tracker.
- [ ] Verify that a fresh agent can resume from the trackers and linked GitHub records without relying on chat-only context.
- [ ] Reconcile this tracker with the latest run results before declaring the rebuild complete.

## Known GitHub references

- Working branch: https://github.com/NetHub-Ltd/NetPay/tree/work/minimal-netpay-rebuild
- Integration branch: https://github.com/NetHub-Ltd/NetPay/tree/dev
- Closed, unmerged PR #178 (closed because the head and base had identical commits at the time): https://github.com/NetHub-Ltd/NetPay/pull/178
- Tracking issue #179: https://github.com/NetHub-Ltd/NetPay/issues/179
- CI run #569 (previously reported successful; not freshly checked in this baseline): https://github.com/NetHub-Ltd/NetPay/actions/runs/39757001572
- Frontend build run #15 (previously reported successful; not freshly checked in this baseline): https://github.com/NetHub-Ltd/NetPay/actions/runs/39757002712

## Evidence rules

Use these labels in updates:
- **OBSERVED** — directly inspected in repository or GitHub.
- **VERIFIED** — confirmed by a test, workflow, command, or authoritative source.
- **INFERRED** — conclusion from observed evidence.
- **PROPOSED** — recommended but not yet approved/implemented.
- **UNKNOWN** — not established.

Do not mark a checkbox complete based only on intended implementation or a claim without supporting evidence. Always include exact run/commit/command references where available and distinguish "not run" from "failed" or "skipped".

## Changelog

- 2026-10-22: Created a fresh rebuild-specific tracker baseline after discovering the legacy `.trackers/` files on `main` were absent from the rebuild branch. Initial status is deliberately conservative; verification items remain open until checked against current evidence.
- 2026-10-22: Elevated agent handoff to Priority 0. Required reading order, freshness checks, evidence rules, and a resumability acceptance check are now explicit.

## Investigation opened — database-disabled startup and model count (2026-10-22)

**User-observed behavior (OBSERVED by user, not independently reproduced here):** the application appeared to start after the user disabled their database. Exact runtime, image/commit, endpoint, and logs have not yet been established.

**Current source inspection (OBSERVED):**
- `backend/app/main.py` calls `await check_database(engine)` in FastAPI lifespan before `yield`.
- `backend/app/core/database.py` implements that check using `SELECT 1`.
- Therefore, for this exact source, normal FastAPI lifespan, and the same unreachable configured PostgreSQL endpoint, successful application startup is not the expected outcome. Diagnose runtime/configuration/image mismatch or lifecycle behavior before claiming a root cause.
- `backend/Dockerfile` healthcheck probes `/health/live`, not `/health/ready`; liveness alone does not establish database readiness.
- `backend/smoke_tests/test_startup.py` covers successful startup with PostgreSQL available and readiness returning 200; it does not test startup with PostgreSQL unavailable.
- CI provisions PostgreSQL and Redis, applies migrations, and the container smoke script starts both dependencies. The existing CI path therefore does not exercise the user's database-off scenario.

**Model count (VERIFIED by source inventory):**
- `backend/app/models/` has 8 Python files including `__init__.py` and `base.py`; domain models are grouped into modules rather than one file per model.
- `__init__.py` imports/exports 16 SQLModel table classes; `BaseMixin` is a shared mixin, not a table.
- `test_database_foundation.py` explicitly expects 16 table names, and migration `0002_full_domain_schema` describes the full 16-table schema. The number of files alone does not show a model deficit.
- This verifies declared model/table count in source, not that the user's running database actually has all 16 tables or that migration application is correct in that runtime.

**Next safe actions:**
1. Establish whether the test used the local backend, Docker container, frontend dev server, or deployed site; record the actual image/commit and effective `DATABASE_URL` host without exposing credentials.
2. Reproduce with the exact PostgreSQL endpoint unavailable and capture startup logs plus process/container exit/health state.
3. Add a negative startup regression test that asserts the app does not complete startup when PostgreSQL is unavailable.
4. Separate liveness from readiness in operational health checks; review whether the container healthcheck should use `/health/ready` for the deployment's actual health semantics.
5. Verify actual applied migration revision and 16 table names in the tested database.
6. Update this tracker and issue #179 with exact evidence before implementing a fix.

No application code has been changed as part of this investigation yet.


## Issue #180 — database configuration, startup failure path, Alembic layout, and pool sizing (2026-10-22)

**Issue:** https://github.com/NetHub-Ltd/NetPay/issues/180  
**User-approved scope:** proceed with issue first, then trackers, then implementation. Issue #180 was created before these tracker updates.

### Requested outcomes
- Investigate Render test deployment behavior when the Aiven PostgreSQL database is switched off; do not infer a root cause without deployment/log evidence.
- Supply DB host, port, database, username, password, and TLS mode as separate settings; construct async and sync SQLAlchemy URLs internally and safely.
- Use an explicitly named `backend/alembic/` migration directory and update every reference without changing revision identities/history.
- Keep idle/peak PostgreSQL connections low and account for multiple workers/instances.
- Preserve both frontend and backend `.env.example`; never log credentials or full connection URLs.

### Implementation status
- **VERIFIED:** Issue #180 created at https://github.com/NetHub-Ltd/NetPay/issues/180 before implementation.
- **OBSERVED:** current `Settings` uses one `DATABASE_URL`, transforms its scheme for Alembic, and async engine currently allows pool size 5 plus overflow 5.
- **OBSERVED:** `backend/alembic.ini` currently points to `migrations`; source migration environment is `backend/migrations/env.py`.
- **UNKNOWN:** why the Render service appeared to start while Aiven was off; deployment commit, logs, effective DB host and whether this was backend startup versus platform health remain to be verified.
- **PROPOSED:** small configurable pool, initially size 1 / overflow 0, pending tests and connection-budget review. A pool still retains an idle connection once opened; zero-idle behavior is a distinct trade-off.
- No implementation changes have been made as of this tracker entry.

### Next safe action
Implement and test this issue on `work/minimal-netpay-rebuild` only. Add the negative startup regression test first, then settings/URL tests, migration-directory move and reference audit, and pool tests. Update this record with exact commands/results and re-fetch remote files after changes.
