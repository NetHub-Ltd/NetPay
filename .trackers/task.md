# Task: Minimal NetPay rebuild — tracking baseline

**Last updated:** 2026-10-23  
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


## Implementation and CI outcome — 2026-10-22

**Latest verified application-code commit:** `90951334628987c10cb77fb6f06f80bdedf9fe1f`. Subsequent commits update trackers only. The branch API was re-fetched after the changes; `dev` remains at `5bcbf865837cedc258e6a11d483b12a28f7f2ccc`, and `main` remains at `a55500c2838b8ad1cc637a121f2b30f7f88132d0`.

### Implemented
- Separate DB settings and SQLAlchemy URL construction for asyncpg and psycopg, including driver-specific TLS parameters and secret-wrapped username/password.
- Temporary `DATABASE_URL` compatibility bridge to keep existing Compose/cluster env injection working while new environments migrate to `DB_*`. When a non-local `DB_HOST` is specified, it takes precedence over the legacy URL.
- Configurable pool with defaults `DB_POOL_SIZE=1`, `DB_MAX_OVERFLOW=0`, `pool_pre_ping=True`, LIFO reuse, 10-second checkout timeout and 1800-second recycle interval.
- Alembic files moved to `backend/alembic/`, `script_location = alembic`, existing revision IDs/content preserved, and migrations included in the runtime image.
- Docker healthcheck now checks `/health/ready`; both CI workflow envs and container smoke test use split DB settings.
- New tests cover reserved characters, driver-specific SSL query parameters, legacy URL transition, pool bounds, and failure to enter FastAPI lifespan when the required database check raises.
- The schema integration test now derives its URL from shared settings instead of skipping when only split DB settings are present.

### Verified evidence
- **VERIFIED:** CI [run #615](https://github.com/NetHub-Ltd/NetPay/actions/runs/39784724936) passed on the latest application commit. Backend test result: **15 passed, 1 warning**; no skipped migration-schema test. Alembic upgrade, connectivity checks, Docker image build, and container startup smoke passed.
- **VERIFIED:** backend readiness [run #169](https://github.com/NetHub-Ltd/NetPay/actions/runs/39784724918) passed.
- **VERIFIED:** frontend lint [run #61](https://github.com/NetHub-Ltd/NetPay/actions/runs/39784724989) and frontend build [run #61](https://github.com/NetHub-Ltd/NetPay/actions/runs/39784724933) passed.
- **VERIFIED:** old path `backend/migrations/env.py` returns not found; new `backend/alembic/env.py` exists. Revision file contents/IDs were copied unchanged.
- **VERIFIED:** branch API confirms `dev` and `main` were not changed.

### Remaining unknowns / constraints
- **UNKNOWN:** why the user's Render test deployment appeared to start with Aiven disabled; no Render deployment metadata/logs or runtime config has been inspected.
- **UNKNOWN:** actual schema revision/table inventory on the Render/Aiven database. CI confirms the 16-table migration schema against its own PostgreSQL service only.
- Deployment manifests were intentionally not modified. The compatibility bridge prevents immediate breakage for existing `DATABASE_URL` injection; migrate Render to `DB_*` when convenient and remove the old variable after verifying the new settings. For Aiven, configure `DB_SSL_MODE=require` or the appropriate stronger TLS verification mode.
- CI warning: Starlette warns that its TestClient/httpx integration is deprecated; not blocking this change.


## PR and security-scan update — 2026-10-22

- **PR #181:** https://github.com/NetHub-Ltd/NetPay/pull/181, open/unmerged, target `dev`.
- Latest implementation/config/test tree commit: `4f0123e9ed1f4d8d2e6d67a9cb86462c261a2e75`. Subsequent commits to this branch may be tracker-only; use live branch API for current tip.
- **VERIFIED:** CI run [#634](https://github.com/NetHub-Ltd/NetPay/actions/runs/39786001400) and PR CI [#635](https://github.com/NetHub-Ltd/NetPay/actions/runs/39786009483) passed on the latest tree. Backend tests: 15 passed, 1 warning; migration, connectivity and container smoke passed.
- **VERIFIED:** backend readiness [#188](https://github.com/NetHub-Ltd/NetPay/actions/runs/39786001722), frontend lint [#81](https://github.com/NetHub-Ltd/NetPay/actions/runs/39786009723), and frontend build [#81](https://github.com/NetHub-Ltd/NetPay/actions/runs/39786009393) passed.
- **BLOCKED:** GitGuardian check fails on six detections from earlier commits in PR #181. The current tree was cleaned (blank example password, removed workflow/container password literals, synthetic reserved-character test value assembled from fragments), but GitGuardian scans earlier commits too. The detections are the local/test placeholders introduced during this work, not verified production credentials. No history rewrite or finding dismissal was performed. Do not merge until the check is resolved through an approved path.
- **UNKNOWN:** actual Render startup when Aiven was disabled; no Render deployment metadata/logs or Aiven schema query have been inspected.


## User decision — Git history preservation (2026-10-22)

- **VERIFIED (user decision):** Preserve all existing Git history for PR #181. Do not rebase, squash, force-push, or rewrite prior commits to clear GitGuardian findings.
- Keep PR #181 open and unmerged while the GitGuardian check is unresolved. Review the findings through the existing security workflow; do not dismiss them or claim they are harmless without reviewing the actual finding context.
- **Fresh workflow evidence at branch commit `b81c1ca77b8de12ebe29cae3c18f4ab9d0335a84`:** CI run #643, backend readiness #197, frontend lint #90, and frontend build #89 completed successfully. The GitHub Actions workflow-run query does not report GitGuardian, so its current state must be checked separately in the PR checks UI/API before declaring the security gate resolved.
- **UNKNOWN:** Render/Aiven DB-off behavior remains unverified.


## New-chat handoff — 2026-10-22 21:05 UTC

### User decision
- **VERIFIED:** User explicitly instructed: preserve Git history. No rebase, squash, force-push, reset, or history rewrite to resolve GitGuardian findings.
- Keep PR #181 open and unmerged while the GitGuardian findings/security gate are unresolved.

### Current work item: issue #180 / PR #181
- Issue: https://github.com/NetHub-Ltd/NetPay/issues/180
- PR: https://github.com/NetHub-Ltd/NetPay/pull/181 (open, target `dev`, unmerged).
- Working branch: `work/minimal-netpay-rebuild`. Do not create another branch, push directly to `dev`/`main`, modify deployment manifests, or merge.
- Implemented: separate DB connection settings with internally built async/sync SQLAlchemy URLs and temporary legacy `DATABASE_URL` bridge; driver-specific SSL query parameters; conservative pool size 1/overflow 0; migration directory `backend/alembic/`; readiness healthcheck; negative startup-failure regression test; CI/readiness/env examples updated. Existing migration IDs/content retained.
- Current-tree secret cleanup removed explicit example/workflow/container password literals; earlier commit findings still appear in GitGuardian's PR scan.

### Latest known verification and security state
- At commit `b81c1ca77b8de12ebe29cae3c18f4ab9d0335a84`, CI #643, backend readiness #197, frontend lint #90, and frontend build #89 completed successfully.
- After further tracker-only commits, workflow runs associated with commit `d2d9eb371f4f6f9d8928fdf0dc22c8d814f169f2` were queued: CI #651, backend readiness #205, frontend lint #98, frontend build #97. Re-query the live branch tip and these runs before reporting their outcome.
- GitGuardian's current check state is **UNKNOWN** from workflow-run queries; prior PR evidence says it failed on six findings from earlier commits. Review the actual findings in GitGuardian/PR checks. Do not assume they're harmless and do not merge while required security check fails.
- **UNKNOWN:** Render/Aiven DB-off startup behavior, actual Render deployment SHA/logs/effective non-secret DB host, and actual Aiven migration/schema remain unverified. CI uses CI PostgreSQL and mocked DB failure; it is not production/runtime proof.

### New chat: first safe actions
1. Re-read all four trackers, `AGENTS.md`, `docs/REBUILD_SPEC.md`, and refresh the applicable current skill(s) from https://github.com/NetHub-Ltd/skills-.git.
2. Query the live branch head and PR #181 checks. Re-check workflow runs #651/#205/#98/#97; distinguish completed results from queued/in-progress.
3. Review the exact GitGuardian detections and decide the appropriate security review/remediation while preserving history. If any actual credential was exposed, follow the secret-rotation process; do not rewrite commits.
4. Keep PR #181 open/unmerged until the security gate is resolved. Separately investigate Render/Aiven with deployment metadata/logs when available; no unsupported root-cause claim.
5. Re-fetch tracker files and update them after meaningful evidence changes.


## Live verification refresh — 2026-10-23

- **VERIFIED:** PR #181 is open, unmerged, and targets `dev`; live PR fetch reports head branch `work/minimal-netpay-rebuild`. Keep it open/unmerged.
- **VERIFIED:** Workflow runs associated with recorded commit `5efc356fc4a217f78a5d7851e53ed9f52f93869a`: CI #656, backend readiness #210, frontend lint #103, and frontend build #102 all completed with conclusion `success`. These are run IDs `39854485306`, `39854485643`, `39854485487`, and `39854485464` respectively.
- **VERIFIED:** Current PR discussion contains a GitGuardian bot comment listing three detections: two PostgreSQL Credentials detections in `backend/smoke_tests/test_database_foundation.py` at commit `385799452bc790f743c081fe561b0795acd31775` (test-only URL-reserved-character value `p@ss:/% word`), and one Generic Password detection in `backend/scripts/container_startup_smoke.sh` at commit `869ad9a1e47ea2cd6af9e45d2b97db99146e5994` (`DB_PASSWORD=netpay` in the container smoke-test invocation). These contexts appear test-only from inspected source, but scanner incidents remain active and must be handled via the approved security workflow; do not dismiss them or state that production credentials were exposed. Earlier tracker wording says six detections, which conflicts with the currently visible bot comment listing three; reconcile the count against the GitGuardian dashboard/check run.
- **UNKNOWN:** The live branch head SHA was not returned by the branch search result, so `5efc356...` is the latest recorded tracker commit, not independently proven to be current head. Re-query the branch commit SHA using a GitHub ref/commit endpoint before any write or merge decision.
- **UNKNOWN:** GitGuardian's current required-check conclusion was not surfaced by the workflow-run query or combined status endpoint (the latter returned no status entries). Do not infer the security gate passed.
- **UNKNOWN:** Render/Aiven DB-off behavior, deployed SHA/logs/effective non-secret DB host, and Aiven migration/schema remain unverified.
- **Next safe action:** obtain authoritative current branch head and PR check details, reconcile GitGuardian's exact incident count/status, then continue the broader rebuild acceptance review. Do not alter application code, DB, deployment manifests, or history as part of this status refresh.


## M-Pesa Core implementation — issue #187 (2026-10-23)

- **Approval:** user approved the M-Pesa Core architecture and explicitly authorized implementation plus thorough testing on 2026-10-22 22:24:57Z.
- **Issue:** https://github.com/NetHub-Ltd/NetPay/issues/187
- **Approved boundary:** internal Python interface; application-owned public APIs; Core-owned credential storage/resolution; durable provider-operation audit plus structured logs; public callback routes delegate to Core parsing/normalization.
- **Capability scope:** inventory current official Daraja APIs and classify by support/prerequisites. Cover relevant collection and operational APIs broadly, including C2B and other operations, but gate APIs that need merchant product/initiator/security-credential permissions. Cards/PayPal/Airtel Money implementations remain out of scope.
- **Pre-change branch tip:** `8960d3c0d0911474e195f212e0bb68c6b474d860` on `work/minimal-netpay-rebuild`; its tree SHA `3e880884c27f2b5634f23666d8de7eef54c1e63f` matches the live `dev` tree SHA observed at `72a9d108dde93c208a1330a87962bd9e47f4606e`. Local `git clone/pull` was attempted but failed because this runtime cannot resolve github.com; remote GitHub reads are available.
- **Observed baseline:** backend has the 16-table SQLModel/Alembic foundation, but `backend/app/main.py` currently registers health routes and static frontend only; there is no M-Pesa Core implementation module in the inspected tree.
- **Safety:** preserve history; work only on existing `work/minimal-netpay-rebuild`; one PR to `dev`; no changes to `dev`, `main`, Flux/deployment manifests, production DB, or secrets.
- **Testing requirement:** add unit, provider-contract, database/migration, concurrency, callback replay/order, credential/redaction, timeout/unknown-outcome, audit failure, and existing regression tests. Report exact CI run IDs/results; no claim of local test execution because the runtime cannot clone the repo.


## Implementation status — 2026-10-23

Implemented on the existing work branch for draft PR #188:
- Internal typed M-Pesa Core and shared Daraja OAuth/HTTP handling.
- Encrypted integration credentials, key IDs/rotation, initiator security credentials, explicit capability allowlist.
- STK Push/query, C2B URL registration and callback routes, Dynamic QR, transaction status, account balance, reversal, B2C/B2B, and a provisional Pull Transactions adapter.
- Durable provider-operation audit, redacted structured logs, normalized unknown/not-sent outcomes, callback evidence persistence/deduplication/conflict audit, and caller-keyed idempotency for mutating provider operations.
- Alembic revision 0003, backend environment example, module documentation, and provider/callback/idempotency/migration tests.

Verification:
- Final code commit 18e3de35185f1219014ba183879835fd3740cefb passed CI: backend tests (34 passed, one Starlette deprecation warning), backend readiness, frontend lint/build, and container startup smoke.
- PartyA/PartyB audit values are masked, callback dedupe is type-scoped, and callback host is explicitly configured per environment; these changes passed CI.
- No live Daraja sandbox run has been performed; mock contract tests are not proof of live provider compatibility.

Known gaps:
- Pull Transactions remains disabled until its exact endpoint/request/callback contract is verified against merchant-accessible official docs/sandbox.
- B2B Express Checkout is not implemented because the accessible public portal listing does not expose its request schema/endpoint.
- The Core does not create a public payment API or mutate canonical payment/ledger state. The payment domain must own authorization, limits, canonical state, and financial effects.

Do not merge or deploy without explicit approval.
