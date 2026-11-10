export function safeReturnTo(value: string | null, origin: string): string;
export function constantTimeEqual(left: string, right: string): boolean;
export function isValidSessionHandle(value: string): boolean;
export function isSameOriginRequest(
  origin: string | null,
  requestOrigin: string,
  secFetchSite: string | null,
): boolean;
export function resolveAllowedGet(
  path: string[],
  searchParams: URLSearchParams,
): string | null;
