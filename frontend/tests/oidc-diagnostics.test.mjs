import assert from "node:assert/strict";
import test from "node:test";
import {
  classifyOidcLoginFailure,
  createOidcLoginDiagnostic,
} from "../lib/server/oidc-diagnostics.mjs";

test("classifies missing configuration without exposing the missing value", () => {
  const result = classifyOidcLoginFailure(
    new Error("Missing required server configuration: OIDC_CLIENT_ID"),
  );
  assert.deepEqual(result, { category: "configuration", browserError: "configuration" });
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
    category: "discovery_unreachable",
    browserError: "provider",
  });
  assert.equal(event.event, "oidc_login_initiation_failed");
  assert.equal(event.request_id, "request-123");
  assert.equal(event.category, "discovery_unreachable");
  assert.equal("message" in event, false);
  assert.equal("stack" in event, false);
  assert.equal("secret-bearing detail" in JSON.stringify(event), false);
});
