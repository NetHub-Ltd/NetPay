# P0-A — Payment integrity (STK path)

## Idempotency

`POST /v1/payment-intents` **requires** header `Idempotency-Key`.

- Scope: unique per `(tenant_id, idempotency_key)`.
- Replay returns the original intent (`idempotent_replay: true`) without a second Daraja call.

## Amounts

- Source of truth: `amount_minor` (integer). **100 = 1.00 KES**.
- Daraja STK receives whole major units (`amount_minor // 100`).

## Status machine

| From | To |
|------|-----|
| `created` | `provider_requested`, `failed` |
| `provider_requested` | `succeeded`, `failed`, `expired` |
| terminal | no further changes |

Duplicate STK callbacks after settle return `status: duplicate`.

## Provider checkout id

`provider_checkout_id` is unique when set (one intent per checkout conversation).

## Ledger (P0-B)

- Table `ledger_entries` is **append-only**.
- On transition to `succeeded`, one `collection_credit` row is written (`amount_minor`, currency, provider_ref).
- Unique `(payment_intent_id, entry_type)` prevents double-posting on duplicate callbacks.
- `GET /v1/payment-intents/{id}/ledger` lists rows (tenant-scoped).
- Future refunds must add compensating entries, never edit existing rows.

## P1-A durable inbound events

- `POST /internal/events` persists by unique `event_id` then processes.
- Replays return the stored result (`processed`).
- Failures increment `attempts`; after max → `dead`.
- `POST /internal/expire-stale` moves stale `provider_requested` → `expired` (`STK_TIMEOUT_SECONDS`, default 120).
- Late success after `expired` is **ignored** (no auto-succeed).

## P1-B reconciliation

- Table `reconciliation_exceptions` (open/resolved).
- `POST /v1/reconciliation/scan` (admin) opens exceptions for:
  - succeeded without `collection_credit`
  - `provider_requested` older than 2× `STK_TIMEOUT_SECONDS`
- `GET /v1/reconciliation/exceptions`, `POST .../resolve`
- SPA: **Needs attention** + **Help** how-to guides.
