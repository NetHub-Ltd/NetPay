import { cookies } from "next/headers";
import { getToken } from "next-auth/jwt";
import type { JWT } from "next-auth/jwt";

function isSecureAuthUrl(): boolean {
  const url = process.env.AUTH_URL || process.env.NEXTAUTH_URL || "";
  return (
    process.env.AUTH_USE_SECURE_COOKIES === "true" ||
    url.startsWith("https://") ||
    process.env.VERCEL === "1"
  );
}

/** Must match frontend/auth.ts cookie naming. */
export function sessionCookieName(): string {
  return isSecureAuthUrl()
    ? "__Secure-authjs.session-token"
    : "authjs.session-token";
}

export async function getAuthJwt(): Promise<JWT | null> {
  const cookieStore = await cookies();
  const all = cookieStore.getAll();
  const cookieHeader = all.map((c) => `${c.name}=${c.value}`).join("; ");
  const name = sessionCookieName();
  const secure = isSecureAuthUrl();

  const attempts: Array<{ cookieName?: string; salt?: string; secureCookie?: boolean }> = [
    { cookieName: name, salt: name, secureCookie: secure },
    { secureCookie: secure },
    { cookieName: "authjs.session-token", salt: "authjs.session-token", secureCookie: false },
    {
      cookieName: "__Secure-authjs.session-token",
      salt: "__Secure-authjs.session-token",
      secureCookie: true,
    },
  ];

  for (const opts of attempts) {
    try {
      const token = await getToken({
        req: {
          headers: {
            cookie: cookieHeader,
            get(headerName: string) {
              if (headerName.toLowerCase() === "cookie") return cookieHeader;
              return undefined;
            },
          },
        } as never,
        secret: process.env.AUTH_SECRET,
        ...opts,
      });
      if (token) return token as JWT;
    } catch {
      /* try next */
    }
  }
  return null;
}

export async function getIdpAccessToken(): Promise<string | undefined> {
  const jwt = await getAuthJwt();
  return typeof jwt?.accessToken === "string" ? jwt.accessToken : undefined;
}
