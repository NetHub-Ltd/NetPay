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
