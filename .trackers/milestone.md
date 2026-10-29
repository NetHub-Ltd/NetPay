# NetPay rebuild milestones

**Last updated:** 2026-10-29  
**Branch:** `feat/mpesa-core-complete` (PR #215 to `dev`)  
**Current specification:** [`docs/MPESA_CORE_SPEC.md`](../docs/MPESA_CORE_SPEC.md); historical rebuild spec: [`docs/REBUILD_SPEC.md`](../docs/REBUILD_SPEC.md)  
**Status principle:** Do not mark a milestone complete without evidence.

## Milestone R0 — Tracking and repository baseline

| ID | Acceptance criterion | Status |
|---|---|---|
| R0.1 | Rebuild-specific trackers exist on the working branch | VERIFIED — created 2026-10-22 |
| R0.2 | Working/integration branch relationship is recorded | VERIFIED — PR #188 targets `dev`; current working branch remains separate and no history rewrite was performed |
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
| R1.4 | Verify frontend and backend `.env.example` files | VERIFIED — frontend example inspected; backend example includes M-Pesa settings and leaves public callback origin explicit per environment |
| R1.5 | Verify no deployment-manifest changes were introduced | VERIFIED — branch diff contains no deployment manifests or Flux resources |
| R1.6 | Review branch diff for unintended legacy code or unrelated changes | VERIFIED — reviewed changed-file list; changes are Core code, migration, tests, docs and trackers |

## Milestone R2 — Application behavior

| ID | Acceptance criterion | Status |
|---|---|---|
| R2.1 | Implementation conforms to `docs/REBUILD_SPEC.md` | PARTIAL — Core boundary implemented; Pull Transactions remains provisional and B2B Express Checkout is an explicit gap; live sandbox verification is pending |
| R2.2 | Backend tests and readiness checks pass | VERIFIED — final code commit 18e3de35185f1219014ba183879835fd3740cefb: 34 tests passed; readiness passed |
| R2.3 | Frontend lint/typecheck and build pass | VERIFIED — frontend lint and build workflows passed on commit 18e3de35185f1219014ba183879835fd3740cefb |
| R2.4 | Container smoke test confirms FastAPI serves frontend and API routes correctly | VERIFIED IN CI — container startup smoke passed on commit 18e3de35185f1219014ba183879835fd3740cefb |
| R2.5 | Payment security, idempotency, callback trust, and financial-state rules match the spec | PARTIAL — targeted credential, audit, idempotency and callback tests pass; live provider verification and payment-domain integration remain outstanding |

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


## M-Pesa Core — issue #187 (2026-10-23)

| ID | Acceptance criterion | Status |
|---|---|---|
| MP.1 | Current branch/baseline and existing models/migrations inspected | VERIFIED — remote GitHub reads; local clone blocked by unavailable DNS/network |
| MP.2 | Implementation issue created before tracker/code changes | VERIFIED — [issue #187](https://github.com/NetHub-Ltd/NetPay/issues/187) |
| MP.3 | Current official Daraja API inventory documented with capability/prerequisite classification | PARTIAL — inventory/prerequisites documented; Pull Transactions contract remains provisional and B2B Express Checkout schema is inaccessible in the public listing |
| MP.4 | Credential encryption and resolution; OAuth lifecycle/cache | VERIFIED IN CI — encryption/key rotation, certificate-based security credential and OAuth cache behavior tested; live OAuth not run |
| MP.5 | Shared typed HTTP transport, safe errors, timeouts, correlation | VERIFIED IN CI — provider response, timeout, connect-error and unknown-outcome tests pass; no automatic retries for ambiguous operations |
| MP.6 | Durable provider-operation audit and redacted structured logging | VERIFIED IN CI — durable audit persistence/redaction and structured operation logging implemented and tested |
| MP.7 | STK/C2B callbacks normalized, correlated, deduplicated, safe under reordering | VERIFIED IN CI WITH LIMITS — callback evidence, dedupe and conflict audit tested; C2B validation is basic shortcode/amount gating, and cryptographic callback signatures are not assumed |
| MP.8 | Other relevant API adapters have typed contracts and capability gates | PARTIAL — STK/query, C2B, Dynamic QR, status, balance, reversal, B2C/B2B implemented; Pull Transactions provisional, B2B Express Checkout not implemented |
| MP.9 | Unit, contract, integration, concurrency and security regression tests | VERIFIED IN CI — 34 tests passed, including operation adapters, callback persistence/dedupe, credential security and concurrent idempotency |
| MP.10 | CI/migrations/container/frontend checks re-run on final branch tip | VERIFIED — CI, readiness, frontend lint/build and container startup smoke all passed on 18e3de35185f1219014ba183879835fd3740cefb |

Gate: do not mark any item VERIFIED without a concrete test, source, or workflow result. Daraja APIs requiring initiator/security credentials or product permissions must be disabled unless those requirements are configured.


## Implementation verification update — 2026-10-23

- Core implementation is on the existing work branch and draft PR #188.
- Final code commit 18e3de35185f1219014ba183879835fd3740cefb passed: backend tests (34 passed, 1 Starlette deprecation warning), backend readiness, frontend lint/build, and container startup smoke.
- Audit metadata masks PartyA/PartyB identifiers; callback fingerprints are scoped by callback type; callback host is explicit per environment.
- Live Daraja sandbox tests have not been performed. Pull Transactions remains provisional/disabled until its exact contract is verified. B2B Express Checkout is not implemented because the accessible official portal listing does not expose the request schema/endpoint.
- No public payment-initiation API, separate service, deployment manifest, Flux resource, production database, or main-branch change is included.


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


## M-Pesa Core complete API scope — approved 2026-10-29

### M0 — Contract verification and implementation (in progress)
- [x] Product owner approved complete proposed mpesa_core API inventory and exhaustive testing.
- [x] Refresh current CORE engineering skill and record current dev baseline.
- [x] Update issue #187 and add docs/MPESA_CORE_SPEC.md on feat/mpesa-core-complete.
- [ ] Verify endpoint/version, request/response fields, permissions, callback schema and retry behavior for every operation against current official docs.
- [x] Freeze and document capability/permission gates; sandbox-only C2B simulation; opt-in C2B registration.
- [x] Implement shared schemas, validation, typed errors, OAuth cache/concurrency and HTTP lifecycle.
- [x] Implement all proposed API adapters with per-operation success/rejection/malformed/transport/ambiguous/security tests; provisional product contracts remain production-gated.
- [x] Implement callback parsers/normalizers without moving application route/state ownership into Core.
- [x] Run backend, migration, CI, frontend, image and container checks on code head `8fb5a3ba1004af8ff240ed13cc2cd07ab283b1d3` (CI run `40780804974` passed); the branch contains tracker/spec-only commits after this tested code head; current branch-tip checks are pending.
- [x] Re-fetch and reconcile trackers/issue; open one draft PR targeting dev (#215); do not merge without user approval.

**Acceptance note:** all proposed API families must have an implemented and tested contract. If official documentation proves a proposed product name is retired, unavailable or not a distinct endpoint, record the evidence and implement the documented equivalent only when one exists; never invent an endpoint to satisfy a label.


### M0 progress snapshot (2026-10-29)
- [x] Create the approved topic branch and write the implementation specification.
- [x] Add Core package foundation, typed operation schemas, validation, errors, OAuth/HTTP transport and app lifespan.
- [x] Add callback parsing, safe response redaction and RSA initiator-credential encryption.
- [x] Add mocked tests across operation payloads and shared failure/security paths.
- [x] Confirm CI is green on code head `8fb5a3ba1004af8ff240ed13cc2cd07ab283b1d3` (run `40780804974`); rerun after the tracker reconciliation commit.
- [ ] Validate provisional API contracts (especially Bill Manager, Ratiba, B2B Express Checkout, Lipa na Bonga and Pull Transactions) against authenticated official docs/sandbox.
- [x] Finalize documentation and tracker read-back; maintain one PR targeting dev (#215).

## #217 approved implementation progress — 2026-10-29 UTC

- [x] Product owner approved implementation contract.
- [x] Created topic branch `feat/mpesa-application-flow-217` from `dev`.
- [x] Added M2M token signing and scope checks, credential hashing/provisioning, Core-owned credential encryption, OAuth onboarding, STK request persistence/idempotency, status read, STK callback handling and transactional outbox event, and gated opt-in C2B handlers.
- [x] Added API documentation and application-level PostgreSQL integration tests.
- [ ] Review generated source and run/observe current branch CI.
- [ ] Add and verify failure-path coverage for ambiguous provider outcomes, invalid/mismatched callbacks, database rollback, and scope narrowing.
- [ ] Verify Alembic upgrade from current head and no historical migration changes.
- [ ] Open/maintain reviewable PR targeting `dev`; all checks must pass before ready-for-review.
- [ ] User reviews PR; no autonomous merge.
- [ ] Only after approved merge, execute #216 exhaustive test matrix and decide controlled test-environment readiness.

**Evidence discipline:** code being written is not evidence that behavior works. Current branch tests/CI are not yet verified.
## #217 verification checkpoint — 2026-10-29 UTC

- Draft PR [#218](https://github.com/NetHub-Ltd/NetPay/pull/218) is open against `dev`; it has not been merged and remains under review.
- **Observed CI failure and fix:** run [40787891591](https://github.com/NetHub-Ltd/NetPay/actions/runs/40787891591) failed because the test expected one STK callback row while the implementation correctly retained both the processed callback and a mismatched/rejected callback. The assertion was corrected to verify one `processed` and one `rejected` record.
- **Observed backend test success:** run [40788087483](https://github.com/NetHub-Ltd/NetPay/actions/runs/40788087483) completed backend migration, test, PostgreSQL and Redis steps successfully; its log reported **65 passed, 1 warning**. Its container image/startup job was still in progress at observation time, so it was not yet a complete workflow success.
- A PostgreSQL commit-failure rollback test has since been added for callback/payment/outbox atomicity. Latest code also validates production callback URL HTTPS and selects the STK transaction type from integration product type.
- **Current-head status:** CI, backend readiness, frontend lint and frontend build have been triggered for the newer head and were still in progress at last observation. Do not mark the PR ready until the exact latest-head checks finish successfully.
- No live Daraja sandbox transaction has been performed. Fake-Core tests prove application behavior only, not provider interoperability.
- #216 remains a separate verification-only readiness gate after #217's reviewed merge to `dev`.



## #217 failure diagnosis and follow-up — 2026-10-29 00:15 UTC

- [x] Inspect the latest failed CI output and locate the failing application-level test: [CI run 40789386571](https://github.com/NetHub-Ltd/NetPay/actions/runs/40789386571), STK initiation assertion in `test_payment_application.py:254` (HTTP 500 instead of 202).
- [x] Trace the failure to a source-level cause: `PaymentApplicationService.initiate_stk` referenced `ProviderRequest` but `backend/app/payments/service.py` did not import it.
- [x] Commit minimal fix `52414c1ee33c030cb08a1810ce3579e496ea105e` adding the missing import; no schema, migration, deployment or release-workflow changes.
- [ ] Verify fixed-head CI [40792832066](https://github.com/NetHub-Ltd/NetPay/actions/runs/40792832066), readiness [40792832026](https://github.com/NetHub-Ltd/NetPay/actions/runs/40792832026), frontend lint [40792832015](https://github.com/NetHub-Ltd/NetPay/actions/runs/40792832015), and frontend build [40792832019](https://github.com/NetHub-Ltd/NetPay/actions/runs/40792832019); these were queued at last observation.
- [ ] Review the complete PR diff, callback acknowledgement and C2B provider contracts, and migration compatibility before marking ready.
- [ ] Obtain user review; do not merge autonomously. Execute issue #216 only after #217 is reviewed and merged to `dev`.

**Evidence distinction:** the import fix is committed; its test verification is pending. The earlier PostgreSQL duplicate-key log mentioned a different idempotency key and is not attributed to this failure.


## #217 C2B replay recovery follow-up — 2026-10-29 00:17 UTC

- [x] Re-check CI after the import fix: run [40792832066](https://github.com/NetHub-Ltd/NetPay/actions/runs/40792832066) progressed beyond STK initiation but failed at duplicate C2B validation replay, test line 446.
- [x] Trace the failure to rollback-expired ORM state being accessed in duplicate recovery; commit `3237a9a6e9298ae9f7f383f09b3a3f5b19b52802` captures the integration UUID before rollback.
- [ ] Verify CI, backend readiness, frontend lint/build, migration and container smoke on the updated code. No green result has yet been observed for this fix.
- [ ] Keep PR #218 draft/unmerged until all gates pass and the user reviews it; #216 remains deferred.


## #217 verification result — 2026-10-29 00:18 UTC

- [x] Latest code commit `3237a9a6e9298ae9f7f383f09b3a3f5b19b52802`: CI [40792997496](https://github.com/NetHub-Ltd/NetPay/actions/runs/40792997496) passed migration upgrade through `0003_mpesa_core_capabilities`, **65 tests passed, 1 warning**, PostgreSQL/Redis connectivity.
- [x] Backend readiness [40792997409], frontend lint [40792997425], and frontend build [40792997517] passed.
- [ ] Wait for CI container image/startup job; run [40792997496] is not complete yet.
- [ ] Review full PR diff/provider contracts and await user review. PR #218 stays draft/unmerged; #216 remains deferred until #217 is reviewed and merged.


## Parallel milestone — marketing conversion theme experiment

| ID | Acceptance criterion | Status |
|---|---|---|
| MT.1 | Isolated feature branch created from live `dev` after user approval | VERIFIED — branch `feat/theme-test-marketing-conversion` created |
| MT.2 | Two distinct Design 1 + 2 landing-page directions are available at `/theme-test` | IN PROGRESS |
| MT.3 | Claims and CTAs reflect existing NetPay capabilities and routes | PENDING REVIEW |
| MT.4 | Route is noindex/nofollow, excluded from sitemap and disallowed in robots | PENDING |
| MT.5 | Frontend lint, typecheck and production build pass on the final branch head | PENDING — not run here yet |
| MT.6 | Rendered responsive/browser QA completed | PENDING — do not claim verified without browser evidence |
| MT.7 | PR targets `dev`, remains unmerged pending user review | PENDING |


### Theme-test milestone update — 2026-10-29 00:58 UTC

| ID | Acceptance criterion | Status |
|---|---|---|
| MT.1 | Isolated feature branch created from live `dev` after user approval | VERIFIED |
| MT.2 | Two distinct Design 1 + 2 landing-page directions are available at `/theme-test` | IMPLEMENTED — source present; browser rendering not yet verified |
| MT.3 | Claims and CTAs reflect existing NetPay capabilities and routes | SOURCE REVIEWED — visual copy avoids live-data claims; final review pending |
| MT.4 | Route is noindex/nofollow, excluded from sitemap and disallowed in robots | VERIFIED by source inspection |
| MT.5 | Frontend lint, typecheck and production build pass on final branch head | PENDING — earlier lint/build failed; fixes committed; latest checks queued |
| MT.6 | Rendered responsive/browser QA completed | NOT VERIFIED — no browser capture performed |
| MT.7 | PR targets `dev`, remains unmerged pending user review | VERIFIED — draft PR #219 |


### Final source correction — 2026-10-29 01:00 UTC

- Latest source commit: `191e51f58b87267eb591a228d4251e09a204f289`. Fixed the last JSX apostrophe found by lint in the prior run.
- Fresh latest-head checks: frontend lint #575 and backend readiness #682 were in progress; frontend build #574 and CI #1128 were queued at last observation. Results are pending.
- Earlier lint/build failures belong to prior commits and must not be treated as latest-head results. No successful latest-head result is claimed yet.
- Browser-rendered QA remains not performed. PR #219 remains draft/open/unmerged against `dev`.
