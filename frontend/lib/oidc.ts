/** Browser API client: authenticated requests are same-origin BFF calls. */
export type AuthMe = {
  id: string; email: string; full_name: string; username: string;
  is_active: boolean; is_admin: boolean; tenant_id: string | null; auth_type: string;
};
export type Membership = {
  merchant_id: string; role: string; merchant_name: string | null; merchant_slug: string | null;
};
export type MerchantSummary = {
  id: string; name: string; slug: string; status: string; default_currency: string; role: string;
};
export type HumanPayment = {
  id: string; merchant_reference: string; amount_minor: number; currency: string;
  status: string; payment_source: string; phone_number: string | null;
  initiated_at: string | null; completed_at: string | null; created_at: string | null;
};
export class AuthApiError extends Error {
  readonly status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = "AuthApiError";
    this.status = status;
  }
}
async function authFetch<T>(path: string): Promise<T> {
  const response = await fetch("/api/backend" + path, {
    headers: { Accept: "application/json" }, credentials: "same-origin", cache: "no-store",
  });
  if (response.status === 401) throw new AuthApiError(401, "Session expired — sign in again");
  if (response.status === 403) throw new AuthApiError(403, "You do not have permission to access this merchant");
  if (!response.ok) {
    let detail = "Request failed (" + response.status + ")";
    try {
      const body = await response.json() as { detail?: unknown };
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      // Keep a safe status-based message when the response is not JSON.
    }
    throw new AuthApiError(response.status, detail);
  }
  return await response.json() as T;
}
export function startLogin(): void {
  window.location.assign("/api/auth/login?returnTo=%2Fdashboard%2F");
}
export async function clearSession(): Promise<void> {
  const response = await fetch("/api/auth/logout", {
    method: "POST", credentials: "same-origin",
    headers: { "X-NetPay-Logout": "1" }, cache: "no-store",
  });
  if (!response.ok) throw new Error("Could not sign out. Please retry.");
}
export function fetchAuthMe(): Promise<AuthMe> {
  return authFetch<AuthMe>("/v1/auth/me");
}
export function fetchMemberships(): Promise<Membership[]> {
  return authFetch<Membership[]>("/v1/auth/memberships");
}
export function fetchMerchantSummary(merchantId: string): Promise<MerchantSummary> {
  return authFetch<MerchantSummary>("/v1/auth/merchants/" + encodeURIComponent(merchantId));
}
export function fetchMerchantPayments(merchantId: string, limit = 20): Promise<HumanPayment[]> {
  return authFetch<HumanPayment>(
    "/v1/auth/merchants/" + encodeURIComponent(merchantId) + "/payments?limit=" + limit,
  );
}
