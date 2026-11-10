import {
  createCipheriv, createDecipheriv, createHash, createPublicKey, createVerify,
  randomBytes, timingSafeEqual,
} from "node:crypto";

export const OIDC_TRANSACTION_COOKIE = "netpay_oidc_transaction";
export const OIDC_TRANSACTION_TTL_SECONDS = 600;
export type OidcTokens = {
  access_token: string; refresh_token?: string; id_token: string; expires_in: number;
};
export type LoginTransaction = {
  state: string; nonce: string; verifier: string; returnTo: string; issuedAt: number;
};
type OidcMetadata = {
  issuer: string; authorization_endpoint: string; token_endpoint: string; jwks_uri: string;
};
type JwtClaims = {
  iss?: string; aud?: string | string[]; azp?: string; sub?: string;
  exp?: number; iat?: number; nonce?: string;
};
type TokenResponse = {
  access_token?: unknown; refresh_token?: unknown; id_token?: unknown; expires_in?: unknown;
};
let metadataCache: { expiresAt: number; value: OidcMetadata } | null = null;
let jwksCache: { expiresAt: number; keys: JsonWebKey[] } | null = null;

function requiredEnv(name: string): string {
  const value = process.env[name]?.trim();
  if (!value) throw new Error("Missing required server configuration: " + name);
  return value;
}
function configuredIssuer(): string {
  const url = new URL(requiredEnv("OIDC_ISSUER"));
  if (url.username || url.password || url.search || url.hash) throw new Error("OIDC issuer URL is invalid");
  if (process.env.NODE_ENV === "production" && url.protocol !== "https:") throw new Error("OIDC issuer must use HTTPS");
  return url.toString().replace(/\/+$/, "");
}
export function configuredRedirectUri(): string {
  const url = new URL(requiredEnv("OIDC_REDIRECT_URI"));
  if (url.username || url.password || url.hash) throw new Error("OIDC redirect URI is invalid");
  if (process.env.NODE_ENV === "production" && url.protocol !== "https:") throw new Error("OIDC redirect URI must use HTTPS");
  return url.toString();
}
async function getMetadata(): Promise<OidcMetadata> {
  const now = Date.now();
  if (metadataCache && metadataCache.expiresAt > now) return metadataCache.value;
  const issuer = configuredIssuer();
  const response = await fetch(issuer + "/.well-known/openid-configuration", {
    cache: "no-store", signal: AbortSignal.timeout(8_000),
  });
  if (!response.ok) throw new Error("Identity provider discovery failed");
  const body: unknown = await response.json();
  if (!body || typeof body !== "object") throw new Error("Identity provider metadata is invalid");
  const data = body as Record<string, unknown>;
  const metadataIssuer = typeof data.issuer === "string" ? data.issuer.replace(/\/+$/, "") : "";
  const authorization = typeof data.authorization_endpoint === "string" ? data.authorization_endpoint : "";
  const token = typeof data.token_endpoint === "string" ? data.token_endpoint : "";
  const jwks = typeof data.jwks_uri === "string" ? data.jwks_uri : "";
  if (metadataIssuer !== issuer || !authorization || !token || !jwks) {
    throw new Error("Identity provider metadata does not match configured issuer");
  }
  for (const endpoint of [authorization, token, jwks]) {
    const url = new URL(endpoint);
    if (url.username || url.password || (process.env.NODE_ENV === "production" && url.protocol !== "https:")) {
      throw new Error("Identity provider endpoint is not trusted");
    }
  }
  const value = { issuer, authorization_endpoint: authorization, token_endpoint: token, jwks_uri: jwks };
  metadataCache = { value, expiresAt: now + 300_000 };
  return value;
}
function transactionKey(): Buffer {
  const secret = requiredEnv("OIDC_TRANSACTION_SECRET");
  if (secret.length < 32) throw new Error("OIDC_TRANSACTION_SECRET must contain at least 32 characters");
  return createHash("sha256").update(secret, "utf8").digest();
}
function randomValue(bytes = 32): string {
  return randomBytes(bytes).toString("base64url");
}
/** Encrypt the short-lived transaction so the PKCE verifier is not readable in the cookie. */
export function sealTransaction(value: LoginTransaction): string {
  const iv = randomBytes(12);
  const cipher = createCipheriv("aes-256-gcm", transactionKey(), iv);
  const encrypted = Buffer.concat([cipher.update(JSON.stringify(value), "utf8"), cipher.final()]);
  return [iv, cipher.getAuthTag(), encrypted].map((part) => part.toString("base64url")).join(".");
}
export function openTransaction(value: string | undefined): LoginTransaction | null {
  if (!value) return null;
  try {
    const [iv, tag, ciphertext] = value.split(".");
    if (!iv || !tag || !ciphertext) return null;
    const decipher = createDecipheriv("aes-256-gcm", transactionKey(), Buffer.from(iv, "base64url"));
    decipher.setAuthTag(Buffer.from(tag, "base64url"));
    const raw = Buffer.concat([
      decipher.update(Buffer.from(ciphertext, "base64url")), decipher.final(),
    ]).toString("utf8");
    const parsed: unknown = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object") return null;
    const tx = parsed as LoginTransaction;
    const age = Math.floor(Date.now() / 1000) - tx.issuedAt;
    if (
      typeof tx.state !== "string" || typeof tx.nonce !== "string" ||
      typeof tx.verifier !== "string" || typeof tx.returnTo !== "string" ||
      !Number.isInteger(tx.issuedAt) || age < 0 || age > OIDC_TRANSACTION_TTL_SECONDS
    ) return null;
    return tx;
  } catch {
    return null;
  }
}
export async function createAuthorizationRequest(
  origin: string, returnTo: string,
): Promise<{ url: string; transactionCookie: string }> {
  const redirectUri = configuredRedirectUri();
  if (new URL(redirectUri).origin !== origin) throw new Error("OIDC redirect origin must match NetPay");
  const metadata = await getMetadata();
  const verifier = randomValue(48);
  const state = randomValue();
  const nonce = randomValue();
  const challenge = createHash("sha256").update(verifier).digest("base64url");
  const scopes = (process.env.OIDC_SCOPES || "openid profile email").trim();
  if (!scopes.split(/\s+/).includes("openid")) throw new Error("OIDC_SCOPES must include openid");
  const params = new URLSearchParams({
    response_type: "code", client_id: requiredEnv("OIDC_CLIENT_ID"),
    redirect_uri: redirectUri, scope: scopes, state, nonce,
    code_challenge: challenge, code_challenge_method: "S256",
  });
  return {
    url: metadata.authorization_endpoint + "?" + params.toString(),
    transactionCookie: sealTransaction({
      state, nonce, verifier, returnTo, issuedAt: Math.floor(Date.now() / 1000),
    }),
  };
}
async function getJwks(): Promise<JsonWebKey[]> {
  const now = Date.now();
  if (jwksCache && jwksCache.expiresAt > now) return jwksCache.keys;
  const metadata = await getMetadata();
  const response = await fetch(metadata.jwks_uri, {
    cache: "no-store", signal: AbortSignal.timeout(8_000),
  });
  if (!response.ok) throw new Error("Identity provider signing keys are unavailable");
  const body: unknown = await response.json();
  if (!body || typeof body !== "object" || !Array.isArray((body as { keys?: unknown }).keys)) {
    throw new Error("Identity provider signing keys are invalid");
  }
  const keys = (body as { keys: JsonWebKey[] }).keys;
  jwksCache = { keys, expiresAt: now + 300_000 };
  return keys;
}
function safeEqual(left: string, right: string): boolean {
  const a = Buffer.from(left); const b = Buffer.from(right);
  return a.length === b.length && timingSafeEqual(a, b);
}
/** Verify RS256 signature plus required issuer, audience, time and nonce claims. */
export async function verifyIdToken(
  token: string, expectedNonce?: string, expectedSubject?: string,
): Promise<JwtClaims> {
  const parts = token.split(".");
  if (parts.length !== 3) throw new Error("Invalid ID token");
  let header: { alg?: string; kid?: string };
  let claims: JwtClaims;
  try {
    header = JSON.parse(Buffer.from(parts[0], "base64url").toString("utf8")) as typeof header;
    claims = JSON.parse(Buffer.from(parts[1], "base64url").toString("utf8")) as JwtClaims;
  } catch {
    throw new Error("Invalid ID token");
  }
  if (header.alg !== "RS256" || !header.kid) throw new Error("Unsupported ID token signing algorithm");
  const jwk = (await getJwks()).find((key) =>
    key.kid === header.kid && key.kty === "RSA" &&
    (!key.use || key.use === "sig") && (!key.alg || key.alg === "RS256")
  );
  if (!jwk) { jwksCache = null; throw new Error("ID token signing key was not found"); }
  const key = createPublicKey({ key: jwk, format: "jwk" });
  const verifier = createVerify("RSA-SHA256");
  verifier.update(parts[0] + "." + parts[1]);
  verifier.end();
  if (!verifier.verify(key, Buffer.from(parts[2], "base64url"))) {
    throw new Error("ID token signature validation failed");
  }
  const metadata = await getMetadata();
  const clientId = requiredEnv("OIDC_CLIENT_ID");
  const audiences = Array.isArray(claims.aud) ? claims.aud : [claims.aud];
  const now = Math.floor(Date.now() / 1000);
  if (
    claims.iss !== metadata.issuer || !audiences.includes(clientId) ||
    typeof claims.exp !== "number" || claims.exp <= now ||
    typeof claims.iat !== "number" || claims.iat > now + 60 ||
    typeof claims.sub !== "string" || !claims.sub
  ) throw new Error("ID token claims validation failed");
  if (audiences.length > 1 && claims.azp !== clientId) throw new Error("ID token authorized party validation failed");
  if (expectedNonce && (typeof claims.nonce !== "string" || !safeEqual(claims.nonce, expectedNonce))) {
    throw new Error("ID token nonce validation failed");
  }
  if (expectedSubject && claims.sub !== expectedSubject) throw new Error("ID token subject changed");
  return claims;
}
async function tokenRequest(form: URLSearchParams): Promise<OidcTokens> {
  const metadata = await getMetadata();
  const basic = Buffer.from(requiredEnv("OIDC_CLIENT_ID") + ":" + requiredEnv("OIDC_CLIENT_SECRET")).toString("base64");
  const response = await fetch(metadata.token_endpoint, {
    method: "POST",
    headers: {
      Authorization: "Basic " + basic,
      "Content-Type": "application/x-www-form-urlencoded",
      Accept: "application/json",
    },
    body: form, cache: "no-store", signal: AbortSignal.timeout(10_000),
  });
  if (!response.ok) throw new Error("Identity provider token request failed");
  const body: unknown = await response.json();
  if (!body || typeof body !== "object") throw new Error("Invalid token response");
  const data = body as TokenResponse;
  if (
    typeof data.access_token !== "string" || typeof data.expires_in !== "number" ||
    !Number.isFinite(data.expires_in) || data.expires_in <= 0
  ) throw new Error("Incomplete token response");
  return {
    access_token: data.access_token,
    refresh_token: typeof data.refresh_token === "string" ? data.refresh_token : undefined,
    id_token: typeof data.id_token === "string" ? data.id_token : "",
    expires_in: data.expires_in,
  };
}
export async function exchangeAuthorizationCode(code: string, verifier: string): Promise<OidcTokens> {
  const tokens = await tokenRequest(new URLSearchParams({
    grant_type: "authorization_code", code,
    redirect_uri: configuredRedirectUri(), code_verifier: verifier,
  }));
  if (!tokens.id_token) throw new Error("Identity provider did not return an ID token");
  return tokens;
}
export async function refreshOidcTokens(refreshToken: string): Promise<OidcTokens> {
  return tokenRequest(new URLSearchParams({ grant_type: "refresh_token", refresh_token: refreshToken }));
}
