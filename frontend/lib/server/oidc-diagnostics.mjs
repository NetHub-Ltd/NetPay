/** Safe OIDC login-initiation diagnostics. Never return or log raw exception content. */
const CONFIGURATION_MESSAGES = new Set([
  "OIDC issuer URL is invalid",
  "OIDC redirect URI is invalid",
  "OIDC issuer must use HTTPS",
  "OIDC redirect URI must use HTTPS",
  "OIDC redirect origin must match NetPay",
  "OIDC_TRANSACTION_SECRET must contain at least 32 characters",
]);

export function classifyOidcLoginFailure(error) {
  const message = error instanceof Error ? error.message : "";
  if (
    message.startsWith("Missing required server configuration:") ||
    CONFIGURATION_MESSAGES.has(message) ||
    message === "OIDC_SCOPES must include openid"
  ) {
    return { category: "configuration", browserError: "configuration" };
  }
  if (message === "Identity provider discovery failed") {
    return { category: "discovery_http_error", browserError: "provider" };
  }
  if (message === "Identity provider metadata is invalid" || error instanceof SyntaxError) {
    return { category: "discovery_invalid_response", browserError: "provider" };
  }
  if (message === "Identity provider metadata does not match configured issuer") {
    return { category: "discovery_issuer_mismatch", browserError: "provider" };
  }
  if (message === "Identity provider endpoint is not trusted" || message === "Invalid URL") {
    return { category: "discovery_endpoint_invalid", browserError: "provider" };
  }
  if (
    (error instanceof TypeError && /fetch failed|network/i.test(message)) ||
    (error instanceof Error && ["AbortError", "TimeoutError"].includes(error.name))
  ) {
    return { category: "discovery_unreachable", browserError: "provider" };
  }
  return { category: "internal", browserError: "provider" };
}

/** A deliberately small allowlisted event; exception messages and stack traces are excluded. */
export function createOidcLoginDiagnostic(requestId, failure) {
  return {
    event: "oidc_login_initiation_failed",
    request_id: requestId,
    category: failure.category,
    timestamp: new Date().toISOString(),
  };
}
