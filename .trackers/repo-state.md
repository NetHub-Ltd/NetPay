# NetPay repository state

**Last updated:** 2026-10-22

## Branches

| Branch | Known commit | Meaning |
|---|---|---|
| `work/minimal-netpay-rebuild` | `5bcbf865837cedc258e6a11d483b12a28f7f2ccc` (baseline before tracker commits) | Working branch |
| `dev` | `5bcbf865837cedc258e6a11d483b12a28f7f2ccc` (baseline before tracker commits) | Integration branch; identical to working branch at last branch inspection |
| `main` | `a55500c2838b8ad1cc637a121f2b30f7f88132d0` | Older code; not modified by this task |

**Important:** The tracker commits will advance `work/minimal-netpay-rebuild` only. Update this file with the resulting branch tip after all tracker files are committed and verified.

## Pull request and issue

- PR #178: closed, unmerged. A retarget to `dev` was rejected because head and base had no differing commits at the time. The PR was closed without explicit user approval; this was a process error and no merge occurred.
- Issue #179: rebuild delivery/verification tracking issue — https://github.com/NetHub-Ltd/NetPay/issues/179

## Known workflow evidence

| Workflow | Run | Previously reported state | What remains |
|---|---|---|---|
| CI | [#569](https://github.com/NetHub-Ltd/NetPay/actions/runs/39757001572) | Success | Recheck current run/jobs and backend-related coverage |
| Frontend build | [#15](https://github.com/NetHub-Ltd/NetPay/actions/runs/39757002712) | Success | Recheck current run/jobs and exact lint/typecheck/build steps |

These states are carried forward from the previous session summary and must be re-fetched before being used as current verification.

## Tracker health

- `.trackers/` was present on `main` with older STK/C2B and release-workflow records.
- `.trackers/` was absent from `work/minimal-netpay-rebuild` at the start of this task.
- The old tracker contents are not authoritative for the clean rebuild; rebuild-specific trackers are being established.
- Deployment manifests are out of scope; Flux owns deployment reconciliation.

## Update protocol

Before work:
1. Read this file and `task.md`, `milestone.md`, `rollback.md`, and the applicable repo instructions.
2. Record intended scope, baseline commit, and any changed assumptions before implementation.
3. If the tracker is missing or contradictory, repair the tracking baseline before application changes.

During work:
1. Update task/milestone status when meaningful evidence changes.
2. Record exact workflow/run IDs, commands, and outcomes; distinguish failure, skipped, and not run.
3. Stop and surface scope or approval decisions instead of silently expanding work.

After work:
1. Re-fetch branch refs and tracker files to verify persisted contents.
2. Record the resulting working-branch commit and PR/issue state.
3. List changed, verified, not verified, risks, rollback, and follow-ups in the report.
4. Never claim a remote write succeeded until the tool response and follow-up read confirm it.
