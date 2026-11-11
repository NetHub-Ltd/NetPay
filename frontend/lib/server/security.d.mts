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
