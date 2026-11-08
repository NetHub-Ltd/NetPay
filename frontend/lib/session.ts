/** Browser session for IdP access token — never store client secrets. */

const ACCESS_KEY = "netpay_idp_access_token";
const VERIFIER_KEY = "netpay_oidc_code_verifier";
const STATE_KEY = "netpay_oidc_state";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return sessionStorage.getItem(ACCESS_KEY);
  } catch {
    return null;
  }
}

export function setAccessToken(token: string | null): void {
  if (typeof window === "undefined") return;
  try {
    if (token) sessionStorage.setItem(ACCESS_KEY, token);
    else sessionStorage.removeItem(ACCESS_KEY);
  } catch {
    /* private mode */
  }
}

export function setPkcePair(verifier: string, state: string): void {
  sessionStorage.setItem(VERIFIER_KEY, verifier);
  sessionStorage.setItem(STATE_KEY, state);
}

export function takePkcePair(): { verifier: string | null; state: string | null } {
  const verifier = sessionStorage.getItem(VERIFIER_KEY);
  const state = sessionStorage.getItem(STATE_KEY);
  sessionStorage.removeItem(VERIFIER_KEY);
  sessionStorage.removeItem(STATE_KEY);
  return { verifier, state };
}

export function clearSession(): void {
  setAccessToken(null);
  try {
    sessionStorage.removeItem(VERIFIER_KEY);
    sessionStorage.removeItem(STATE_KEY);
  } catch {
    /* ignore */
  }
}
