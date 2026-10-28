# NetPay mpesa_core — implementation specification

Status: Approved implementation scope; endpoint-level contracts must be verified against current Safaricom documentation before coding each adapter.
Repository baseline: dev at 82bae5b7c8e1704491b0aa8eec1dfa8fa948364f (observed 2026-10-28).
Decision: Implement the complete proposed API inventory, including capabilities not exposed in the initial merchant UX. No adapter is complete until its contract and tests exist.

## 1. Goal and boundaries

Build a compact asynchronous Python package at backend/app/mpesa_core/. FastAPI creates one shared MpesaCore instance per application process during lifespan and closes it on shutdown. This is an application-scoped singleton, not a fragile class-level singleton.

Core owns OAuth token acquisition/cache/expiry, typed operation methods, provider URL and payload construction, protocol validation, reusable async HTTP transport, bounded timeouts, provider response parsing/normalization, typed errors, safe structured operation logs, and callback payload parsing/normalization.

NetPay application owns merchant authorization, integration lookup, credential decryption/rotation and persistence, public APIs and callback routes, callback correlation/deduplication/acknowledgement, payment state, application idempotency, durable audit persistence, reconciliation scheduling, and outbox/event delivery. Core must not query the database or become a second application layer. Resolve credentials in the application and pass them to Core through typed secret-bearing context.

A valid callback schema is not proof of authenticity. An integration ID in a callback URL is a routing key, not authentication. HTTP 200 or an STK initiation acknowledgement is not proof of payment success.

## 2. Proposed module layout

- client.py: MpesaCore, OAuth lifecycle, transport and operation methods.
- schemas.py: typed requests/results, provider response envelopes and normalized callback models.
- validation.py: reusable and operation-specific validation.
- errors.py: stable typed errors and outcome/retry classification.
- callbacks.py: callback parsing and normalization only; no FastAPI routes or persistence.
- __init__.py: small intentional exports.

Inspect existing backend conventions and Pydantic version before choosing exact model APIs. Avoid unnecessary abstractions.

## 3. Shared schemas and operation contracts

Every operation has a dedicated typed request and result model. Raw provider JSON exists only at the transport/parser boundary and is validated immediately.

Shared primitives:
- Environment: sandbox or production; never silently fall back.
- Credentials: consumer key/secret and optional product-specific passkey, initiator name/password or security credential material where required. Secret values must not leak through repr, str, errors, logs, results or audit metadata.
- IntegrationContext: opaque integration ID, environment, shortcode/product metadata, enabled capability set, credential version and resolved credentials.
- OperationOutcome: accepted, completed only with authoritative completion evidence, rejected, not_sent, or unknown.
- ProviderError: stable internal code, safe message, HTTP status if known, safe provider code, retry classification and whether the request may have reached Daraja.
- OAuthToken: secret access token, expiry deadline and non-secret cache metadata.
- ProviderOperationResult: typed operation payload, safe request/correlation IDs and outcome; never includes credentials or access tokens.

Operation-specific models:
- STK Push: normalized Kenyan MSISDN, positive integer KES amount in minor units at the NetPay boundary, account reference, description, shortcode/passkey context and application-generated callback URL. Convert to documented Daraja amount units at the boundary. Result includes merchant/checkout request IDs and acknowledgement, not payment success.
- STK Query: checkout request ID and required shortcode/password context; result is provider evidence, not an invented final payment state.
- C2B registration: validation URL, confirmation URL and response type; registration is opt-in and capability-gated.
- C2B simulation: sandbox-only shortcode, MSISDN, amount and bill reference; block production before transport.
- Dynamic QR: merchant name, reference, amount, transaction code, credit-party identifier and requested image size; result includes encoded QR data.
- Transaction Status: receipt/originator conversation identifier, shortcode/party context, identifier type, initiator/security credential and result/timeout callback URLs as required. Acknowledgement is asynchronous.
- Account Balance: shortcode, identifier type, initiator/security credential and result/timeout callback URLs; asynchronous result.
- Reversal: original transaction ID, amount where required, party context, initiator/security credential, remarks/occasion and callbacks. Never blindly retry after an ambiguous send.
- B2C: recipient, amount, command, originator conversation ID, initiator/security credential, remarks/occasion and callbacks. Acknowledgement differs from final result callback.
- B2B: supported command variant, PartyA/PartyB, amount, account reference where required, initiator/security credential, remarks/occasion and callbacks; validate each command variant.
- Pull Transactions: documented query window/filter and response/callback context; exact date range, pagination and callback semantics must be confirmed.
- Ratiba/Standing Orders, Bill Manager, Tax Remittance, Lipa na Bonga and B2B Express Checkout have typed adapters. Where the public portal does not expose complete field schemas, endpoint/payload assumptions are provisional and must pass authenticated documentation or sandbox contract tests before production enablement. If the catalogue maps a capability to an existing endpoint/command, use that documented mapping. Never invent new endpoints.

Callback models:
- STK callback: CheckoutRequestID, MerchantRequestID, ResultCode/ResultDesc and optional metadata items such as amount, receipt, transaction time and phone.
- C2B validation/confirmation: documented transaction type, TransID, TransTime, TransAmount, business shortcode, bill reference, MSISDN and optional invoice/organization fields where present.
- Async result/timeout callback: documented envelope with conversation IDs, originator ID, result type/code/description, transaction ID, typed result parameters and reference data.
- Handle bounded unknown fields at parser boundary for forward compatibility; do not persist raw callback PII by default. Application owns correlation, deduplication, authenticity/risk checks and state transitions.

## 4. Validation and reliability rules

- Normalize supported Kenyan phone formats to 254XXXXXXXXX; reject malformed or ambiguous values instead of guessing.
- Use integer minor units in NetPay domain contracts; never use float money arithmetic. Convert at the provider boundary according to each endpoint's documented unit/precision. Reject fractional KES where the endpoint requires whole shillings.
- Validate required fields, documented lengths, enumerations and character constraints per endpoint. Do not invent one universal amount limit or apply STK limits to unrelated products.
- Validate URLs and production HTTPS policy; syntactic validity does not prove callback reachability.
- Validate date ranges and timezone awareness; reject inverted/unsupported windows.
- Fail before network I/O when credentials, environment, product prerequisites or capability gates are missing.
- Validate HTTP status, content type where relevant, JSON shape, required IDs, response codes and provider semantics. HTTP 200 alone is not success.
- Distinguish failure before send from timeout/connection loss after possible transmission. No blind retries of financial mutations. Retry only when documentation or a real idempotency contract makes it safe.
- Bound request/response body size and prevent secrets, passkeys, security credentials, auth headers, full MSISDNs and unnecessary PII from entering logs/errors/audit metadata.
- Isolate OAuth cache by environment and credential identity/version, not shortcode alone. Coordinate concurrent refresh per cache key, refresh before expiry, and invalidate on credential rotation.

## 5. Daraja API inventory

Use sandbox.safaricom.co.ke and api.safaricom.co.ke only where the current product docs specify those hosts. The following paths are confirmed by official pages reviewed so far; entries marked verification required must be verified before implementation and must never be guessed.

| Capability | Documented path / contract | Mode and boundary |
|---|---|---|
| OAuth authorization | GET /oauth/v1/generate?grant_type=client_credentials | Foundation; secret token cache per environment and credential identity. |
| M-Pesa Express / STK Push | POST /mpesa/stkpush/v1/processrequest | Core collection; acknowledgement is not payment success. |
| STK Push Query | POST /mpesa/stkpushquery/v1/query | Query evidence only; interpret result codes precisely. |
| C2B URL Registration | POST /mpesa/c2b/v1/registerurl | Explicit opt-in and shortcode/product permission gate. |
| C2B validation/confirmation | Inbound NetPay callback routes | Core parser/normalizer; application owns route, acknowledgement and payment-state handling. |
| C2B Simulation | POST /mpesa/c2b/v1/simulate | Sandbox only; production use must be blocked before transport. |
| Dynamic QR Code | POST /mpesa/qrcode/v1/generate | Capability-gated; transaction code and amount rules per docs. |
| Transaction Status | POST /mpesa/transactionstatus/v1/query | Asynchronous; receipt or originator conversation ID and callbacks required. |
| Account Balance | POST /mpesa/accountbalance/v1/query | Restricted; initiator/security credential and account role required. |
| Reversal | POST /mpesa/reversal/v1/request | Restricted, asynchronous; eligibility varies by transaction type. |
| B2C | POST /mpesa/b2c/v3/paymentrequest | Restricted disbursement; initiator/security credential, product access and callback handling. |
| B2B | POST /mpesa/b2b/v1/paymentrequest | Restricted transfer; enumerate supported command IDs and party types from docs. |
| Pull Transactions | POST /pulltransactions/v1/register and POST /pulltransactions/v1/query | C2B missed-callback recovery; limited lookback window, nominated number and offset semantics require sandbox verification. |
| B2B Express Checkout | POST /v1/ussdpush/get-msisdn | USSD push to the paying merchant's till operator; documented by current public SDK/OpenAPI catalogues; production permission and callback contract must be verified. |
| Ratiba / Standing Orders | POST /standingorder/v1/createStandingOrderExternal | Commercial recurring collection; requires customer authorization and product agreement/permissions. |
| Bill Manager | POST /v1/billmanager-invoice/optin, /single-invoicing, /bulk-invoicing, /reconciliation, /cancel-single-invoice, /cancel-bulk-invoice, /change-optin-details, /change-invoice, /change-invoices | Separate invoicing/reconciliation product; endpoint family corroborated by public SDK catalogues; operation payloads require sandbox contract validation. |
| Tax Remittance | POST /mpesa/b2b/v1/remittax | Dedicated documented KRA tax remittance product; requires prior KRA PRN integration and product/initiator permissions. |
| Lipa na Bonga | POST /v1/lipa/na/bonga/redeem-paybill | Customer redeems Bonga points; payment settlement notification is received through the registered C2B confirmation route. Payload fields require sandbox contract validation. |

### Official documentation reviewed
- Transaction Status: https://developer.safaricom.co.ke/apis/TransactionStatus
- Dynamic QR: https://developer.safaricom.co.ke/apis/DynamicQRCode
- B2C: https://developer.safaricom.co.ke/apis/BusinessToCustomer
- STK Push: https://developer.safaricom.co.ke/apis/MpesaExpressSimulate
- Safaricom Node library (corroborating subset, not authority for complete catalogue): https://github.com/safaricom/mpesa-node-library
- Tax Remittance: https://developer.safaricom.co.ke/apis/TaxRemittance
- Bill Manager: https://developer.safaricom.co.ke/apis/BillManager
- Ratiba: https://developer.safaricom.co.ke/apis/MpesaRatiba
- B2B Express Checkout: https://developer.safaricom.co.ke/apis/B2BExpressCheckout
- Public SDK catalogue cross-check (not official): https://laraveldaraja.com/apis/overview/
- Pull Transactions request details (public SDK/docs cross-check, not official): https://laraveldaraja.com/apis/pull-transactions/
- Lipa na Bonga request details (public SDK/docs cross-check, not official): https://laraveldaraja.com/apis/lipa-na-bonga/

Safaricom's current portal confirms Transaction Status is asynchronous and accepts a receipt or originator conversation ID; it documents Dynamic QR and B2C endpoints. The official Node library lists a subset of established APIs, including balance, B2B, B2C, C2B registration/simulation, STK push/query, reversal and transaction status. The product owner approved the proposed inventory, not the invention of undocumented routes. A name that cannot yet be verified remains a catalogue-verification gate until authoritative documentation establishes the contract; the matrix must then record endpoint/version, roles/credentials, sandbox availability, callback schema, asynchronous semantics and test fixtures.

## 6. Error and outcome taxonomy

Distinguish invalid input, missing credentials, invalid environment, disabled capability, OAuth rejection/malformed response, definitive provider rejection, transport failure before send (not_sent), timeout/connection loss after possible send (unknown), malformed/contradictory response, rate limit/transient provider failure, and invalid callback payload. Retry classification is operation-specific. Never map ambiguous outcomes to failed or succeeded without authoritative evidence.

## 7. Exhaustive test plan

For every operation test:
- Valid request maps to exact documented method, path, headers and payload.
- Required/optional fields, enums, lengths, amount and identifier boundaries.
- Success acknowledgement and required IDs.
- Provider rejection and normalized safe errors.
- Non-2xx, invalid content type, non-JSON, missing fields and unexpected types.
- Connection failure before send, timeout after possible send, server/rate-limit responses.
- Capability disabled, unsupported environment, missing credentials/initiator/passkey/permissions.
- Log, exception and result redaction.
- Correct retry classification and no duplicate financial mutation after ambiguous send.

Shared cross-operation tests cover phone normalization, money conversion without floats, OAuth failures/expiry/credential rotation/concurrent refresh, environment and credential isolation, multiple integrations using one client, lifecycle cleanup, malformed/oversized callback bodies, unknown fields, duplicate/out-of-order callbacks, identifier and amount mismatches, no false payment success, opt-in C2B registration, sandbox-only simulation, and asynchronous result semantics for status/disbursement/reversal/balance calls.

Test tiers:
1. Fast deterministic unit tests using httpx.MockTransport or existing repo-equivalent mocks in CI.
2. Application/database integration tests for credential resolution and audit/state ownership where applicable.
3. Opt-in sandbox contract tests only when credentials, enabled products and reachable callbacks exist. Never use production credentials or execute real financial transactions in tests.
4. Backend tests, migration checks, frontend checks, CI, image build and container smoke. Report exact run IDs/commands and never invent a coverage threshold.

## 8. Security, observability and performance

Structured logs may include operation, environment, correlation ID, safe integration identifier, duration, HTTP status and normalized outcome. Never log secrets, tokens, authorization headers, passkeys, security credentials or full callback payloads. Core logs are distinct from durable audit persistence; NetPay persists audit evidence. If an operation requires durable audit before sending, the application must enforce that precondition. Use one reusable async HTTP client with explicit connect/read/write/pool timeouts, bounded connection limits and clean shutdown. Keep token cache bounded; do not add Redis/database dependencies solely for Core token caching without evidence. No new runtime dependency without a documented need.

## 9. Delivery sequence

1. Specification and all four trackers are committed to the approved topic branch; issue #187 tracks this scope.
2. Verify and freeze endpoint-specific contracts against the current official catalogue; adapters with provisional public-SDK-derived contracts remain gated from production until sandbox contract validation.
3. Implement shared schemas, validation, errors, OAuth and transport foundation.
4. Implement API adapters in bounded groups, with tests for each.
5. Implement callback parsers and verify application route boundaries without restoring the deleted router design by assumption.
6. Run repository tests, CI and container checks; record exact outcomes.
7. Open one PR targeting dev and leave it unmerged for user review.

## 10. Rollback and exclusions

Use reviewed revert commits; never rewrite history. Any justified database change requires a new Alembic revision and reviewed safe downgrade; do not remove schema objects with live data without separate approval. No production credentials, production financial calls, deployment-manifest edits, Flux changes, direct pushes to dev/main, or merge are authorized.
