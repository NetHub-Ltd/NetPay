/**
 * OIDC authorization code + PKCE for Keycloak (public client `netpay`).
 * No client secret. NetPay never talks to Keycloak JWKS — browser only.
 */

const KEYCLOAK_URL = (import.meta.env.VITE_KEYCLOAK_URL as string) || 'https://auth.nethub.co.ke'
const REALM = (import.meta.env.VITE_KEYCLOAK_REALM as string) || 'nethub'
const CLIENT_ID = (import.meta.env.VITE_KEYCLOAK_CLIENT_ID as string) || 'netpay'
const REDIRECT_URI =
  (import.meta.env.VITE_OIDC_REDIRECT_URI as string) ||
  `${window.location.origin}/auth/callback`

const PKCE_VERIFIER_KEY = 'netpay_pkce_verifier'
const PKCE_STATE_KEY = 'netpay_pkce_state'
const REFRESH_KEY = 'nethub_refresh_token'

function base64UrlEncode(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer)
  let str = ''
  for (let i = 0; i < bytes.length; i++) str += String.fromCharCode(bytes[i])
  return btoa(str).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
}

function randomString(length: number): string {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~'
  const arr = new Uint8Array(length)
  crypto.getRandomValues(arr)
  let out = ''
  for (let i = 0; i < length; i++) out += chars[arr[i] % chars.length]
  return out
}

async function sha256(plain: string): Promise<ArrayBuffer> {
  const data = new TextEncoder().encode(plain)
  return crypto.subtle.digest('SHA-256', data)
}

export function getOidcConfig() {
  return {
    keycloakUrl: KEYCLOAK_URL.replace(/\/$/, ''),
    realm: REALM,
    clientId: CLIENT_ID,
    redirectUri: REDIRECT_URI,
    authorizationEndpoint: `${KEYCLOAK_URL.replace(/\/$/, '')}/realms/${REALM}/protocol/openid-connect/auth`,
    tokenEndpoint: `${KEYCLOAK_URL.replace(/\/$/, '')}/realms/${REALM}/protocol/openid-connect/token`,
    endSessionEndpoint: `${KEYCLOAK_URL.replace(/\/$/, '')}/realms/${REALM}/protocol/openid-connect/logout`,
  }
}

/** Start login: store PKCE verifier + state, redirect to Keycloak. */
export async function beginLogin(returnTo = '/home'): Promise<void> {
  const cfg = getOidcConfig()
  const verifier = randomString(64)
  const state = randomString(32)
  const challenge = base64UrlEncode(await sha256(verifier))

  sessionStorage.setItem(PKCE_VERIFIER_KEY, verifier)
  sessionStorage.setItem(PKCE_STATE_KEY, state)
  sessionStorage.setItem('netpay_return_to', returnTo)

  const params = new URLSearchParams({
    client_id: cfg.clientId,
    redirect_uri: cfg.redirectUri,
    response_type: 'code',
    scope: 'openid profile email',
    state,
    code_challenge: challenge,
    code_challenge_method: 'S256',
  })

  window.location.assign(`${cfg.authorizationEndpoint}?${params.toString()}`)
}

export type TokenSet = {
  access_token: string
  refresh_token?: string
  id_token?: string
  expires_in?: number
}

/** Exchange authorization code for tokens (public client + PKCE). */
export async function exchangeCode(code: string, state: string): Promise<TokenSet> {
  const cfg = getOidcConfig()
  const savedState = sessionStorage.getItem(PKCE_STATE_KEY)
  const verifier = sessionStorage.getItem(PKCE_VERIFIER_KEY)
  sessionStorage.removeItem(PKCE_STATE_KEY)
  sessionStorage.removeItem(PKCE_VERIFIER_KEY)

  if (!verifier) throw new Error('Missing PKCE verifier — start login again')
  if (!savedState || savedState !== state) throw new Error('Invalid OAuth state')

  const body = new URLSearchParams({
    grant_type: 'authorization_code',
    client_id: cfg.clientId,
    code,
    redirect_uri: cfg.redirectUri,
    code_verifier: verifier,
  })

  const res = await fetch(cfg.tokenEndpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`Token exchange failed (${res.status}): ${text.slice(0, 200)}`)
  }
  return res.json() as Promise<TokenSet>
}

export function setRefreshToken(token: string | null) {
  if (token) sessionStorage.setItem(REFRESH_KEY, token)
  else sessionStorage.removeItem(REFRESH_KEY)
}

export function getRefreshToken(): string | null {
  return sessionStorage.getItem(REFRESH_KEY)
}

export function getReturnTo(): string {
  return sessionStorage.getItem('netpay_return_to') || '/home'
}

export function logoutAtKeycloak(idToken?: string | null) {
  const cfg = getOidcConfig()
  const params = new URLSearchParams({
    client_id: cfg.clientId,
    post_logout_redirect_uri: `${window.location.origin}/`,
  })
  if (idToken) params.set('id_token_hint', idToken)
  window.location.assign(`${cfg.endSessionEndpoint}?${params.toString()}`)
}
