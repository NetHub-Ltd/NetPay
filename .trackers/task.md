# Task: #24 C2B notification handling

**Branch:** feat/p1-c2b-notification-handling → **dev**

## Done
- [x] Confirmation → open intent by BillRef / account_reference
- [x] TransID dedupe (no double ledger)
- [x] Unmatched / missing BillRef → reconciliation exception
- [x] Amount mismatch → exception, no silent succeed
- [x] Validation audit accepted
- [x] Tests for success, dup TransID, unmatched, mismatch, validation
- [x] Help docs for paybill/till C2B
