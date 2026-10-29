# NetPay repository state and agent handoff

**Last updated:** 2026-10-29

## Current active task — mpesa_core

- **Branch:** `feat/mpesa-core-complete`; base `dev` at `82bae5b7c8e1704491b0aa8eec1dfa8fa948364f` when the branch was created.
- **Issue / PR:** issue #187; draft PR #215 targets `dev`, remains unmerged.
- **Latest verified code head:** `8fb5a3ba1004af8ff240ed13cc2cd07ab283b1d3`; CI run `40780804974` passed backend tests, migration, PostgreSQL/Redis, production image build without push, container startup smoke test, frontend lint/build and backend readiness.
- **Open blocker:** verify provisional Bill Manager, Ratiba, B2B Express Checkout, Lipa na Bonga and Pull Transactions contracts with authenticated Daraja documentation/sandbox before production enablement. These capabilities are production-gated in Core.
- **No deployment or merge:** no image was pushed; Flux/deployment manifests were not changed; PR #215 is for review only.

## Start here — mandatory handoff procedure

This file is the quick orientation page. A new agent must read the four rebuild trackers in this order:

1. `.trackers/task.md` — goal, scope, constraints, current checklist, evidence rules.
2. `.trackers/repo-state.md` — this file: live branches, PR/issue state, handoff protocol.
3. `.trackers/milestone.md` — acceptance criteria and milestone progress.
4. `.trackers/rollback.md` — safe recovery boundaries and known rollback gaps.

Then read `AGENTS.md`, `docs/REBUILD_SPEC.md`, and refresh the relevant skills from [NetHub skills](https://github.com/NetHub-Ltd/skills-.git). Check live GitHub branch refs, latest workflow runs, issue #187 and PR #215 before relying on recorded state. Issue #179/PR #178 are historical rebuild records only.

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


## Current verified state — issue #180 (2026-10-22)

- Latest verified application-code commit: `90951334628987c10cb77fb6f06f80bdedf9fe1f`. Tracker-only commits have since advanced `work/minimal-netpay-rebuild`; query the branch API for the live tip.
- Latest CI [#615](https://github.com/NetHub-Ltd/NetPay/actions/runs/39784724936) passed: 15 backend tests passed, 1 warning, no skipped tests; migration application, PostgreSQL/Redis connectivity, container build and smoke passed.
- Backend readiness [#169](https://github.com/NetHub-Ltd/NetPay/actions/runs/39784724918), frontend lint [#61](https://github.com/NetHub-Ltd/NetPay/actions/runs/39784724989), and frontend build [#61](https://github.com/NetHub-Ltd/NetPay/actions/runs/39784724933) passed.
- The first CI attempt exposed a real driver mismatch: asyncpg rejects `sslmode`; fixed by emitting `ssl` in the async URL and retaining `sslmode` for psycopg. Later checks passed.
- Migration path is now `backend/alembic/`; `backend/alembic.ini` points at it; revision IDs/content were preserved; Docker image includes migration files.
- Database config now prefers explicit `DB_*` settings and temporarily accepts legacy `DATABASE_URL` for existing deployment env injection. Do not log generated URLs. Configure Aiven TLS explicitly.
- Default pool size 1 / overflow 0 is conservative but still retains one idle connection per active process after use. Total capacity multiplies across workers and instances.
- Deployment manifests remain untouched by instruction. Existing URL-based secrets remain usable via the bridge; Render can migrate to separate `DB_*` variables once configured.
- **Still UNKNOWN:** Render startup observation when Aiven was disabled; no Render logs, deployment SHA, or actual Aiven schema query available. CI test proves the lifespan rejects a raised DB connectivity error, not the exact external Render event.
- Issue #180 has implementation and evidence comment ID `6341640313`. PR #178 remains closed/unmerged. PR #181 is now open against `dev`: https://github.com/NetHub-Ltd/NetPay/pull/181; it is not merged.


## PR #181 status and security gate — 2026-10-22

- PR #181 is open against `dev`; do not merge yet.
- Latest implementation/config/test tree commit: `4f0123e9ed1f4d8d2e6d67a9cb86462c261a2e75`. Live branch tip has advanced with tracker-only commits; query branch API for current SHA.
- CI #634 and PR CI #635 succeeded; backend tests 15 passed, 1 warning, no skipped migration-schema test. Backend readiness #188 and frontend lint/build #81 succeeded.
- GitGuardian Security Checks fails with six detections from earlier commits in the PR (sample/local CI/container/test values). Current tree was cleaned, but the scanner still scans prior commits. No history rewrite or dismissal was performed. Resolve with approved action before merge; do not imply actual production credentials were exposed without evidence.
- Render/Aiven DB-off observation remains unresolved; the exact Render deployment SHA/logs/effective endpoint are still unknown.


## User decision — preserve history / latest checks (2026-10-22)

- **VERIFIED (user decision):** Preserve Git history. Do not rebase, squash, force-push, rewrite commits, or dismiss GitGuardian findings to make PR #181 pass.
- PR #181 remains open and unmerged against `dev` until GitGuardian is reviewed through the existing security process and required checks pass.
- **Fresh workflow evidence for branch commit `b81c1ca77b8de12ebe29cae3c18f4ab9d0335a84`:** CI #643, backend readiness #197, frontend lint #90, and frontend build #89 all completed with success. The workflow-run API response does not include GitGuardian; its current check status is therefore **UNKNOWN** from this query and must be checked separately.
- **UNKNOWN:** Render deployment SHA/logs/effective DB endpoint and actual Aiven schema remain uninspected; no root cause claimed.
- Next safe action: inspect the exact six GitGuardian findings and determine whether any actual credential was exposed; preserve history and follow the repository's existing review/rotation process if warranted. Do not merge until the required security gate is resolved.


## New-chat handoff snapshot — 2026-10-22 21:05 UTC

### Canonical current task
- Issue #180: https://github.com/NetHub-Ltd/NetPay/issues/180
- PR #181: https://github.com/NetHub-Ltd/NetPay/pull/181
- Branch: `work/minimal-netpay-rebuild`; PR target `dev`; PR is open and unmerged.
- User's explicit decision: **preserve Git history**. No rebase/squash/force-push/reset/history rewrite; do not dismiss security findings without review.

### Implementation summary
- Split DB fields (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_SSL_MODE`) build asyncpg and psycopg URLs via SQLAlchemy URL utilities; temporary `DATABASE_URL` bridge remains for existing external environment injection.
- asyncpg URL uses `ssl`; psycopg URL uses `sslmode`. Pool defaults: size 1, overflow 0, timeout 10s, recycle 1800s, pre-ping and LIFO. This can still retain one idle connection per active engine/process.
- Alembic directory is `backend/alembic/`; migration IDs/content retained. Docker healthcheck uses readiness endpoint. Startup failure regression test added. Workflow/container env and both env examples updated.
- Deployment manifests/Flux untouched.

### Latest evidence (re-check before relying)
- CI #643, backend readiness #197, frontend lint #90, frontend build #89 passed at prior branch commit `b81c1ca77b8de12ebe29cae3c18f4ab9d0335a84`.
- Following tracker-only updates, run IDs seen queued at commit `d2d9eb371f4f6f9d8928fdf0dc22c8d814f169f2`: CI #651, readiness #205, frontend lint #98, frontend build #97. Re-query current branch tip and outcomes.
- GitGuardian previously failed with six findings from earlier PR commits. Its current state is not established by the workflow-run query. Review exact detections; preserve history and keep PR unmerged until required security check passes.
- Render/Aiven outage reproduction, deployed SHA/logs/effective endpoint, and actual Aiven schema: **UNKNOWN**. CI schema verification was against CI PostgreSQL; startup failure test uses a mocked exception.

### New-chat next steps
1. Read all four trackers, `AGENTS.md`, `docs/REBUILD_SPEC.md`, and refresh relevant skill from NetHub skills repo.
2. Fetch live branch tip, PR #181 status/checks, issue #180, and workflow outcomes.
3. Review GitGuardian findings with the history-preservation constraint. Do not claim findings are false positives without evidence.
4. Investigate Render only with deployment/log/config evidence; do not alter deployment manifests or DB.
5. Sync/re-fetch all trackers and issue/PR after new evidence.


## Live verification refresh — 2026-10-23

- PR #181 fetched live: state `open`, `merged=false`, base `dev`, head branch `work/minimal-netpay-rebuild`. Keep open and unmerged.
- Workflow runs associated with recorded commit `5efc356fc4a217f78a5d7851e53ed9f52f93869a`: CI #656 (success), backend readiness #210 (success), frontend lint #103 (success), frontend build #102 (success). Run IDs: `39854485306`, `39854485643`, `39854485487`, `39854485464`.
- PR discussion's currently visible GitGuardian bot comment lists three detections: two PostgreSQL Credentials detections on commit `385799452bc790f743c081fe561b0795acd31775`, file `backend/smoke_tests/test_database_foundation.py`, involving a reserved-character test password; and one Generic Password detection on commit `869ad9a1e47ea2cd6af9e45d2b97db99146e5994`, file `backend/scripts/container_startup_smoke.sh`, involving `DB_PASSWORD=netpay` in a test container invocation. These appear test-context values from the inspected lines, but incidents remain active; confirm full findings and current required-check status through GitGuardian. Prior tracker records say six detections, conflicting with this visible three-row comment.
- The combined commit-status endpoint returned no status entries; this is not proof that required checks passed. GitGuardian is not included in the Actions workflow-run list.
- Branch search confirmed `work/minimal-netpay-rebuild` exists but did not expose its SHA. `5efc356...` remains the latest recorded tracker commit, not a freshly confirmed branch head.
- CORE engineering skill refreshed from `NetHub-Ltd/skills-` current README and `CORE-AI-Product-Engineering-Skill-v1.0.0.md`; apply evidence-first verification, smallest reversible changes, security review, and Changed/Verified/Not verified/Risks/Rollback/Follow-ups reporting.
- Render/Aiven behavior remains unknown; no runtime metadata/logs/schema were inspected. No application or deployment changes made in this verification pass.


## Current work — M-Pesa Core issue #187 (2026-10-23)

- **Issue:** https://github.com/NetHub-Ltd/NetPay/issues/187
- **Approval:** user approved implementation and requested thorough testing of every supported use case.
- **Working branch:** `work/minimal-netpay-rebuild`; pre-change tip `8960d3c0d0911474e195f212e0bb68c6b474d860`; current `dev` tip observed as `72a9d108dde93c208a1330a87962bd9e47f4606e`. Both trees were `3e880884c27f2b5634f23666d8de7eef54c1e63f` at inspection time.
- **Existing PR state:** PR #181 is closed (its merge commit is present on `dev`); PR #182 is an open `dev` → `main` PR and is not part of this task. Create a new single PR from the existing working branch to `dev` after implementation.
- **Runtime constraint:** local `git clone` failed with `Could not resolve host: github.com`. Remote GitHub reads/writes are available. Do not claim local tests ran; use repository CI as the executable test environment and inspect the resulting runs.
- **Baseline observation:** `backend/app/main.py` has health endpoints and optional static export serving; existing models include `ProviderRequest`, `ProviderCallback`, `AuditLog`, `DarajaIntegration`, `Payment`, `PaymentAttempt`, `PaymentVerification`, and transactional outbox records. No `mpesa_core` package was present in the inspected tree.
- **API evidence:** official Safaricom portal lists Authorization, M-Pesa Express, C2B, B2C, Transaction Status, Account Balance, Reversals, Dynamic QR, Business Pay Bill/Buy Goods, B2B Express Checkout and Pull Transactions. Each capability's product/initiator/permission prerequisites must be represented; this inventory does not imply every merchant is entitled to every operation.
- **Next action:** update the spec/capability matrix and trackers, then implement on the existing branch; run CI and verify all outcomes before opening one PR to `dev`.


## Implementation verification update — 2026-10-23

- Target: NetPay PR #188, base dev, head work/minimal-netpay-rebuild.
- Final code commit: 18e3de35185f1219014ba183879835fd3740cefb. CI/backend readiness/frontend lint/frontend build/container startup smoke passed; backend suite reported 34 passed with one Starlette deprecation warning.
- Audit redaction, callback-type-scoped dedupe, explicit per-environment callback host, and API-coverage caveats are included and verified by the final CI run.
- No deployment configuration or public payment endpoint was added. dev/main have not been modified by this work.


## User-approved cleanup — remove rejected M-Pesa Core (2026-10-28)

- **User decision:** The current M-Pesa Core implementation is rejected as unnecessarily complex. Delete the existing Core package and its Core-only tests; do not implement a replacement in this change.
- **Issue:** [#213 — Remove rejected M-Pesa Core implementation](https://github.com/NetHub-Ltd/NetPay/issues/213).
- **Branch:** `chore/remove-rejected-mpesa-core`, created from the live `dev` ref. PR must target `dev`; do not merge.
- **Scope:** delete `backend/app/mpesa_core/`; remove its `main.py` router import/registration; remove tests that solely import/test the deleted package; update these trackers. Keep shared application models and historical Alembic revisions unless an explicit reference audit proves removal is necessary; never delete/alter applied migration history in this cleanup.
- **Out of scope:** replacement singleton/client, new APIs/services/routes/schemas, new migrations/dependencies, unrelated app behavior, frontend, deployment manifests, CI/GHCR workflow behavior, `dev`, and `main`.
- **Approval boundary:** the next task after this PR is merged is to discuss the replacement class architecture and API methods with the user before writing code.
- **Verification discipline:** inspect all references before deletion; report actual test runs and unverified behavior accurately. Preserve history; rollback through a reviewed revert commit.


## Cleanup implementation update — 2026-10-28

- **OBSERVED / changed on this topic branch:** removed the complete `backend/app/mpesa_core/` package (9 Python files), deleted `backend/smoke_tests/test_mpesa_core.py` and `backend/smoke_tests/test_mpesa_callbacks.py` because both directly test the rejected package, and removed the two Core callback-router wiring lines from `backend/app/main.py`.
- **Preserved deliberately:** application/domain models, historical Alembic revision `0003_mpesa_core_capabilities`, database schema history, frontend, settings, CI/GHCR workflows, deployment/Flux files, and all other application code. Historical migrations are not deleted or rewritten; schema cleanup would require separate data-impact review.
- **Architecture boundary:** no replacement class or new API has been written. Replacement design must be discussed with the user after this cleanup PR is reviewed and merged.
- **Verification so far:** GitHub read-back confirmed the Core files and `test_mpesa_core.py` are absent; callback test deletion and `main.py` update were acknowledged by GitHub write responses. Final read-back/reference audit and CI results remain pending.
- **Not verified yet:** test suite, import checks, frontend build, container smoke, or runtime behavior. Do not describe these as passing until evidence is retrieved.
- **Rollback:** reviewed revert commits only; do not reset/rewrite history. Reverting this PR restores the package and its route wiring. No DB migration or deployment change was made.


## PR handoff refresh — 2026-10-28

- **PR #214:** https://github.com/NetHub-Ltd/NetPay/pull/214 — open, targeting `dev`; **not merged**. Tracking issue #213 remains open.
- **Observed PR diff:** 16 paths: the 9-file Core package, its 2 Core-specific test files, `backend/app/main.py`, and the 4 trackers. No other paths appear in the PR changed-file list.
- **CI status at handoff refresh:** backend readiness run [40769097112](https://github.com/NetHub-Ltd/NetPay/actions/runs/40769097112), frontend build [40769096856](https://github.com/NetHub-Ltd/NetPay/actions/runs/40769096856), frontend lint [40769097051](https://github.com/NetHub-Ltd/NetPay/actions/runs/40769097051), and CI [40769097145](https://github.com/NetHub-Ltd/NetPay/actions/runs/40769097145) were still in progress. No test outcome is claimed yet.
- **Verified by read-back:** `backend/app/main.py` no longer imports or registers the Core callback router; all 9 `backend/app/mpesa_core/` files and both Core-specific test files are listed as deletions in PR #214.
- **Not verified:** repository-wide runtime reference audit and final CI conclusions. The GitHub code-search connector indexes the default branch rather than this topic branch, so it is not evidence of a complete topic-branch reference scan.
- **Next safe action:** retrieve the workflow conclusions and review any failures; do not merge. Replacement-class design remains a separate post-merge discussion requiring the user's approval before code is written.


## Approved mpesa_core implementation — live handoff (2026-10-29)

- **OBSERVED:** live dev points to 82bae5b7c8e1704491b0aa8eec1dfa8fa948364f; its merge commit records PR #214 removing the rejected Core implementation.
- **OBSERVED:** branch feat/mpesa-core-complete was created from that exact dev SHA. Specification commit: 09e94644e6144ca8f2ef7e397dde77131c3ae5b4.
- **Issue:** #187 updated for the newly approved full-scope implementation: https://github.com/NetHub-Ltd/NetPay/issues/187.
- **Specification:** docs/MPESA_CORE_SPEC.md on feat/mpesa-core-complete.
- **Fresh skill:** refreshed CORE-AI-Product-Engineering-Skill-v1.0.0.md from https://github.com/NetHub-Ltd/skills-.git. Applied inspect-before-change, evidence labels, proposal/impact/test/rollback discipline, simplest-correct architecture and no unsupported implementation claims.
- **Important instruction reconciliation:** older AGENTS.md says work only on work/minimal-netpay-rebuild and forbids new branches, but the current user-approved task and later tracker workflow explicitly require a topic branch from dev and one PR targeting dev. For this task, use feat/mpesa-core-complete only; do not touch work/minimal-netpay-rebuild, dev or main directly.
- **Existing models observed:** DarajaIntegration stores integration metadata and encrypted credential material; ProviderRequest supports operation/correlation/idempotency and safe request/response metadata; PaymentVerification and reconciliation records exist. Inspect their current consumers before deciding whether any schema change is required. Do not duplicate these models or edit historical migration revisions.
- **Initial status at branch creation:** docs/spec and issue/tracker coordination only; superseded by the Implementation progress snapshot below.
- **Next action:** validate provisional Bill Manager, Ratiba, B2B Express Checkout, Lipa na Bonga and Pull Transactions contracts against authenticated Safaricom documentation or sandbox. Keep these capabilities production-gated until verified; rerun checks after the tracker/spec-only status commit.


## Implementation progress snapshot (2026-10-29)

- Added docs/MPESA_CORE_SPEC.md and backend/app/mpesa_core/{__init__.py,client.py,schemas.py,validation.py,errors.py,callbacks.py}; added backend/smoke_tests/test_mpesa_core.py.
- Updated backend/app/main.py to create one MpesaCore per FastAPI lifespan and close it during shutdown.
- Core uses existing httpx, Pydantic, Loguru and cryptography dependencies; no new dependency, migration, deployment manifest, Flux or GHCR workflow change.
- API adapters are implemented for documented common Daraja APIs and the proposed product families, including Tax Remittance, Pull Transactions, B2B Express Checkout, Ratiba, Lipa na Bonga and Bill Manager operations. Unverified/ambiguous product payloads must remain flagged for sandbox validation, not advertised as production-verified.
- CI run `40780804974` passed on code head `8fb5a3ba1004af8ff240ed13cc2cd07ab283b1d3`: backend smoke tests, migration, PostgreSQL/Redis, image build and container startup smoke. Backend readiness, frontend lint and frontend build passed on the same head. Tracker/spec-only commits follow the tested code head; verify current branch-tip checks before review.

## Approved #217 implementation — current branch state (2026-10-29 UTC)

- Contract approval recorded in [issue #217](https://github.com/NetHub-Ltd/NetPay/issues/217).
- Working branch `feat/mpesa-application-flow-217` was created from `dev` SHA `3d77327c1d00f713b7ec088492dc91dd953d139c`.
- Added application API modules under `backend/app/payments/`, Core credential encryption in `backend/app/mpesa_core/credentials.py`, Core OAuth validation method, M2M signing setting, one-time provisioning script, API contract documentation, and PostgreSQL-backed application integration tests.
- Main API is registered through `backend/app/main.py`; existing model fields and Alembic revisions were reused. No historical migration was edited and no new migration is currently planned.
- **Not yet verified:** Python import/typing/runtime correctness, DB integration test behavior, migration checks on branch tip, all CI workflows, live Daraja sandbox interoperability, callback acknowledgement contract, and C2B provider registration. CI is the next evidence gate.
- Current work is application runtime code and tests, unlike the earlier audit-only branch. Flux/deployment manifests and GHCR build/push behavior have not been intentionally changed.
- Issue #216 remains a verification-only gate after #217's reviewed merge to `dev`.
## #217 verification checkpoint — 2026-10-29 UTC

- Draft PR [#218](https://github.com/NetHub-Ltd/NetPay/pull/218) is open against `dev`; it has not been merged and remains under review.
- **Observed CI failure and fix:** run [40787891591](https://github.com/NetHub-Ltd/NetPay/actions/runs/40787891591) failed because the test expected one STK callback row while the implementation correctly retained both the processed callback and a mismatched/rejected callback. The assertion was corrected to verify one `processed` and one `rejected` record.
- **Observed backend test success:** run [40788087483](https://github.com/NetHub-Ltd/NetPay/actions/runs/40788087483) completed backend migration, test, PostgreSQL and Redis steps successfully; its log reported **65 passed, 1 warning**. Its container image/startup job was still in progress at observation time, so it was not yet a complete workflow success.
- A PostgreSQL commit-failure rollback test has since been added for callback/payment/outbox atomicity. Latest code also validates production callback URL HTTPS and selects the STK transaction type from integration product type.
- **Current-head status:** CI, backend readiness, frontend lint and frontend build have been triggered for the newer head and were still in progress at last observation. Do not mark the PR ready until the exact latest-head checks finish successfully.
- No live Daraja sandbox transaction has been performed. Fake-Core tests prove application behavior only, not provider interoperability.
- #216 remains a separate verification-only readiness gate after #217's reviewed merge to `dev`.



## #217 current repository state — 2026-10-29 00:15 UTC

- Working branch: `feat/mpesa-application-flow-217`; PR [#218](https://github.com/NetHub-Ltd/NetPay/pull/218) targets `dev`, is draft/open, and is unmerged.
- Latest code fix commit: `52414c1ee33c030cb08a1810ce3579e496ea105e`. The fix imports `ProviderRequest` alongside `AuditLog` in `backend/app/payments/service.py`; the STK service used `ProviderRequest` without importing it, causing the 500 observed in CI run [40789386571](https://github.com/NetHub-Ltd/NetPay/actions/runs/40789386571).
- The duplicate-key database log referenced `merchant-payment-key-1`, whereas the failed request used `flow-key-1`; do not conflate them. The missing Python import is the source-confirmed cause.
- Fixed-head workflows were queued at last observation: CI [40792832066](https://github.com/NetHub-Ltd/NetPay/actions/runs/40792832066), readiness [40792832026](https://github.com/NetHub-Ltd/NetPay/actions/runs/40792832026), frontend lint [40792832015](https://github.com/NetHub-Ltd/NetPay/actions/runs/40792832015), frontend build [40792832019](https://github.com/NetHub-Ltd/NetPay/actions/runs/40792832019). These are pending evidence, not passes.
- Preserve Git history. Do not change `dev`, `main`, Flux/deployment manifests, or GHCR build/push behavior. No live Daraja transaction was run. Issue #216 remains blocked until #217 is reviewed and merged to `dev`.


## #217 latest CI follow-up — 2026-10-29 00:17 UTC

- CI [40792832066](https://github.com/NetHub-Ltd/NetPay/actions/runs/40792832066) still failed after the missing `ProviderRequest` import fix, now at duplicate C2B validation replay (`backend/smoke_tests/test_payment_application.py:446`): the replay response was HTTP 500.
- Handler source showed the duplicate recovery path rolled back and then accessed `integration.id`. Commit `3237a9a6e9298ae9f7f383f09b3a3f5b19b52802` captures the UUID before rollback and uses the scalar key in recovery. This follow-up is not yet test-verified.
- PR #218 remains draft/open/unmerged against `dev`. Preserve history and leave #216 blocked until #217 is reviewed and merged.


## #217 latest verified CI evidence — 2026-10-29 00:18 UTC

- Code commit `3237a9a6e9298ae9f7f383f09b3a3f5b19b52802` is verified by CI [40792997496](https://github.com/NetHub-Ltd/NetPay/actions/runs/40792997496): Alembic upgrade to revision `0003_mpesa_core_capabilities`, **65 passed, 1 warning**, PostgreSQL and Redis connectivity all passed.
- Backend readiness [40792997409](https://github.com/NetHub-Ltd/NetPay/actions/runs/40792997409), frontend lint [40792997425](https://github.com/NetHub-Ltd/NetPay/actions/runs/40792997425), and frontend build [40792997517](https://github.com/NetHub-Ltd/NetPay/actions/runs/40792997517) passed for the same code commit.
- The CI container job remains queued, so the full CI/image startup gate is not yet green. PR #218 remains draft/open/unmerged. Later tracker-only commits do not change application code; use live PR SHA for handoff state.


## Parallel branch — marketing conversion theme experiment (2026-10-29)

- **Branch:** `feat/theme-test-marketing-conversion`, created from live `dev` after explicit user approval to override the older branch-only rule for this isolated experiment. PR must target `dev`; no direct writes to `dev` or `main`.
- **Scope:** noindex `/theme-test` visual comparison of two Design 1 + Design 2 marketing directions. Existing Ledger theme remains product default.
- **Design constraints:** preserve current product truth; use existing documented capabilities only; no invented testimonials, customer metrics, uptime, certification, fees, or unsupported payment methods. Keep prototype off sitemap and disallowed in robots.
- **Verification:** implementation, lint/typecheck/build and browser QA are pending until evidenced. The active payment-flow task and PR #218 remain separate; do not overwrite their status with this experiment.
- **Rollback:** reviewed revert of route/CSS/robots changes; no schema/data or deployment changes.
