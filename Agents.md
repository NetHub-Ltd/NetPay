# Agents.md — NetPay

Instructions for AI coding agents and automated collaborators working on this repository.

This file is **authoritative** for agent behavior unless the user explicitly overrides it for a single task.

---

## 1. Engineering protocol

Follow **Engineer Mode** (proposal → approval → topic branch → PR to **`dev`** → user merge).

- Never push or merge unreviewed work to `main`.
- Prefer small PRs; keep `.trackers/` synchronized when that directory exists.
- Do not expand scope beyond the approved task.
- Secrets must never be committed.

---

## 2. Milestone alignment (mandatory)

**Every commit and every pull request must be aligned with the Production Readiness Gate milestones.**

### Source of truth

| Resource | URL / location |
|----------|----------------|
| Project board | https://github.com/orgs/NetHub-Ltd/projects/2 |
| Milestones | https://github.com/NetHub-Ltd/NetPay/milestones |
| Evaluation report | `.reports/NetPay_Production_Readiness_Evaluation.pdf` |
| Report index | `.reports/README.md` |

### Milestones

| Milestone | Meaning |
|-----------|---------|
| **M0 — Baseline** | Already demonstrated on `main` (reference only; closed issues). |
| **P0 — Financial integrity** | **Blocking GO.** Idempotency, state machine, ledger, minor-unit amounts, financial tests, unique provider refs. |
| **P1 — Collections & async** | Durable events/DLQ, timeout/unknown, reconciliation, C2B. |
| **P2 — Security & ops** | NetHub AS, secrets at rest, rate limits, metrics/runbooks, production k3s. |
| **P3 — Expand rails** | Refunds, B2C, multi-provider — **only after P0 Critical items are credible (≥ score 2 with tests).** |

### Required checks before committing or opening a PR

1. **Identify the milestone** the change belongs to (or document why it is process-only: CI, docs, trackers, Agents.md).
2. **Link tracking** — PR body and/or commits should reference the relevant issue number(s) and milestone (e.g. `Closes #15`, `Milestone: P0`).
3. **Do not skip P0 for product features** — do not implement P3 (refunds, B2C, new providers) or non-essential product expansion while Critical P0 items remain open, unless the user explicitly authorizes an exception.
4. **Tests are product** — financial or domain behavior changes must include or update automated tests appropriate to the change; CI must stay green.
5. **Board hygiene** — if the agent can update GitHub Issues/Projects, move or label items to match reality (`In Progress`, `Done (M0)`, etc.). If it cannot, state the intended board update in the PR for a human.

### PR description template (minimum)

```markdown
## Summary
…

## Milestone alignment
- Milestone: P0 | P1 | P2 | P3 | M0 | process-only
- Related issues: #…
- Why this does not violate P0-before-P3 ordering: …

## Risk / production impact
…

## Test plan
…

## Rollback
…
```

### Out-of-milestone work

Allowed without a readiness issue only when **process-only**, for example:

- Engineer Mode trackers
- CI workflow fixes
- Documentation under `.reports/` or `Agents.md`
- Branch/PR hygiene

Even then, say so explicitly under **Milestone alignment: process-only**.

---

## 3. Auth boundary

NetPay does **not** own end-user registration or login long-term.

- Users are authorized by **NetHub AS**; NetPay validates tokens.
- Local password login is transitional.
- See `docs/auth-model.md` when present on the branch.

---

## 4. Quality defaults

- Frontend: `npm run lint` and `npm run build` (or framework equivalent) must pass for frontend changes.
- Backend: pytest (and framework-appropriate new tests) for behavior changes.
- Prefer clear names, explicit errors, no silent swallowed exceptions.
- Document public surface and non-obvious logic.
- Mark hotfixes and deliberate debt in code and trackers.

---

## 5. Deployment preference

Preferred target: **k3s**. Inspect `deploy/` before assuming layout.

---

## 6. Session start (agents)

1. Read this file.
2. Check open milestones and Critical **P0** issues.
3. Confirm the approved task maps to a milestone (or process-only).
4. Inspect `.trackers/` if present.
5. Propose before implementing non-trivial work; wait for explicit approval when Engineer Mode requires it.

---

**On every commit and PR: verify milestone alignment first.**
