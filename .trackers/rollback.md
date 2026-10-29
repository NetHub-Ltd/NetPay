# NetPay rebuild rollback notes

**Last updated:** 2026-10-29

## Current change

This task adds the `mpesa_core` package, typed schemas, adapters and tests on `feat/mpesa-core-complete`, plus the FastAPI lifespan client lifecycle. No database schema migration, deployment manifest, Flux or GHCR push workflow change was made. PR #215 targets `dev` and remains unmerged.

## Recovery approach

- Before any future application change, record the exact pre-change working-branch commit in `.trackers/repo-state.md`.
- Prefer a reviewed revert commit for committed changes; do not reset or rewrite shared branch history without explicit approval.
- If a tracker-only update is wrong, correct it with a follow-up commit and preserve the history of the correction.
- Do not roll back or modify `main`, `dev`, Flux resources, or deployed resources as part of tracker repair.

## Known references

- Previous working baseline before tracker creation: `5bcbf865837cedc258e6a11d483b12a28f7f2ccc`.
- `dev` was observed at the same SHA as the working branch at the last branch inspection.
- `main` was observed at `a55500c2838b8ad1cc637a121f2b30f7f88132d0` and must remain untouched by this task.

## Handoff continuity

- The tracker handoff protocol is now documented in `.trackers/task.md` and `.trackers/repo-state.md`; milestone R0.5 records that documentation as verified.
- Independent resumability remains open under milestone R0.6. Do not treat the existence of instructions as proof that a fresh agent can resume correctly.
- Issue #179 contains a dated handoff note and canonical tracker links. Live branch refs remain authoritative over older branch-tip statements.

## Data and migrations

- No database migrations or data changes are part of tracker creation.

## Risks / unknowns

- This file is not a substitute for validating runtime rollback behavior of the rebuilt application.
- Exact rollback procedures for application images and release tags remain to be verified against the current release workflow and Flux configuration. Flux manifests are deliberately out of scope.


## Issue #180 rollback boundaries (2026-10-22)

- Issue: https://github.com/NetHub-Ltd/NetPay/issues/180
- Before implementation, record the current working branch tip and verify `dev` and `main` are unchanged.
- Settings and pool changes should be reverted through reviewed commits; do not reset or rewrite branch history.
- Moving `backend/migrations/` to `backend/alembic/` must preserve each migration file's contents and revision IDs. If Alembic cannot locate revisions after the move, revert the path/config reference changes together.
- No database reset, table drop, destructive migration, secret exposure, deployment manifest edit, or production database action is authorized.
- Render/Aiven runtime verification may require user-visible deployment logs/metadata. Do not change the database or claim the startup bug fixed solely from source inspection.
- If separate connection fields replace `DATABASE_URL`, document the required Render environment-variable update; do not silently assume Render has those variables configured. Keep the env example and code changes consistent.


## Implementation rollback/evidence update — 2026-10-22

- Implemented changes are on `work/minimal-netpay-rebuild`, application-code commit `90951334628987c10cb77fb6f06f80bdedf9fe1f`; tracker-only commits have since advanced the branch. `dev` and `main` were rechecked and unchanged.
- CI #615 passed (15 passed, 1 warning), including Alembic migration and container smoke; backend readiness #169 and frontend lint/build #61 passed.
- Revert the settings/pool/Docker/test/workflow changes via reviewed commits if needed. Revert the Alembic directory/config/image-copy changes together so migrations remain discoverable as one unit.
- The compatibility bridge is temporary; removing it requires coordinated updates to external Render variables and deployment-owned secrets/manifests. Do not edit those manifests here.
- No database reset, schema drop, production DB action, Flux resource edit, branch reset, or history rewrite occurred.
- Actual Render/Aiven DB-off startup and Render schema remain unverified; do not treat CI's mocked failure test or CI PostgreSQL schema as production evidence.


## PR/security state — 2026-10-22

- PR #181 is open against `dev`, not merged.
- Latest implementation/config/test tree commit `4f0123e9ed1f4d8d2e6d67a9cb86462c261a2e75` passed CI #634/#635, readiness #188 and frontend lint/build #81.
- GitGuardian still fails because earlier commits contain six detected local/test placeholder values. Current tree occurrences were removed. Do not rewrite history or dismiss findings without approval; do not merge while the required security check fails.
- No Render/Aiven outage reproduction has been obtained. Do not roll back or alter the user's database as part of diagnosis.


## GitGuardian resolution boundary — 2026-10-22

- User explicitly chose to preserve Git history for PR #181. Do not rewrite commits, rebase, squash, force-push, or reset the branch to remove scanner findings.
- Keep PR #181 open/unmerged until the findings are reviewed and the required security check passes. Any real credential exposure should be handled through the appropriate secret rotation/remediation process without rewriting history.
- No production database, deployment manifest, `dev`, or `main` changes are authorized by this decision.


## New-chat handoff / rollback boundaries — 2026-10-22 21:05 UTC

- User explicitly decided to **preserve Git history** for PR #181. Do not rewrite history, rebase, squash, force-push, reset, or use those actions to clear GitGuardian detections.
- PR #181 remains open/unmerged against `dev`. Review the exact GitGuardian findings and resolve via the existing security process. If an actual credential exposure is confirmed, rotate/revoke it as appropriate; current context does not establish that any production credential was exposed.
- No rollback or change to `dev`, `main`, Flux/deployment manifests, deployed resources, or production DB is authorized by this decision.
- Last known green runs on prior tip `b81c1ca77b8de12ebe29cae3c18f4ab9d0335a84`: CI #643, readiness #197, frontend lint #90, frontend build #89. Subsequent queued runs at commit `d2d9eb371f4f6f9d8928fdf0dc22c8d814f169f2`: CI #651, readiness #205, frontend lint #98, frontend build #97; verify before relying on them.
- Render/Aiven DB-off behavior remains unverified. Do not use a database reset, destructive migration, or deployment-manifest change for diagnosis.
- If application changes need reverting, use reviewed revert commits; keep Alembic path/config/image-copy changes together. Preserve branch history.


## Live verification refresh — 2026-10-23

- No application, database, deployment manifest, Flux resource, `dev`, or `main` changes were made in this verification pass.
- PR #181 remains open and unmerged. Preserve history; no reset, rebase, squash, force-push, or commit rewriting.
- CI #656, readiness #210, frontend lint #103, and frontend build #102 passed for recorded commit `5efc356fc4a217f78a5d7851e53ed9f52f93869a`.
- GitGuardian bot comment currently lists three detections in prior commits: two test URL credential-pattern detections and one smoke-test password literal. Inspect full incidents and verify current check conclusion before choosing a resolution. Do not dismiss findings, rewrite history, or assert production credential exposure without evidence. Earlier tracker wording says six detections; reconcile count.
- Render/Aiven startup and actual schema remain unverified. Do not change DB settings in deployment or touch manifests without authorization.
- Next safe action is evidence gathering only: confirm live branch head SHA, fetch PR required checks / GitGuardian check result and full incident context, then update issue and trackers. If a real credential is established, follow approved rotation/revocation procedures while preserving Git history.


## M-Pesa Core implementation rollback boundary — issue #187 (2026-10-23)

- Pre-change working-branch tip: `8960d3c0d0911474e195f212e0bb68c6b474d860`; preserve history and use reviewed revert commits.
- Add only new Alembic revisions; never edit applied migrations or reset/replace the database.
- No production credentials, production transactions, database writes, deployment manifests, Flux resources, `dev`, or `main` changes are authorized by this implementation task.
- Revert Core application files, configuration, tests, documentation and the corresponding migration together if rollback is required. Do not remove schema objects with live data without a separately reviewed migration.
- A passing GitHub CI run validates the tested commit in CI, not Render/Aiven production behavior. Local tests cannot be run from this environment unless repository access/network becomes available.


## Rollback and recovery notes — M-Pesa Core

- Current implementation is isolated to PR #188 on work/minimal-netpay-rebuild; it has not been merged or deployed.
- Revision 0003 is additive. Downgrade to 0002_full_domain_schema removes the M-Pesa credential/capability columns and provider-operation idempotency columns/constraint. Do not downgrade a database containing live M-Pesa operation history without first preserving the affected audit records.
- Code rollback should use a reviewed revert of the PR/commit; do not reset or rewrite branch history.
- No Flux manifests, deployment resources, production database, production credentials, or main branch were changed.
- Final code commit 18e3de35185f1219014ba183879835fd3740cefb passed CI: 34 backend tests, readiness, frontend lint/build, and container startup smoke. The PR remains unmerged and undeployed.
- Live Daraja sandbox verification and production rollout remain explicitly out of scope until separately approved.


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


## mpesa_core complete implementation — rollback boundary (2026-10-29)

- Pre-change base: dev SHA 82bae5b7c8e1704491b0aa8eec1dfa8fa948364f. Topic branch: feat/mpesa-core-complete. Initial spec commit: 09e94644e6144ca8f2ef7e397dde77131c3ae5b4.
- Existing Core package was removed by merged PR #214; do not cherry-pick or restore its deleted files. This is a fresh design and implementation.
- Roll back code through a reviewed revert commit on the topic branch. Preserve Git history; never reset, rebase, squash, force-push or rewrite commits.
- Do not modify dev/main, deployment manifests, Flux resources or GHCR build/push behavior. Do not use production credentials or initiate real financial transactions.
- Reuse existing integration/provider-operation/verification/reconciliation models where justified. If a schema change is necessary, add a new Alembic revision; do not edit applied historical migrations. Review downgrade impact before removing any columns/tables or records.
- Initial snapshot was documentation-only; see the implementation progress sections above for current code and test evidence.
- Ambiguous provider outcomes must remain unresolved; rollback must not turn them into failed/succeeded payments or trigger automatic duplicate requests.


## Implementation changes after initial specification

- Added new Core package files and one test module; updated backend/app/main.py only for app-scoped client lifecycle. No DB schema or migration change was made.
- Revert these changes through reviewed revert commits on feat/mpesa-core-complete only. Do not restore the removed pre-PR-214 Core implementation.
- CI run `40780804974` passed on code head `8fb5a3ba1004af8ff240ed13cc2cd07ab283b1d3`: backend tests, migration, PostgreSQL/Redis, image build and container startup smoke. Backend readiness and frontend lint/build also passed. The branch now contains tracker/spec-only commits after the tested code head; rerun checks on the current branch tip before review. No runtime rollback is indicated by current checks.
- Provisional product payload contracts are not to be treated as production-ready until validated. Disable capability use rather than sending guessed/incorrect payloads if contract validation finds a mismatch.

## #217 implementation rollback and safety checkpoint — 2026-10-29 UTC

- Product owner approved the contract; implementation is isolated on `feat/mpesa-application-flow-217`.
- No production credentials, production DB operations, live financial transactions, Flux/deployment manifest changes, or GHCR build/push behavior changes were made.
- No schema fields were intentionally added and no historical migration was edited. Verify the existing schema is sufficient in CI before relying on that assumption.
- If the PR is rejected, use a reviewed revert commit or close the branch/PR; do not reset, rebase, squash, or force-push history.
- Core OAuth onboarding is a provider call; payment initiation persists operation evidence before making the STK mutation. Ambiguous outcomes must remain unknown and must not be blindly retried.
- C2B registration is sandbox-only and ambiguous registration outcomes block another registration attempt until reconciled. Production C2B remains gated pending provider-contract evidence.
- **Current rollback readiness:** proposed only; runtime behavior and tests are not yet verified. Document any discovered data/schema or compatibility risks before marking PR ready.
## #217 verification checkpoint — 2026-10-29 UTC

- Draft PR [#218](https://github.com/NetHub-Ltd/NetPay/pull/218) is open against `dev`; it has not been merged and remains under review.
- **Observed CI failure and fix:** run [40787891591](https://github.com/NetHub-Ltd/NetPay/actions/runs/40787891591) failed because the test expected one STK callback row while the implementation correctly retained both the processed callback and a mismatched/rejected callback. The assertion was corrected to verify one `processed` and one `rejected` record.
- **Observed backend test success:** run [40788087483](https://github.com/NetHub-Ltd/NetPay/actions/runs/40788087483) completed backend migration, test, PostgreSQL and Redis steps successfully; its log reported **65 passed, 1 warning**. Its container image/startup job was still in progress at observation time, so it was not yet a complete workflow success.
- A PostgreSQL commit-failure rollback test has since been added for callback/payment/outbox atomicity. Latest code also validates production callback URL HTTPS and selects the STK transaction type from integration product type.
- **Current-head status:** CI, backend readiness, frontend lint and frontend build have been triggered for the newer head and were still in progress at last observation. Do not mark the PR ready until the exact latest-head checks finish successfully.
- No live Daraja sandbox transaction has been performed. Fake-Core tests prove application behavior only, not provider interoperability.
- #216 remains a separate verification-only readiness gate after #217's reviewed merge to `dev`.



## #217 fix and rollback checkpoint — 2026-10-29 00:15 UTC

- Latest fix commit: `52414c1ee33c030cb08a1810ce3579e496ea105e` on `feat/mpesa-application-flow-217`; PR [#218](https://github.com/NetHub-Ltd/NetPay/pull/218) remains draft/open/unmerged.
- Root cause identified from source: `backend/app/payments/service.py` constructed `ProviderRequest` without importing it, causing STK initiation to return HTTP 500 in CI run [40789386571](https://github.com/NetHub-Ltd/NetPay/actions/runs/40789386571). The fix adds it to the existing operations-model import.
- No schema/migration, database data, deployment manifest, Flux resource, `dev`/ `main`, or GHCR build/push behavior was changed by this fix. No live financial transaction was initiated.
- CI/readiness/frontend checks for the fix commit were queued: [CI 40792832066](https://github.com/NetHub-Ltd/NetPay/actions/runs/40792832066), [readiness 40792832026](https://github.com/NetHub-Ltd/NetPay/actions/runs/40792832026), [lint 40792832015](https://github.com/NetHub-Ltd/NetPay/actions/runs/40792832015), [build 40792832019](https://github.com/NetHub-Ltd/NetPay/actions/runs/40792832019). Verification is pending.
- If the PR is rejected or regression is found, use a reviewed revert commit on the topic branch. Preserve history; never reset, rebase, squash, or force-push. Do not merge without user approval; do not start #216 before #217 is merged.


## #217 second CI regression fix — 2026-10-29 00:17 UTC

- Latest application fix commit: `3237a9a6e9298ae9f7f383f09b3a3f5b19b52802`; PR #218 remains draft and unmerged.
- CI after the import fix exposed a duplicate C2B validation replay returning HTTP 500. The recovery handler rolled back the async session and then accessed an expired ORM instance; the fix captures the integration UUID before rollback and uses it in the duplicate lookup.
- No schema, migration, database data, deployment/Flux, `dev`/`main`, or GHCR workflow changes were made. Test verification remains pending; preserve history and do not start #216.


## #217 status update — 2026-10-29 00:18 UTC

- Code commit `3237a9a6e9298ae9f7f383f09b3a3f5b19b52802` passed backend migration, 65 tests (1 warning), and PostgreSQL/Redis connectivity in CI [40792997496](https://github.com/NetHub-Ltd/NetPay/actions/runs/40792997496).
- Readiness [40792997409], frontend lint [40792997425], and frontend build [40792997517] passed. CI container startup remains pending. PR #218 is still draft and unmerged.


## Marketing theme experiment rollback — 2026-10-29

- **Branch:** `feat/theme-test-marketing-conversion`; **PR #219:** https://github.com/NetHub-Ltd/NetPay/pull/219, draft/open and unmerged, target `dev`.
- The only intended application changes are new `frontend/app/theme-test/page.tsx`, its route-scoped `page.module.css`, and `frontend/app/robots.ts` disallow entries. The experiment uses illustrative payment/code data clearly labelled as not live.
- No backend, database, migrations, public homepage, product theme tokens, deployment manifests, Flux, or GHCR build/push behavior are changed.
- Roll back with a reviewed revert of the route files and robots entries. Preserve Git history; do not reset/rebase/squash/force-push. No production data or transaction changes.
- CI workflows were observed running after PR creation; final test outcomes and browser-rendered QA are pending and must be recorded before review readiness.


### Theme-test verification and recovery update — 2026-10-29 00:58 UTC

- Latest source fix commit at last check: `e54e1d77e9fcc79c3d13c2fb57907b169baee875`. Earlier frontend lint/build runs failed due to JSX text escaping and a plain homepage anchor; both were corrected. Fresh latest-head checks were queued, not yet passed.
- If failures remain, fix on `feat/theme-test-marketing-conversion` and re-run CI; do not weaken lint/type checks. Browser QA remains outstanding.
- PR #219 stays draft/unmerged. Revert only via reviewed commits; no history rewrite or production/deployment rollback is involved.


### Final source correction — 2026-10-29 01:00 UTC

- Latest source commit: `191e51f58b87267eb591a228d4251e09a204f289`. Fixed the last JSX apostrophe found by lint in the prior run.
- Fresh latest-head checks: frontend lint #575 and backend readiness #682 were in progress; frontend build #574 and CI #1128 were queued at last observation. Results are pending.
- Earlier lint/build failures belong to prior commits and must not be treated as latest-head results. No successful latest-head result is claimed yet.
- Browser-rendered QA remains not performed. PR #219 remains draft/open/unmerged against `dev`.


## Selected marketing theme refinement — rollback — 2026-10-29 01:15 UTC

- **Pre-change base:** `dev` at `416c8fa9d7d625a4be9389c12d564278c7cc1878` (includes the merged initial theme-test PR #219).
- **Current scope:** Replace the two-direction comparison on `/theme-test` with one screenshot-aligned concept. Files changed: `frontend/app/theme-test/page.tsx` and `frontend/app/theme-test/page.module.css`; tracker updates are documentation only.
- **Rollback:** Use a reviewed revert of the PR for issue #220. If the change is rejected, restore the prior versions of the two route files from the pre-implementation base (`dev` commit above) in a follow-up commit. Do not reset or rewrite history. Keep the route's robots exclusion and noindex metadata unless the route is intentionally removed.
- No schema/data, backend, deployment, Flux, or GHCR change exists to roll back. No deployment has been performed.
- **Verification caveat:** CI and browser QA are pending/not verified at this checkpoint.


### Selected theme PR checkpoint — 2026-10-29 01:12 UTC

- Draft PR #221 targets `dev` and addresses issue #220: https://github.com/NetHub-Ltd/NetPay/pull/221.
- Latest source commit at PR creation: `81f60ab4f3e2dda765ba8719d2e8fe4caf599069`; GitGuardian passed. Frontend build/lint, backend, and start/health checks were in progress; rendered browser QA is not verified.
- Rollback remains a reviewed revert of PR #221. No deployment, database change, backend behavior change, or production theme change has occurred.
