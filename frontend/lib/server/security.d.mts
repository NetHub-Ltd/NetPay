export function safeReturnTo(value: string | null, origin: string): string;
export function constantTimeEqual(left: string, right: string): boolean;
export function isValidSessionHandle(value: unknown): boolean;
export function isSameOriginRequest(
  origin: string | null,
  requestOrigin: string,
  secFetchSite: string | null,
): boolean;
export function resolveAllowedGet(
  path: string[],
  searchParams: URLSearchParams,
): string | null;

export function createPkceChallenge(verifier: string): string;
export type LoginTransaction = {
  state: string;
  nonce: string;
  verifier: string;
  returnTo: string;
  issuedAt: number;
};
export function sealLoginTransaction(value: LoginTransaction, key: Uint8Array): string;
export function openLoginTransaction(
  value: string | undefined,
  key: Uint8Array,
  ttlSeconds: number,
  nowSeconds: number,
): LoginTransaction | null;


export function createPublicClientTokenRequest(
  clientId: string,
  parameters: URLSearchParams,
): {
  headers: {
    "Content-Type": string;
    Accept: string;
  };
  body: URLSearchParams;
};

export function isOidcConfigured(
  environment: Record<string, string | undefined>,
): boolean;

export type OidcConfigurationChecks = {
  issuer_present: boolean;
  issuer_https: boolean;
  client_id_present: boolean;
  redirect_uri_present: boolean;
  redirect_uri_https: boolean;
  redirect_origin_matches_site: boolean;
  transaction_secret_ok: boolean;
  scopes_ok: boolean;
};

export function getOidcConfigurationChecks(
  environment: Record<string, string | undefined>,
): OidcConfigurationChecks;
