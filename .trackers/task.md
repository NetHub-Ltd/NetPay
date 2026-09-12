# Task: P0-A Payment integrity

**Milestone:** P0 — Financial integrity  
**Issues:** #15 #16 #18 #19 (partial) #20  
**Branch:** feat/p0-payment-integrity-a  
**Status:** Implementation complete — PR pending

## Completed in this PR
- State machine + transition helper
- Idempotency-Key required on create; unique (tenant_id, key)
- amount_minor (100 = 1 KES); major units at Daraja boundary
- Unique provider_checkout_id
- Migration 002
- Tests: unit transitions + idempotency/replay/concurrent/double-callback/tenant isolation
- Frontend sends amount_minor + Idempotency-Key

## Deferred (P0-B)
- Append-only ledger (#17)
