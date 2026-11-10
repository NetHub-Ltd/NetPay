import assert from "node:assert/strict";
import test from "node:test";
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
    resolveAllowedGet(["v1", "auth", "merchants", "not-a-uuid"], new URLSearchParams()),
    null,
  );
});
