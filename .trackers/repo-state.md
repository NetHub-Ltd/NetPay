# NetPay repository state

**Last updated:** 2026-10-22

## Branches

| Branch | Commit | Meaning |
|---|---|---|
| `work/minimal-netpay-rebuild` | See live branch ref | Working branch; tracker-only commits are on this branch |
| `dev` | `5bcbf865837cedc258e6a11d483b12a28f7f2ccc` | Integration branch; unchanged by tracker creation |
| `main` | `a55500c2838b8ad1cc637a121f2b30f7f88132d0` | Older code; untouched by this task |

At the start of tracker creation, `work/minimal-netpay-rebuild` and `dev` both pointed to `5bcbf865837cedc258e6a11d483b12a28f7f2ccc`. Tracker-only commits advanced the working branch beyond the application baseline. The branch page/API is the authoritative source for the live tip because each tracker correction itself advances the tip. The branches now differ by tracker commits; no application code was changed by this task.

## Pull request and issue

- PR #178: closed, unmerged. A retarget to `dev` was rejected because head and base had no differing commits at the time. The PR was closed without explicit user approval; this was a process error and no merge occurred.
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
- Four rebuild-specific trackers now exist on the working branch: `task.md`, `milestone.md`, `repo-state.md`, and `rollback.md`.
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
