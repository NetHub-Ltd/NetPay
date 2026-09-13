# NetPay milestones — STK end-to-end & collections reliability

**Source:** STK flow audit (NetPay + mpesa-edge), September 2026  
**Integration branch:** `dev`  
**Related gate:** Production Readiness Architecture Gate v1 (collections / async / testing)

This file is the working milestone map for **initiating STK, persisting payloads, Daraja calls, edge callbacks, and settlement**. Broader P0–P3 financial milestones from the original board remain valid; items below refine the **STK / M2M path**.

---

## Status legend

| Tag | Meaning |
|-----|---------|
| **DONE** | In `dev` / product path as of last audit |
| **NEXT** | Ordered implementation work |
| **LATER** | After NEXT; not blocking first reliable STK |

---

## Milestone S0 — Baseline STK path (exists)

**Goal:** A correct shortcode + credentials can start STK; callback can settle via edge → NetPay.

| ID | Item | Status |
|----|------|--------|
| S0.1 | `POST /v1/payment-intents` + required `Idempotency-Key` | DONE |
| S0.2 | Persist intent: phone, amount_minor, integration, account_reference, optional `context_json` | DONE |
| S0.3 | Daraja OAuth + STK `processrequest` | DONE |
| S0.4 | Default callback URL via edge (`/cb/{gw_*}/stk`, Safaricom-safe path) | DONE |
| S0.5 | Edge queue → `POST /internal/events` with internal API key | DONE |
| S0.6 | Durable `inbound_events` + match `CheckoutRequestID` | DONE |
| S0.7 | State machine → succeeded/failed + ledger credit on success | DONE |
| S0.8 | Tenant-level merchant webhooks (HMAC) | DONE |
| S0.9 | `outbound_requests` audit for OAuth/STK/C2B register (not intent-linked yet) | DONE |

**Exit criteria:** Sandbox STK succeeds and lands **Paid** with ledger when edge secrets and shortcode are correct.

---

## Milestone S1 — Intent-grade STK audit & failure integrity

**Goal:** Every STK attempt is fully reconstructible from the payment intent; failures never leave ambiguous state.

| ID | Item | Status |
|----|------|--------|
| S1.1 | Persist **STK request payload** on the intent (or mandatory FK to outbound row) | NEXT |
| S1.2 | Persist **STK response payload** on the intent (full Daraja JSON, not only checkout ids) | NEXT |
| S1.3 | Add `payment_intent_id` to `outbound_requests` for all STK/OAuth calls in that flow | NEXT |
| S1.4 | On STK provider failure: transition intent → `failed`, set `failure_reason` from Daraja body | NEXT |
| S1.5 | Correct STK `TransactionType` for **till** vs **paybill** | NEXT |
| S1.6 | Payment detail UI: show last provider call outcome + callback timeline (inbound) | NEXT |

**Exit criteria:** For any intent id, support can answer: what we sent, what Daraja returned, whether callback arrived, final state — without guessing.

---

## Milestone S2 — M2M collection contract

**Goal:** Other services can start a collection with the minimum fields you specified and receive status reliably.

| ID | Item | Status |
|----|------|--------|
| S2.1 | API accepts **phone** (STK number), **amount** (canonical minor units), **integration/shortcode ref** | DONE (shape) |
| S2.2 | API accepts **status callback URL** per payment (notify endpoint) | NEXT |
| S2.3 | API accepts **metadata** as first-class field; returned on read (`IntentOut`) | NEXT |
| S2.4 | Fanout: prefer per-intent status URL, then tenant webhooks | NEXT |
| S2.5 | Document M2M: headers (`Idempotency-Key`, auth), body, callback signing, edge dependency | NEXT |
| S2.6 | OpenAPI / example client for create + status webhook | LATER |

**Minimum create body (target after S2):**

```json
{
  "integration_public_id": "gw_…",
  "phone": "2547…",
  "amount_minor": 100,
  "status_callback_url": "https://partner.example/hooks/netpay",
  "metadata": { "order_id": "…" },
  "account_reference": "ORDER123",
  "description": "Order 123"
}
```

**Exit criteria:** Partner can create STK with phone, amount, status endpoint, metadata; receives signed status posts for that payment.

---

## Milestone S3 — Edge ↔ NetPay operational certainty

**Goal:** No silent break between Daraja callbacks and NetPay settlement.

| ID | Item | Status |
|----|------|--------|
| S3.1 | Edge `/cb/{gw_*}/…` (+ legacy `/mpesa/cb/…`) | DONE |
| S3.2 | Edge → NetPay secure forward + heartbeat | DONE |
| S3.3 | NetPay System status / last inbound without browser polling edge | DONE |
| S3.4 | Surface outbound + inbound failures in product UI (ops-friendly) | NEXT |
| S3.5 | Runbook: STK stuck in waiting — checklist (creds, env, edge secrets, DLQ, checkout match) | NEXT |
| S3.6 | Alerting on outbound STK error rate / missing callbacks | LATER |

**Exit criteria:** Ops can diagnose a stuck STK in &lt; 5 minutes using UI + `outbound_requests` + `inbound_events`.

---

## Milestone S4 — UX completion for collections setup (related)

**Goal:** Operators can set up shortcodes and understand STK vs app notifications without jargon traps.

| ID | Item | Status |
|----|------|--------|
| S4.1 | Plain-language shortcode setup + connect confirmation | DONE |
| S4.2 | Home dashboard + Lucide navigation | DONE |
| S4.3 | Payment detail: provider/callback evidence (ties to S1.6) | NEXT |
| S4.4 | Guided empty states when no shortcode / STK never connected | LATER |

---

## Milestone S5 — Gate leftovers (collections-adjacent)

Aligned with original board / Production Gate — not all STK-specific.

| ID | Item | Status |
|----|------|--------|
| S5.1 | C2B confirmation mapping + tests | DONE (code path) |
| S5.2 | NetHub AS token validation (replace local auth in prod) | LATER (P2) |
| S5.3 | Secrets manager / encryption at rest for provider credentials | LATER (P2) |
| S5.4 | Rate limits, metrics, k3s hardening | LATER (P2) |
| S5.5 | Refunds / B2C (gate scenarios) | LATER (P3) |

---

## Suggested delivery order

```text
S1 (intent audit + fail integrity)
  → S2 (M2M status URL + metadata)
  → S3.4–S3.5 (ops surfaces + runbook)
  → S4.3 (payment detail evidence)
  → S5 P2+ as separate program
```

**Do not** expand edge responsibilities: edge remains public callback ingress only; NetPay remains financial authority.

---

## Traceability

| Audit theme | Milestone |
|-------------|-----------|
| Save every part of STK payload / response | S1.1–S1.3 |
| Call Safaricom, edge receives, resolve payment | S0 (done) + S1.4 + S3 |
| M2M: phone, amount, status endpoint, metadata | S2 |
| User friction (setup / waiting / errors) | S4 + S1.6 |
| M2M friction (contract / webhooks) | S2 |

---

## Changelog

| Date | Note |
|------|------|
| 2026-09-13 | Initial milestone map from STK E2E audit (NetPay + mpesa-edge) |
