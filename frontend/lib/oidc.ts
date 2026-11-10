/** Public-client OIDC authorization code + PKCE (no client secret). */

import { loadSpaConfig, apiBase } from "./config";
import { setPkcePair, takePkcePair, setAccessToken, clearSession } from "./session";

function b64url(bytes: ArrayBuffer | Uint8Array): string {
  const arr = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
  let s = "";
  arr.forEach((b) => {
    s += String.fromCharCode(b);
  });
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function randomString(length = 64): string {
  const bytes = new Uint8Array(length);
  crypto.getRandomValues(bytes);
  return b64url(bytes);
}

async function sha256(input: string): Promise<ArrayBuffer> {
  return crypto.subtle.digest("SHA-256", new TextEncoder().encode(input));
}

export async function startLogin(): Promise<void> {
  const cfg = await loadSpaConfig();
  if (!cfg.oidc_configured) {
    throw new Error("OIDC is not configured on this NetPay deployment");
  }
  const verifier = randomString(64);
  const state = randomString(32);
  const challenge = b64url(await sha256(verifier));
  setPkcePair(verifier, state);

  const params = new URLSearchParams({
    response_type: "code",
    client_id: cfg.oidc_client_id,
    redirect_uri: cfg.oidc_redirect_uri,
    scope: cfg.oidc_scopes,
    state,
    code_challenge: challenge,
    code_challenge_method: "S256",
  });

  let authorize = `${cfg.oidc_issuer}/oauth/v2/authorize`;
  try {
    const disc = await fetch(`${cfg.oidc_issuer}/.well-known/openid-configuration`, {
      cache: "no-store",
    });
    if (disc.ok) {
      const body = (await disc.json()) as { authorization_endpoint?: string };
      if (body.authorization_endpoint) authorize = body.authorization_endpoint;
    }
  } catch {
    /* use Zitadel-style default */
  }

  window.location.assign(`${authorize}?${params.toString()}`);
}

export async function completeLoginFromCallback(url: string): Promise<void> {
  const cfg = await loadSpaConfig();
  const u = new URL(url);
  const err = u.searchParams.get("error");
  if (err) {
    throw new Error(u.searchParams.get("error_description") || err);
  }
  const code = u.searchParams.get("code");
  const state = u.searchParams.get("state");
  if (!code || !state) {
    throw new Error("Missing authorization code");
  }
  const { verifier, state: expected } = takePkcePair();
  if (!verifier || !expected || expected !== state) {
    throw new Error("Invalid login state — start sign-in again");
  }

  let tokenEndpoint = `${cfg.oidc_issuer}/oauth/v2/token`;
  try {
    const disc = await fetch(`${cfg.oidc_issuer}/.well-known/openid-configuration`, {
      cache: "no-store",
    });
    if (disc.ok) {
      const body = (await disc.json()) as { token_endpoint?: string };
      if (body.token_endpoint) tokenEndpoint = body.token_endpoint;
    }
  } catch {
    /* default */
  }

  const body = new URLSearchParams({
    grant_type: "authorization_code",
    code,
    redirect_uri: cfg.oidc_redirect_uri,
    client_id: cfg.oidc_client_id,
    code_verifier: verifier,
  });

  const res = await fetch(tokenEndpoint, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded", Accept: "application/json" },
    body,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Token exchange failed");
  }
  // Access token only — refresh tokens are not stored until I7 BFF (D1: no offline_access by default).
  const tokens = (await res.json()) as { access_token?: string };
  if (!tokens.access_token) {
    throw new Error("Token response missing access_token");
  }
  setAccessToken(tokens.access_token);
}

export type AuthMe = {
  id: string;
  email: string;
  full_name: string;
  username: string;
  is_active: boolean;
  is_admin: boolean;
  tenant_id: string | null;
  auth_type: string;
};

export type Membership = {
  merchant_id: string;
  role: string;
  merchant_name: string | null;
  merchant_slug: string | null;
};

/** Thrown for /api/v1/auth/* failures; status 401 clears the browser session. */
export class AuthApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "AuthApiError";
    this.status = status;
  }
}

async function authFetch(path: string, accessToken: string): Promise<Response> {
  const base = apiBase();
  return fetch(`${base}${path}`, {
    headers: { Authorization: `Bearer ${accessToken}`, Accept: "application/json" },
    cache: "no-store",
  });
}

export async function fetchAuthMe(accessToken: string): Promise<AuthMe> {
  const res = await authFetch("/api/v1/auth/me", accessToken);
  if (res.status === 401) {
    clearSession();
    throw new AuthApiError(401, "Session expired — sign in again");
  }
  if (!res.ok) {
    const text = await res.text();
    throw new AuthApiError(res.status, text || `auth/me failed (${res.status})`);
  }
  return res.json() as Promise<AuthMe>;
}

export async function fetchMemberships(accessToken: string): Promise<Membership[]> {
  const res = await authFetch("/api/v1/auth/memberships", accessToken);
  if (res.status === 401) {
    clearSession();
    throw new AuthApiError(401, "Session expired — sign in again");
  }
  if (!res.ok) {
    const text = await res.text();
    throw new AuthApiError(res.status, text || `memberships failed (${res.status})`);
  }
  return res.json() as Promise<Membership[]>;
}


export type MerchantSummary = {
  id: string;
  name: string;
  slug: string;
  status: string;
  default_currency: string;
  role: string;
};

export type HumanPayment = {
  id: string;
  merchant_reference: string;
  amount_minor: number;
  currency: string;
  status: string;
  payment_source: string;
  phone_number: string | null;
  initiated_at: string | null;
  completed_at: string | null;
  created_at: string | null;
};

export async function fetchMerchantSummary(
  accessToken: string,
  merchantId: string,
): Promise<MerchantSummary> {
  const res = await authFetch(`/api/v1/auth/merchants/${merchantId}`, accessToken);
  if (res.status === 401) {
    clearSession();
    throw new AuthApiError(401, "Session expired — sign in again");
  }
  if (res.status === 403) {
    throw new AuthApiError(403, "Merchant membership required");
  }
  if (!res.ok) {
    const text = await res.text();
    throw new AuthApiError(res.status, text || `merchant summary failed (${res.status})`);
  }
  return res.json() as Promise<MerchantSummary>;
}

export async function fetchMerchantPayments(
  accessToken: string,
  merchantId: string,
  limit = 20,
): Promise<HumanPayment[]> {
  const res = await authFetch(
    `/api/v1/auth/merchants/${merchantId}/payments?limit=${limit}`,
    accessToken,
  );
  if (res.status === 401) {
    clearSession();
    throw new AuthApiError(401, "Session expired — sign in again");
  }
  if (res.status === 403) {
    throw new AuthApiError(403, "Merchant membership required");
  }
  if (!res.ok) {
    const text = await res.text();
    throw new AuthApiError(res.status, text || `merchant payments failed (${res.status})`);
  }
  return res.json() as Promise<HumanPayment[]>;
}
