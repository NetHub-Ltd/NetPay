# NetPay repository state and agent handoff

**Last updated:** 2026-10-22

## Start here — mandatory handoff procedure

This file is the quick orientation page. A new agent must read the four rebuild trackers in this order:

1. `.trackers/task.md` — goal, scope, constraints, current checklist, evidence rules.
2. `.trackers/repo-state.md` — this file: live branches, PR/issue state, handoff protocol.
3. `.trackers/milestone.md` — acceptance criteria and milestone progress.
4. `.trackers/rollback.md` — safe recovery boundaries and known rollback gaps.

Then read `AGENTS.md`, `docs/REBUILD_SPEC.md`, and refresh the relevant skills from [NetHub skills](https://github.com/NetHub-Ltd/skills-.git). Check live GitHub branch refs, latest relevant workflow runs, issue #179, and PR #178 before relying on recorded state.

### Handoff contract

The repository and linked GitHub records—not an old chat transcript—must explain:
- **Goal and scope:** what NetPay is being rebuilt to do and what is explicitly excluded.
- **Current state:** working branch, integration branch, application baseline, latest tracker commit, current milestone, and last verified result.
- **Decisions and authority:** approved constraints, user decisions, what requires explicit user approval, and what an agent must not change.
- **Evidence:** exact workflow/run IDs, commands, test results, source links, timestamps, and evidence category.
- **Open work:** blockers, unknowns, failed/skipped/not-run checks, next safe action, and acceptance criteria.
- **Recovery:** rollback options, irreversible boundaries, and deployment ownership.
- **History:** meaningful decisions and state changes recorded in trackers/issues/PRs rather than chat alone.

### Rules that prevent handoff drift

1. Before implementation, confirm the tracker baseline and write down the intended scope/next step when it is not already clear.
2. During work, update statuses as evidence changes; preserve prior decisions and record why status changed.
3. After work, synchronize trackers and relevant issue/PR records, record the resulting commit/branch state, and re-fetch the changed records to verify they persisted.
4. Keep `OBSERVED`, `VERIFIED`, `INFERRED`, `PROPOSED`, and `UNKNOWN` distinct. A written implementation claim is not proof that behavior works.
5. If records conflict, stop and reconcile the conflict; do not choose the most convenient version or silently overwrite user-approved decisions.
6. Do not infer a branch tip from this document; query live refs because tracker commits change the tip.
7. Never close/reopen issues or PRs, alter protected refs, deploy, or make destructive/scope-expanding changes without explicit user approval.
8. Keep one working branch and one PR to `dev` for this task; do not push directly to `dev` or `main`.
9. Do not modify deployment manifests; Flux owns deployment reconciliation.
10. No handoff is complete if the next safe action is unclear.

## Branches

| Branch | Last recorded commit | Meaning |
|---|---|---|
| `work/minimal-netpay-rebuild` | See live branch ref | Working branch; tracker-only commits have advanced it beyond the application baseline |
| `dev` | `5bcbf865837cedc258e6a11d483b12a28f7f2ccc` (last recorded) | Integration branch; unchanged by tracker creation as last observed |
| `main` | `a55500c2838b8ad1cc637a121f2b30f7f88132d0` (last recorded) | Older code; untouched by this task as last observed |

At the start of tracker creation, `work/minimal-netpay-rebuild` and `dev` both pointed to `5bcbf865837cedc258e6a11d483b12a28f7f2ccc`. Tracker-only commits advanced the working branch beyond the application baseline. Recheck live refs before any operation; the branch page/API is authoritative. The branches differed by tracker commits after that work; no application code was changed by tracker creation.

## Pull request and issue

- PR #178: closed, unmerged. A retarget to `dev` was rejected because head and base had no differing commits at the time. The PR was closed without explicit user approval; this was a process error and no merge occurred. Do not reopen or otherwise alter it without approval.
- Issue #179: rebuild delivery/verification tracking issue — https://github.com/NetHub-Ltd/NetPay/issues/179

## Workflow evidence carried forward

| Workflow | Run | Previously reported state | What remains |
|---|---|---|---|
| CI | [#569](https://github.com/NetHub-Ltd/NetPay/actions/runs/39757001572) | Success, from prior session summary | Re-fetch run and inspect jobs/logs before relying on this as current verification |
| Frontend build | [#15](https://github.com/NetHub-Ltd/NetPay/actions/runs/39757002712) | Success, from prior session summary | Re-fetch run and inspect jobs/logs before relying on this as current verification |

These are historical reports, not fresh verification performed during tracker creation.

## Tracker health

- `.trackers/` existed on `main` with older STK/C2B and release-workflow records.
- `.trackers/` was absent from `work/minimal-netpay-rebuild` at the start of this task.
- Four rebuild-specific trackers exist on the working branch: `task.md`, `milestone.md`, `repo-state.md`, and `rollback.md`.
- The old tracker contents are not authoritative for the clean rebuild and were not copied as the new baseline.
- Deployment manifests are out of scope; Flux owns deployment reconciliation.

## Update protocol

### Before work
1. Read this file and `task.md`, `milestone.md`, `rollback.md`, plus applicable repository instructions and skills.
2. Record intended scope, baseline commit, and changed assumptions before implementation.
3. If the tracker is missing or contradictory, repair the tracking baseline before application changes.

### During work
1. Update task/milestone status when meaningful evidence changes.
2. Record exact workflow/run IDs, commands, and outcomes; distinguish failure, skipped, and not run.
3. Stop and surface scope or approval decisions instead of silently expanding work.

### After work
1. Re-fetch branch refs and tracker files to verify persisted contents.
2. Record the resulting working-branch commit and PR/issue state.
3. Report changed, verified, not verified, risks, rollback, and follow-ups.
4. Never claim a remote write succeeded until the tool response and follow-up read confirm it.


## Database-off startup report and model inventory (2026-10-22)

- User reports that NetPay appeared to start after they turned off the database. This is a user observation, not yet reproduced by the assistant; exact runtime, image/commit, database endpoint, and logs are unknown.
- Source at the working branch has a FastAPI lifespan startup check (`app/main.py` -> `check_database` -> `SELECT 1`). With the same configured PostgreSQL endpoint truly unreachable and normal lifespan enabled, startup should not complete. Do not claim a root cause until the user's test context is established.
- The Dockerfile healthcheck uses `/health/live`, not `/health/ready`; this checks process liveness rather than DB readiness.
- The existing startup test and CI/container smoke tests use healthy PostgreSQL; no negative database-unavailable startup test was found in the inspected test file/workflow.
- Source inventory declares 16 SQLModel table classes and tests expect 16 table names; these classes are grouped in fewer files. This does not verify the schema in the user's running database.
- Next action: ask whether the test was against the local backend/container or deployed URL, then reproduce against that exact runtime; add negative startup test and verify actual Alembic revision/tables. No application code has been changed for this investigation.


## Active work — issue #180 (2026-10-22)

- Issue created first as requested: https://github.com/NetHub-Ltd/NetPay/issues/180
- Scope: prove database-unavailable startup behavior in Render/Aiven test environment; separate DB credentials/configuration and build async/sync SQLAlchemy URLs internally; rename `backend/migrations/` to `backend/alembic/`; reduce pool connection use; keep env examples and secret-safe logs.
- Working branch remains `work/minimal-netpay-rebuild`. Do not create another branch, push directly to `dev`/ `main`, alter deployment manifests, or modify protected refs.
- Current source evidence: `backend/app/core/config.py` has monolithic `DATABASE_URL`; `backend/app/core/database.py` configures pool size 5 and overflow 5; `backend/migrations/env.py` and `backend/alembic.ini` use migration path `migrations`.
- Runtime unknown: Render may report the service as running while the backend process failed, a prior image may be deployed, or the runtime may use another effective DB endpoint. These are hypotheses only; inspect deployment metadata/logs and never include secret values in issue/tracker text.
- Proposed pool starting point is size 1, no overflow, pre-ping and LIFO, but actual choice must be tested against concurrency and total Render instance/worker count. This is not a zero-idle pool.
- No application code has changed for issue #180 yet. After implementation, re-fetch files and branch state and record the exact result here.
