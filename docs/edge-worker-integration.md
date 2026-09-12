# mpesa-edge ↔ NetPay secure integration

## Architecture

```
Safaricom Daraja
    → HTTPS POST /mpesa/cb/{public_id}/{event}
    → Cloudflare Worker (mpesa-edge)
    → Queue mpesa-callbacks
    → Worker queue consumer
    → POST /internal/events  +  X-Internal-Api-Key
    → NetPay inbound_events + processor (STK / C2B / …)
```

Public traffic terminates at the **edge**. NetPay financial APIs are never opened to Safaricom without the internal key path.

## Shared secret

| System | Variable |
|--------|----------|
| NetPay (k3s / env) | `INTERNAL_API_KEY` |
| mpesa-edge (Wrangler secret) | `NETPAY_INTERNAL_API_KEY` |

Values **must match**. Generate a long random secret (e.g. 32+ bytes). Rotate by updating both sides, then redeploying the Worker.

NetPay validates:

```http
POST /internal/events
X-Internal-Api-Key: <same secret>
Content-Type: application/json
```

Unauthorized calls receive **401**.

## Base URL

Edge secret `NETPAY_BASE_URL` = API origin only (no path, no trailing slash), e.g. `https://api.example.com`.

Consumer calls `{NETPAY_BASE_URL}/internal/events`.

## Envelope contract

Edge sends the normalized envelope (see mpesa-edge README). NetPay maps:

- `event_id` → durable idempotency (`inbound_events`)
- `integration.id` or `integration.public_id` → `integrations.public_id` (`gw_…`)
- `event_type` containing `stk` → STK callback processing
- `payload` → Safaricom body (unchanged)

## Operational checklist

1. Create NetPay integration; note `public_id`.
2. Register Daraja callbacks:  
   `https://gateway.nethub.co.ke/mpesa/cb/{public_id}/stk` (and validation/confirmation as needed).
3. Set NetPay `INTERNAL_API_KEY` and edge secrets; deploy both.
4. Sandbox STK → edge 202 → NetPay intent **Paid** + ledger credit.
5. Replay same `event_id` → no second ledger row.
6. Monitor Cloudflare queue DLQ `mpesa-callbacks-dlq` and NetPay **Needs attention**.

## Related code

- NetPay: `app/api/routes/internal.py`, `app/services/inbound_events.py`
- Edge: `src/netpay_forward.py`, `src/entry.py` `queue` handler
