# Task: P0-B Append-only ledger

**Milestone:** P0 — Financial integrity  
**Issue:** #17 (+ ledger assertions for #19)  
**Branch:** feat/p0-ledger  

## Completed
- ledger_entries model + migration 003
- post_collection_credit on succeeded
- GET /v1/payment-intents/{id}/ledger
- Tests: one credit on success+duplicate callback; none on failed

## After merge
Close #17; verify P0 milestone complete.
