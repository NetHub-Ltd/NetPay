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
