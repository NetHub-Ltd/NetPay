# Task tracker — NetPay OIDC login diagnostics

**Last updated:** 2026-11-11
**Active issue:** #251 — safe OIDC login failure diagnostics
**Implementation branch:** `fix/251-oidc-login-diagnostics`
**Verified base:** main @ 6c443b5ad79b9a913217ba9c49c5d0e33660865f
**PR:** [#252](https://github.com/NetHub-Ltd/NetPay/pull/252), targeting `dev`
**Latest head:** `b5eaa14c08112588fdde83fab83b6fbe6aac47ba`
**Status:** draft PR open; CI status not yet available from the workflow-run query. No production settings changed.

## Approved outcome

Make production OIDC login initiation failures diagnosable through structured, correlated server logs without leaking secrets or personal data. Distinguish local configuration errors from provider discovery/network failures and unexpected internal errors. Keep browser-facing errors generic.

## Implementation delivered in PR #252

1. Classify local configuration, discovery HTTP/response/issuer/endpoint, provider-unreachable and unexpected failures.
2. Emit one allowlisted JSON runtime event with a generated request ID and category; never log exception text, stack traces, URLs, cookies, authorization codes, tokens or environment values.
3. Keep detailed diagnostics server-side and browser error messages generic.
4. Add regression tests for classification and diagnostic payload redaction, including malformed discovery JSON and invalid endpoint URLs.
5. Document Vercel runtime-log investigation and the discovery issuer/endpoint verification procedure.

## Verification

Required on the exact PR head: `npm test`, `npm run lint`, `npm run typecheck`, `npm run build`, and `npm run smoke:production`. No local execution is claimed. Do not mark complete until CI checks reach terminal success.

## Approval boundaries

- PR targets `dev`; repository owner performs final merge.
- No production environment-variable changes, Zitadel/NetHubKe registration changes, secret rotation, deployment configuration changes, release or merge.
- Keep public-client Authorization Code + PKCE behavior unchanged.
- No raw provider response or sensitive exception detail in logs or browser output.
