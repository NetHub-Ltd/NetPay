# NetPay reports

## Production Readiness Evaluation (2026-09-12)

- **File:** [NetPay_Production_Readiness_Evaluation.pdf](./NetPay_Production_Readiness_Evaluation.pdf)
- **Evaluated:** `main` @ `709ceb9`
- **Decision:** **NO-GO** under Architecture Gate v1.0

### Tracking

GitHub milestones and issues enforce the roadmap from this report:

| Milestone | Purpose |
|-----------|---------|
| **M0 — Baseline** | Already demonstrated on main (closed reference issues) |
| **P0 — Financial integrity** | Blocking GO (idempotency, state machine, ledger, tests, …) |
| **P1 — Collections & async** | Durable events, timeout/unknown, reconciliation, C2B |
| **P2 — Security & ops** | NetHub AS, secrets, rate limits, metrics, k3s |
| **P3 — Expand rails** | Refunds, B2C, multi-provider (after P0 ≥2) |

Labels: `gate-done`, `gate-partial`, `gate-missing`, `P0`–`P3`, `critical`, `testing`.

Issues: https://github.com/NetHub-Ltd/NetPay/milestones

### GitHub Project board

Create a **Projects (v2)** board named **NetPay Production Readiness Gate** linked to this repo once a PAT/token with **Projects read/write** is available. Suggested columns: `Done (M0)`, `P0`, `P1`, `P2`, `P3`, `Blocked`. Auto-add issues with labels `P0`–`P3` and `gate-done`.
