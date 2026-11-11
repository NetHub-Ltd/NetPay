import assert from "node:assert/strict";
import test from "node:test";
import { URLSearchParams } from "node:url";
import {
  constantTimeEqual,
  isSameOriginRequest,
  isValidSessionHandle,
  resolveAllowedGet,
  safeReturnTo,
} from "../lib/server/security.mjs";

const origin = "https://pay.example.test";
const merchantId = "123e4567-e89b-42d3-a456-426614174000";

test("return destinations accept local paths and reject external or ambiguous targets", () => {
  assert.equal(safeReturnTo("/dashboard/?tab=payments", origin), "/dashboard/?tab=payments");
  assert.equal(safeReturnTo("https://evil.example", origin), "/dashboard/");
  assert.equal(safeReturnTo("//evil.example/path", origin), "/dashboard/");
  assert.equal(safeReturnTo("/\\evil.example", origin), "/dashboard/");
  assert.equal(safeReturnTo("/%5C%5Cevil.example", origin), "/dashboard/");
  assert.equal(safeReturnTo(null, origin), "/dashboard/");
});

test("OIDC state comparison is exact and constant-time for equal-length strings", () => {
  assert.equal(constantTimeEqual("same-state", "same-state"), true);
  assert.equal(constantTimeEqual("same-state", "other-state"), false);
  assert.equal(constantTimeEqual("short", "longer"), false);
});

test("session handles must have the expected opaque base64url shape", () => {
  assert.equal(isValidSessionHandle("a".repeat(43)), true);
  assert.equal(isValidSessionHandle("not-a-session"), false);
  assert.equal(isValidSessionHandle("a".repeat(300)), false);
});

test("logout requires same-origin request metadata", () => {
  assert.equal(isSameOriginRequest(origin, origin, "same-origin"), true);
  assert.equal(isSameOriginRequest("https://evil.example", origin, "cross-site"), false);
  assert.equal(isSameOriginRequest(null, origin, "same-origin"), false);
  assert.equal(isSameOriginRequest(origin, origin, "cross-site"), false);
});

test("BFF exposes only the explicit dashboard GET routes and bounded query values", () => {
  assert.equal(resolveAllowedGet(["v1", "auth", "me"], new URLSearchParams()), "/api/v1/auth/me");
  assert.equal(resolveAllowedGet(["v1", "auth", "memberships"], new URLSearchParams()), "/api/v1/auth/memberships");
  assert.equal(
    resolveAllowedGet(["v1", "auth", "merchants", merchantId], new URLSearchParams()),
    "/api/v1/auth/merchants/" + merchantId,
  );
  assert.equal(
    resolveAllowedGet(["v1", "auth", "merchants", merchantId, "payments"], new URLSearchParams("limit=100")),
    "/api/v1/auth/merchants/" + merchantId + "/payments?limit=100",
  );
  assert.equal(resolveAllowedGet(["v1", "payments", "all"], new URLSearchParams()), null);
  assert.equal(
    resolveAllowedGet(["v1", "auth", "merchants", merchantId, "payments"], new URLSearchParams("limit=101")),
    null,
  );
  assert.equal(
    resolveAllowedGet(["v1", "auth", "merchants", merchantId, "payments"], new URLSearchParams("limit=5&url=https://evil.example")),
    null,
  );
  assert.equal(
    resolveAllowedGet(["v1", "auth", "merchants", merchantId, "payments"], new URLSearchParams("limit=5&limit=10")),
    null,
  );
  assert.equal(
    resolveAllowedGet(["v1", "auth", "merchants", "not-a-uuid"], new URLSearchParams()),
    null,
  );
});

import { createHash, randomBytes } from "node:crypto";
import {
  createPkceChallenge,
  createPublicClientTokenRequest,
  isOidcConfigured,
  openLoginTransaction,
  sealLoginTransaction,
} from "../lib/server/security.mjs";

test("PKCE S256 challenge matches the RFC 7636 SHA-256 base64url construction", () => {
  const verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk";
  const expected = createHash("sha256").update(verifier, "ascii").digest("base64url");
  assert.equal(createPkceChallenge(verifier), expected);
});

test("OIDC transaction cookie is encrypted, authenticated and expires", () => {
  const key = randomBytes(32);
  const tx = {
    state: randomBytes(32).toString("base64url"),
    nonce: randomBytes(32).toString("base64url"),
    verifier: randomBytes(48).toString("base64url"),
    returnTo: "/dashboard/",
    issuedAt: 1_800_000_000,
  };
  const sealed = sealLoginTransaction(tx, key);
  assert.equal(sealed.includes(tx.verifier), false);
  assert.deepEqual(openLoginTransaction(sealed, key, 600, tx.issuedAt + 1), tx);
  assert.equal(openLoginTransaction(sealed + "x", key, 600, tx.issuedAt + 1), null);
  assert.equal(openLoginTransaction(sealed, key, 600, tx.issuedAt + 601), null);
  assert.equal(openLoginTransaction(sealed, randomBytes(32), 600, tx.issuedAt + 1), null);
});


test("public OIDC authorization-code exchange uses client_id and PKCE without client authentication secret", () => {
  const request = createPublicClientTokenRequest("netpay-public-client", new URLSearchParams({
    grant_type: "authorization_code",
    code: "authorization-code",
    redirect_uri: "https://pay.example.test/auth/callback/",
    code_verifier: "a".repeat(64),
  }));
  assert.equal(request.body.get("client_id"), "netpay-public-client");
  assert.equal(request.body.get("grant_type"), "authorization_code");
  assert.equal(request.body.get("code_verifier"), "a".repeat(64));
  assert.equal(request.body.get("redirect_uri"), "https://pay.example.test/auth/callback/");
  assert.equal(request.body.has("client_secret"), false);
  assert.equal(request.headers.Authorization, undefined);
  assert.equal(request.headers["Content-Type"], "application/x-www-form-urlencoded");
});

test("public OIDC refresh-token exchange includes client_id and never sends a client secret", () => {
  const request = createPublicClientTokenRequest("netpay-public-client", new URLSearchParams({
    grant_type: "refresh_token",
    refresh_token: "refresh-token-value",
  }));
  assert.equal(request.body.get("client_id"), "netpay-public-client");
  assert.equal(request.body.get("grant_type"), "refresh_token");
  assert.equal(request.body.get("refresh_token"), "refresh-token-value");
  assert.equal(request.body.has("client_secret"), false);
  assert.equal(request.headers.Authorization, undefined);
});

test("public OIDC token request rejects an accidental client_secret or mismatched client_id", () => {
  assert.throws(() => createPublicClientTokenRequest("netpay-public-client", new URLSearchParams({
    grant_type: "authorization_code", client_secret: "must-not-exist",
  })), /must not include a client secret/);
  assert.throws(() => createPublicClientTokenRequest("netpay-public-client", new URLSearchParams({
    grant_type: "authorization_code", client_id: "another-client",
  })), /does not match configuration/);
});

test("OIDC readiness requires public-client settings and the encrypted transaction secret, not a client secret", () => {
  const environment = {
    OIDC_ISSUER: "https://auth.example.test",
    OIDC_CLIENT_ID: "netpay-public-client",
    OIDC_REDIRECT_URI: "https://pay.example.test/auth/callback/",
    OIDC_TRANSACTION_SECRET: "t".repeat(32),
  };
  assert.equal(isOidcConfigured(environment), true);
  assert.equal(isOidcConfigured({ ...environment, OIDC_TRANSACTION_SECRET: "short" }), false);
  assert.equal(isOidcConfigured({ ...environment, OIDC_CLIENT_ID: "" }), false);
});
