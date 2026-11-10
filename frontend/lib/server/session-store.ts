import "server-only";

import { cookies } from "next/headers";
import { createHash, randomBytes } from "node:crypto";
import { refreshOidcTokens, type OidcTokens } from "./oidc";

export const SESSION_MAX_AGE_SECONDS = 8 * 60 * 60;
export const SESSION_COOKIE_NAME =
  process.env.NODE_ENV === "production" ? "__Host-netpay_session" : "netpay_session";
export type StoredSession = {
  access_token: string; refresh_token: string | null;
  access_expires_at: string; expires_at: string;
};
function requiredEnv(name: string): string {
  const value = process.env[name]?.trim();
  if (!value) throw new Error("Missing required server configuration: " + name);
  return value;
}
function hashSessionId(value: string): string {
  return createHash("sha256").update(value, "utf8").digest("hex");
}
async function storeRequest(path: string, init: RequestInit = {}): Promise<Response> {
  const base = requiredEnv("NETPAY_BACKEND_INTERNAL_URL").replace(/\/+$/, "");
  return fetch(base + "/internal/v1/bff/sessions" + path, {
    ...init,
    headers: {
      Accept: "application/json", "Content-Type": "application/json",
      "X-NetPay-BFF-Secret": requiredEnv("BFF_INTERNAL_SECRET"), ...init.headers,
    },
    cache: "no-store", signal: init.signal ?? AbortSignal.timeout(7_000),
  });
}
async function readStoredSession(sessionId: string): Promise<StoredSession | null> {
  const response = await storeRequest("/" + hashSessionId(sessionId));
  if (response.status === 404) return null;
  if (!response.ok) throw new Error("NetPay session store is unavailable");
  return await response.json() as StoredSession;
}
export async function createServerSession(tokens: OidcTokens): Promise<string> {
  const sessionId = randomBytes(32).toString("base64url");
  const now = Date.now();
  const response = await storeRequest("", {
    method: "POST",
    body: JSON.stringify({
      session_id_hash: hashSessionId(sessionId),
      access_token: tokens.access_token,
      refresh_token: tokens.refresh_token ?? null,
      access_expires_at: new Date(now + tokens.expires_in * 1000).toISOString(),
      expires_at: new Date(now + SESSION_MAX_AGE_SECONDS * 1000).toISOString(),
    }),
  });
  if (!response.ok) throw new Error("Could not establish the NetPay session");
  return sessionId;
}
export async function revokeServerSession(sessionId: string): Promise<void> {
  const response = await storeRequest("/" + hashSessionId(sessionId), { method: "DELETE" });
  if (!response.ok && response.status !== 404) throw new Error("Could not invalidate the NetPay session");
}
async function updateStoredSession(
  sessionId: string, tokens: OidcTokens, current: StoredSession,
): Promise<StoredSession> {
  const accessExpiresAt = new Date(Date.now() + tokens.expires_in * 1000);
  const refreshToken = tokens.refresh_token ?? current.refresh_token;
  const response = await storeRequest("/" + hashSessionId(sessionId), {
    method: "PATCH",
    body: JSON.stringify({
      access_token: tokens.access_token, refresh_token: refreshToken,
      access_expires_at: accessExpiresAt.toISOString(), expires_at: current.expires_at,
    }),
  });
  if (!response.ok) throw new Error("Could not rotate the NetPay session");
  return {
    access_token: tokens.access_token, refresh_token: refreshToken,
    access_expires_at: accessExpiresAt.toISOString(), expires_at: current.expires_at,
  };
}
export async function getActiveSession(sessionId: string): Promise<StoredSession | null> {
  let current = await readStoredSession(sessionId);
  if (!current) return null;
  const now = Date.now();
  if (Date.parse(current.expires_at) <= now) {
    await revokeServerSession(sessionId);
    return null;
  }
  if (Date.parse(current.access_expires_at) > now + 60_000) return current;
  if (!current.refresh_token) {
    await revokeServerSession(sessionId);
    return null;
  }
  try {
    const rotated = await refreshOidcTokens(current.refresh_token);
    current = await updateStoredSession(sessionId, rotated, current);
    return current;
  } catch {
    await revokeServerSession(sessionId);
    return null;
  }
}
export async function getSessionFromRequest(request: Request): Promise<{
  sessionId: string; session: StoredSession;
} | null> {
  const cookieHeader = request.headers.get("cookie") ?? "";
  const cookiePart = cookieHeader.split(";").map((part) => part.trim())
    .find((part) => part.startsWith(SESSION_COOKIE_NAME + "="));
  const sessionId = cookiePart ? decodeURIComponent(cookiePart.slice(SESSION_COOKIE_NAME.length + 1)) : null;
  if (!sessionId || !/^[A-Za-z0-9_-]{40,60}$/.test(sessionId)) return null;
  const session = await getActiveSession(sessionId);
  return session ? { sessionId, session } : null;
}
export async function getCurrentSession(): Promise<{
  sessionId: string; session: StoredSession;
} | null> {
  const jar = await cookies();
  const sessionId = jar.get(SESSION_COOKIE_NAME)?.value;
  if (!sessionId || !/^[A-Za-z0-9_-]{40,60}$/.test(sessionId)) return null;
  const session = await getActiveSession(sessionId);
  return session ? { sessionId, session } : null;
}
export function sessionCookieOptions() {
  return {
    httpOnly: true, secure: process.env.NODE_ENV === "production",
    sameSite: "lax" as const, path: "/", maxAge: SESSION_MAX_AGE_SECONDS,
  };
}
export function expiredSessionCookieOptions() {
  return {
    httpOnly: true, secure: process.env.NODE_ENV === "production",
    sameSite: "lax" as const, path: "/", maxAge: 0,
  };
}
export async function validateHumanAccessToken(accessToken: string): Promise<void> {
  const base = requiredEnv("NETPAY_BACKEND_INTERNAL_URL").replace(/\/+$/, "");
  const response = await fetch(base + "/api/v1/auth/me", {
    headers: { Authorization: "Bearer " + accessToken, Accept: "application/json" },
    cache: "no-store", signal: AbortSignal.timeout(8_000),
  });
  if (!response.ok) throw new Error("NetPay could not resolve the authenticated NetHub identity");
}
