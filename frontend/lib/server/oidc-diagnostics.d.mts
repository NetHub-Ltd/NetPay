export type OidcLoginFailure = {
  category: string;
  browserError: "configuration" | "provider";
};
export function classifyOidcLoginFailure(error: unknown): OidcLoginFailure;
export function createOidcLoginDiagnostic(
  requestId: string,
  failure: OidcLoginFailure,
): {
  event: "oidc_login_initiation_failed";
  request_id: string;
  category: string;
  timestamp: string;
};
