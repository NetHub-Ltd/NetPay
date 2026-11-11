import assert from "node:assert/strict";
import test from "node:test";
import {
  classifyOidcLoginFailure,
  createOidcLoginDiagnostic,
} from "../lib/server/oidc-diagnostics.mjs";
import { getOidcConfigurationChecks, isOidcConfigured } from "../lib/server/security.mjs";

test("classifies missing configuration as missing_env without exposing the missing value", () => {
  const result = classifyOidcLoginFailure(
    new Error("Missing required server configuration: OIDC_CLIENT_ID"),
  );
  assert.deepEqual(result, { category: "missing_env", browserError: "configuration" });
});

test("classifies precise configuration failures with allowlisted categories", () => {
  assert.deepEqual(
    classifyOidcLoginFailure(new Error("OIDC redirect origin must match NetPay")),
    { category: "redirect_origin_mismatch", browserError: "configuration" },
  );
  assert.deepEqual(
    classifyOidcLoginFailure(new Error("OIDC_TRANSACTION_SECRET must contain at least 32 characters")),
    { category: "transaction_secret_invalid", browserError: "configuration" },
  );
  assert.deepEqual(
    classifyOidcLoginFailure(new Error("OIDC issuer URL is invalid")),
    { category: "issuer_invalid", browserError: "configuration" },
  );
  assert.deepEqual(
    classifyOidcLoginFailure(new Error("OIDC redirect URI is invalid")),
    { category: "redirect_uri_invalid", browserError: "configuration" },
  );
  assert.deepEqual(
    classifyOidcLoginFailure(new Error("OIDC issuer must use HTTPS")),
    { category: "issuer_invalid", browserError: "configuration" },
  );
  assert.deepEqual(
    classifyOidcLoginFailure(new Error("OIDC redirect URI must use HTTPS")),
    { category: "redirect_uri_invalid", browserError: "configuration" },
  );
  assert.deepEqual(
    classifyOidcLoginFailure(new Error("OIDC_SCOPES must include openid")),
    { category: "scopes_invalid", browserError: "configuration" },
  );
});

test("classifies provider discovery failures separately from local configuration", () => {
  assert.equal(
    classifyOidcLoginFailure(new Error("Identity provider discovery failed")).category,
    "discovery_http_error",
  );
  assert.equal(
    classifyOidcLoginFailure(new TypeError("fetch failed: secret-bearing detail")).category,
    "discovery_unreachable",
  );
  assert.equal(
    classifyOidcLoginFailure(new SyntaxError("raw provider response")).category,
    "discovery_invalid_response",
  );
  assert.equal(
    classifyOidcLoginFailure(new TypeError("Invalid URL")).category,
    "discovery_endpoint_invalid",
  );
  assert.equal(
    classifyOidcLoginFailure(new TypeError("unrelated programming error")).category,
    "internal",
  );
  assert.equal(
    classifyOidcLoginFailure(new Error("Identity provider metadata does not match configured issuer")).category,
    "discovery_issuer_mismatch",
  );
});

test("unexpected failures remain generic to the browser", () => {
  assert.deepEqual(
    classifyOidcLoginFailure(new Error("sensitive internal detail")),
    { category: "internal", browserError: "provider" },
  );
});

test("diagnostic event contains only correlation metadata and an allowlisted category", () => {
  const event = createOidcLoginDiagnostic("request-123", {
    category: "redirect_origin_mismatch",
    browserError: "configuration",
  });
  assert.equal(event.event, "oidc_login_initiation_failed");
  assert.equal(event.request_id, "request-123");
  assert.equal(event.category, "redirect_origin_mismatch");
  assert.equal("message" in event, false);
  assert.equal("stack" in event, false);

  const serialized = JSON.stringify(event);
  assert.equal(serialized.includes("secret-bearing detail"), false);
  assert.deepEqual(Object.keys(event).sort(), ["category", "event", "request_id", "timestamp"]);
});

test("getOidcConfigurationChecks reports booleans only and detects origin mismatch", () => {
  const ok = getOidcConfigurationChecks({
    OIDC_ISSUER: "https://auth.example.com",
    OIDC_CLIENT_ID: "netpay-public",
    OIDC_REDIRECT_URI: "https://netpay.nethub.co.ke/auth/callback/",
    OIDC_TRANSACTION_SECRET: "x".repeat(32),
    OIDC_SCOPES: "openid profile email",
    NEXT_PUBLIC_SITE_URL: "https://netpay.nethub.co.ke",
  });
  assert.equal(isOidcConfigured({
    OIDC_ISSUER: "https://auth.example.com",
    OIDC_CLIENT_ID: "netpay-public",
    OIDC_REDIRECT_URI: "https://netpay.nethub.co.ke/auth/callback/",
    OIDC_TRANSACTION_SECRET: "x".repeat(32),
  }), true);
  assert.deepEqual(ok, {
    issuer_present: true,
    issuer_https: true,
    client_id_present: true,
    redirect_uri_present: true,
    redirect_uri_https: true,
    redirect_origin_matches_site: true,
    transaction_secret_ok: true,
    scopes_ok: true,
  });

  const mismatch = getOidcConfigurationChecks({
    OIDC_ISSUER: "https://auth.example.com",
    OIDC_CLIENT_ID: "netpay-public",
    OIDC_REDIRECT_URI: "https://pay.nethub.co.ke/auth/callback/",
    OIDC_TRANSACTION_SECRET: "short",
    NEXT_PUBLIC_SITE_URL: "https://netpay.nethub.co.ke",
  });
  assert.equal(mismatch.redirect_origin_matches_site, false);
  assert.equal(mismatch.transaction_secret_ok, false);
  assert.equal(mismatch.scopes_ok, true);

  const serialized = JSON.stringify(mismatch);
  assert.equal(serialized.includes("auth.example.com"), false);
  assert.equal(serialized.includes("netpay-public"), false);
  assert.equal(serialized.includes("/auth/callback"), false);
});
