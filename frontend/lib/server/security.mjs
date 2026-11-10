import { timingSafeEqual } from "node:crypto";

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const SESSION_HANDLE = /^[A-Za-z0-9_-]{40,60}$/;

export function safeReturnTo(value, origin) {
  if (
    typeof value !== "string" ||
    !value.startsWith("/") ||
    value.startsWith("//") ||
    value.includes("\\") ||
    /%5c/i.test(value)
  ) return "/dashboard/";
  try {
    const parsed = new URL(value, origin);
    return parsed.origin === origin
      ? parsed.pathname + parsed.search + parsed.hash
      : "/dashboard/";
  } catch {
    return "/dashboard/";
  }
}

export function constantTimeEqual(left, right) {
  if (typeof left !== "string" || typeof right !== "string") return false;
  const a = Buffer.from(left);
  const b = Buffer.from(right);
  return a.length === b.length && timingSafeEqual(a, b);
}

export function isValidSessionHandle(value) {
  return typeof value === "string" && SESSION_HANDLE.test(value);
}

export function isSameOriginRequest(origin, requestOrigin, secFetchSite) {
  return typeof origin === "string" &&
    origin === requestOrigin &&
    secFetchSite !== "cross-site";
}

/** Explicit human dashboard GET allowlist. No caller-controlled upstream URL is accepted. */
export function resolveAllowedGet(path, searchParams) {
  const route = path.join("/");
  if (route === "v1/auth/me" || route === "v1/auth/memberships") {
    if ([...searchParams.keys()].length) return null;
    return "/api/" + route;
  }

  const merchant = route.match(/^v1\/auth\/merchants\/([^/]+)$/);
  if (merchant && UUID.test(merchant[1]) && [...searchParams.keys()].length === 0) {
    return "/api/v1/auth/merchants/" + merchant[1];
  }

  const payments = route.match(/^v1\/auth\/merchants\/([^/]+)\/payments$/);
  if (payments && UUID.test(payments[1])) {
    if ([...searchParams.keys()].some((key) => key !== "limit")) return null;
    const raw = searchParams.get("limit") ?? "20";
    if (!/^\d{1,3}$/.test(raw)) return null;
    const limit = Number(raw);
    if (limit < 1 || limit > 100) return null;
    return "/api/v1/auth/merchants/" + payments[1] + "/payments?limit=" + limit;
  }
  return null;
}
