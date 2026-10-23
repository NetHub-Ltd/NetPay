# Daraja capability notes

Verified against Safaricom's public developer portal on 2026-10-20. Re-check before production rollout because API permissions and go-live behavior can vary by app and shortcode.

## M-Pesa Express / STK Push

Official documentation: https://developer.safaricom.co.ke/apis/MpesaExpressSimulate

- OAuth uses `GET /oauth/v1/generate?grant_type=client_credentials` with Basic authentication; sandbox and production have distinct hosts.
- STK initiation is `POST /mpesa/stkpush/v1/processrequest`.
- `ResponseCode = 0` means the request was accepted for processing, not that the customer completed payment. The result arrives asynchronously at `CallBackURL`.
- Callback correlation fields include `MerchantRequestID` and `CheckoutRequestID`. Successful callback metadata can include amount, M-Pesa receipt, transaction date and phone number; unsuccessful callbacks may omit `CallbackMetadata`.
- PayBill uses `CustomerPayBillOnline`; Till uses `CustomerBuyGoodsOnline`.
- The docs specify `AccountReference` max 12 characters and `TransactionDesc` max 13 characters.
- For Till integrations, the STK `BusinessShortCode` may be the Go Live short code / HO / store number while `PartyB` is the Till number. Store these independently; do not assume they are always identical.

## C2B URL registration

Official documentation: https://developer.safaricom.co.ke/apis/CustomerToBusiness

- C2B URL registration enables confirmation notifications and optional validation callbacks for PayBill/Till payments.
- C2B registration is separate from STK Push. A merchant that only uses STK Push must not be forced to register C2B URLs.
- Safaricom documents external C2B validation as optional and requiring activation through its support process. Registering a validation URL does not by itself prove external validation is enabled for the shortcode.
- The current NetPay validation handler checks basic request shape, shortcode, and positive amount, but does not yet support merchant-specific account-reference validation rules. Do not enable external validation in production if the merchant requires account-level rejection rules until that policy is implemented and tested.
- Public callback URLs are required; production URLs must use HTTPS.
- Sandbox URLs may be registered repeatedly or overwritten. Production URL registration is documented as one-time unless the existing registration is removed through URL management or Safaricom support.
- If production registration times out after the request may have reached Safaricom, store the outcome as unknown and do not blindly retry; reconcile the registration status first.

## Transaction status / reconciliation

Official documentation: https://developer.safaricom.co.ke/apis/TransactionStatus

- Transaction Status is an asynchronous API and a secondary reconciliation mechanism when callbacks are missing.
- The docs require a receipt number or originator conversation ID and list additional organization/API-user authorization fields, including an initiator and security credential.
- Consumer key/secret alone do not establish that NetPay can query every transaction. Implement transaction-status queries only when the merchant's shortcode, API product, initiator configuration and permissions have been confirmed.
- When the required status-query capability is unavailable, retain `unknown` outcomes and report that verification is unsupported rather than inferring failure or success.

## Security interpretation

- The opaque integration ID in a callback URL is routing metadata, not cryptographic authentication.
- Validate the callback schema, integration, known request/receipt, amount and available phone/context; deduplicate and prevent terminal-state regression.
- Safaricom's public callback examples do not document a callback signature. Do not claim signed callbacks unless a supported verification mechanism is confirmed for the merchant's product.
- Treat malformed or mismatched callback data as a recorded discrepancy, not payment success.


## Broader capability inventory — refreshed 2026-10-23

Official catalogue: https://developer.safaricom.co.ke/apis

The portal currently lists the following API families relevant to a payment gateway. This is a discovery inventory, not a claim that every API is enabled for every Daraja application or merchant shortcode.

| API family | Intended NetPay disposition | Preconditions / safety gate |
|---|---|---|
| Authorization | Core | Consumer key/secret per environment; token is secret and short-lived. |
| M-Pesa Express / STK Push | Core | Passkey, shortcode/product details, transaction type, callback URL; acceptance is not payment success. |
| STK Query | Core where supported | Query by known checkout request ID; a query result must be normalized without overriding stronger terminal evidence incorrectly. |
| C2B Register URL | Core, opt-in | Merchant explicitly enables C2B; distinguish URL registration from activation of external validation. Ambiguous registration outcome requires reconciliation before retry. |
| C2B Validation / Confirmation | Core, callback route | Validate schema, integration/shortcode, amount and known context; deduplicate; never trust callback routing ID as authentication. |
| Transaction Status | Gated | Requires transaction identifier or originator conversation ID plus appropriate API user/initiator, security credential, callback URLs and permissions. Asynchronous. |
| Account Balance | Gated | Requires appropriate organization API user and balance-query role; callback-based asynchronous result. Sensitive financial data. |
| Reversals | Gated, high-risk | Requires reversal initiator/security credential and permissions; require explicit authorized caller, original transaction correlation, idempotency and audit. Never auto-reverse from a callback/error. |
| Dynamic QR | Conditional | Requires product/shortcode permission and supported merchant use case; typed response and expiry handling. |
| Pull Transactions | Provisional adapter, disabled by default until contract verification | Requires relevant account/API permission and bounded time-window handling; verify exact field names, endpoint version and callback semantics in the merchant-accessible official docs/sandbox before enabling. |
| B2C | Gated, high-risk | Requires B2C/bulk-disbursement capability, API initiator, security credential and callback handling. No public app endpoint should expose it without separate authorization/limits. |
| Business Pay Bill / Business Buy Goods | Gated, high-risk; adapter implemented | Requires product-specific shortcode and initiator permissions; explicitly authorize destination, amount, operation and idempotency. |
| B2B Express Checkout | Follow-up, not implemented | The public [Daraja portal page](https://developer.safaricom.co.ke/apis/B2BExpressCheckout) lists the API but does not expose its request schema or endpoint in accessible documentation; verify the exact contract with Safaricom before implementation or enablement. |
| Tax Remittance, Bill Manager and other product-specific APIs | Document disposition; implement only if relevant to the approved NetPay use cases | Require product and business prerequisites. Do not expose unsupported or unauthorized capabilities. |

### Cross-operation contract requirements

- Shared transport: environment-specific base URL, bounded connect/read/write/pool timeouts, JSON validation, normalized safe error codes, correlation ID, no automatic retry for ambiguous non-idempotent requests.
- Operation audit: record operation name, integration/merchant IDs, correlation ID, timestamps, sanitized request metadata, HTTP status, provider request identifiers, normalized outcome/error code, and safe response metadata. Never persist credentials/tokens/auth headers or full callback PII by default.
- Callback handling: validate input shape, preserve minimal evidence, deduplicate on stable provider IDs where available plus a deterministic fingerprint, and process duplicate/out-of-order callbacks idempotently.
- Payment state remains owned by NetPay's payment domain. Provider acceptance, callback receipt and a status-query response are evidence with different strengths; none may bypass domain state-transition rules.
- Official docs are dynamic and product permissions vary. Re-verify endpoint versions, field constraints, prerequisites and callback semantics before production enablement.

### Official sources reviewed

- https://developer.safaricom.co.ke/apis
- https://developer.safaricom.co.ke/apis/Authorization
- https://developer.safaricom.co.ke/apis/MpesaExpressSimulate
- https://developer.safaricom.co.ke/apis/CustomerToBusiness
- https://developer.safaricom.co.ke/apis/TransactionStatus
- https://developer.safaricom.co.ke/apis/BusinessToCustomer
