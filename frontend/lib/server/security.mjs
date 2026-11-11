import { Buffer } from "node:buffer";
import { createCipheriv, createDecipheriv, createHash, randomBytes, timingSafeEqual } from "node:crypto";
import { URL } from "node:url";

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
    if ([...searchParams.keys()].some((key) => key !== "limit") || searchParams.getAll("limit").length > 1) return null;
    const raw = searchParams.get("limit") ?? "20";
    if (!/^\d{1,3}$/.test(raw)) return null;
    const limit = Number(raw);
    if (limit < 1 || limit > 100) return null;
    return "/api/v1/auth/merchants/" + payments[1] + "/payments?limit=" + limit;
  }
  return null;
}

/** RFC 7636 S256 challenge for a high-entropy PKCE verifier. */
export function createPkceChallenge(verifier) {
  return createHash("sha256").update(verifier, "ascii").digest("base64url");
}

/** AES-256-GCM protects the short-lived OIDC state/nonce/PKCE transaction cookie. */
export function sealLoginTransaction(value, key) {
  const iv = randomBytes(12);
  const cipher = createCipheriv("aes-256-gcm", key, iv);
  const encrypted = Buffer.concat([cipher.update(JSON.stringify(value), "utf8"), cipher.final()]);
  return [iv, cipher.getAuthTag(), encrypted].map((part) => part.toString("base64url")).join(".");
}

export function openLoginTransaction(value, key, ttlSeconds, nowSeconds) {
  if (typeof value !== "string" || value.length > 4096) return null;
  try {
    const [encodedIv, encodedTag, encodedCiphertext, ...extra] = value.split(".");
    if (!encodedIv || !encodedTag || !encodedCiphertext || extra.length) return null;
    if (![encodedIv, encodedTag, encodedCiphertext].every((part) => /^[A-Za-z0-9_-]+$/.test(part))) return null;
    const iv = Buffer.from(encodedIv, "base64url");
    const tag = Buffer.from(encodedTag, "base64url");
    const ciphertext = Buffer.from(encodedCiphertext, "base64url");
    if (
      iv.length !== 12 || tag.length !== 16 || ciphertext.length === 0 ||
      iv.toString("base64url") !== encodedIv ||
      tag.toString("base64url") !== encodedTag ||
      ciphertext.toString("base64url") !== encodedCiphertext
    ) return null;
    const decipher = createDecipheriv("aes-256-gcm", key, iv);
    decipher.setAuthTag(tag);
    const plaintext = Buffer.concat([decipher.update(ciphertext), decipher.final()]).toString("utf8");
    const parsed = JSON.parse(plaintext);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return null;
    const tx = parsed;
    const age = nowSeconds - tx.issuedAt;
    if (
      typeof tx.state !== "string" || !/^[A-Za-z0-9_-]{40,60}$/.test(tx.state) ||
      typeof tx.nonce !== "string" || !/^[A-Za-z0-9_-]{40,60}$/.test(tx.nonce) ||
      typeof tx.verifier !== "string" || !/^[A-Za-z0-9._~-]{43,128}$/.test(tx.verifier) ||
      typeof tx.returnTo !== "string" || !tx.returnTo.startsWith("/") ||
      tx.returnTo.startsWith("//") || tx.returnTo.includes("\\") ||
      !Number.isSafeInteger(tx.issuedAt) || age < 0 || age > ttlSeconds
    ) return null;
    return tx;
  } catch {
    return null;
  }
}


/** Build a public OIDC token request. PKCE, not a client secret, binds the code exchange. */
export function createPublicClientTokenRequest(clientId, parameters) {
  if (typeof clientId !== "string" || !clientId.trim()) {
    throw new Error("OIDC client ID is required");
  }
  const body = new URLSearchParams(parameters);
  if (body.has("client_secret")) {
    throw new Error("Public OIDC token requests must not include a client secret");
  }
  const suppliedClientId = body.get("client_id");
  if (suppliedClientId && suppliedClientId !== clientId.trim()) {
    throw new Error("OIDC token request client ID does not match configuration");
  }
  body.set("client_id", clientId.trim());
  return {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      Accept: "application/json",
    },
    body,
  };
}

/** Validate the server-only settings needed to create and protect an OIDC transaction. */
export function isOidcConfigured(environment) {
  const required = ["OIDC_ISSUER", "OIDC_CLIENT_ID", "OIDC_REDIRECT_URI"];
  return required.every((name) =>
    typeof environment[name] === "string" && environment[name].trim().length > 0
  ) &&
    typeof environment.OIDC_TRANSACTION_SECRET === "string" &&
    environment.OIDC_TRANSACTION_SECRET.trim().length >= 32;
}
