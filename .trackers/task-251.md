# Task tracker — NetPay OIDC login diagnostics

**Last updated:** 2026-11-11
**Active issue:** #251 — safe OIDC login failure diagnostics
**Implementation branch:** `fix/251-oidc-login-diagnostics`
**Verified base:** main @ 6c443b5ad79b9a913217ba9c49c5d0e33660865f
**PR target:** dev
**Status:** implementation in progress; no production settings changed.

## Approved outcome

Make production OIDC login initiation failures diagnosable through structured, correlated server logs without leaking secrets or personal data. Distinguish local configuration errors from provider discovery/network failures and unexpected internal errors. Keep browser-facing errors generic.

## Implementation scope

1. Classify known local OIDC configuration failures separately from discovery HTTP/response/issuer/endpoint errors and network timeouts.
2. Emit one allowlisted JSON runtime event with a generated request ID and category; never log exception text, stack traces, URLs, cookies, authorization codes, tokens or environment values.
3. Keep detailed diagnostics server-side and browser error messages generic.
4. Add regression tests for classification and diagnostic payload redaction.
5. Document Vercel runtime-log investigation and the discovery issuer/endpoint verification procedure.
6. Update this tracker and CI evidence after PR checks.

## Verification

Required on the exact PR head: `npm test`, `npm run lint`, `npm run typecheck`, `npm run build`, and `npm run smoke:production`. Do not claim completion until CI checks reach terminal success.

## Approval boundaries

- PR targets `dev`; repository owner performs final merge.
- No production environment-variable changes, Zitadel/NetHubKe registration changes, secret rotation, deployment configuration changes, release or merge.
- Keep public-client Authorization Code + PKCE behavior unchanged.
- No raw provider response or sensitive exception detail in logs or browser output.
