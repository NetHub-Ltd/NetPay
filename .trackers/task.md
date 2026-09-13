# Task: S1 STK intent audit + notify fanout

**Branch:** feat/s1-stk-intent-audit → **dev**

## Done
- [x] stk_request_json / stk_response_json on intent (Password redacted)
- [x] payment_intent_id on outbound_requests
- [x] STK fail → failed + failure_reason
- [x] Till → CustomerBuyGoodsOnline; paybill → CustomerPayBillOnline
- [x] status_callback_url + metadata on create; detail GET
- [x] Fanout: intent URL → tenant webhooks → none (edge always for provider callbacks)
- [x] Payment detail: provider call section
- [x] Migration 007
