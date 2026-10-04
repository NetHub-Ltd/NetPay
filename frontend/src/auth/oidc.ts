/**
 * Browser OIDC (Zitadel / NetHub IdP) with PKCE — public SPA client.
 *
 * Aligned with NetHubKe env naming (OIDC_ISSUER, OIDC_CLIENT_ID) exposed to the
 * SPA as VITE_OIDC_* at image build time. NetPay never validates the JWT; it
 * stores the access_token and calls NetHub GET /users/me with Bearer.
 *
 * Unlike NetHubKe (Next.js Auth.js + optional client secret on the server),
 * this SPA uses authorization-code + PKCE only — no client secret in the browser.
 */

const STORAGE = {
  verifier: 'netpay_oidc_verifier',
  state: 'netpay_oidc_state',
  returnTo: 'netpay_oidc_return',
} as const

const BUILD_PLACEHOLDER_ISSUER = 'https://build-placeholder.invalid'

export type OidcConfig = {
  issuer: string
  clientId: string
  redirectUri: string
  scopes: string
}

type Discovery = {
  authorization_endpoint?: string
  token_endpoint?: string
  end_session_endpoint?: string
}

let discoveryCache: { at: number; data: Discovery } | null = null

export function getOidcConfig(): OidcConfig | null {
  const issuer = (import.meta.env.VITE_OIDC_ISSUER as string | undefined)
    ?.trim()
    .replace(/\/$/, '')
  const clientId = (import.meta.env.VITE_OIDC_CLIENT_ID as string | undefined)?.trim()
  if (!issuer || !clientId) return null
  if (issuer === BUILD_PLACEHOLDER_ISSUER) return null
  const redirectUri =
    (import.meta.env.VITE_OIDC_REDIRECT_URI as string | undefined)?.trim() ||
    `${window.location.origin}/auth/callback`
  const scopes =
    (import.meta.env.VITE_OIDC_SCOPES as string | undefined)?.trim() ||
    'openid profile email offline_access'
  return { issuer, clientId, redirectUri, scopes }
}

export function isOidcConfigured(): boolean {
  return getOidcConfig() !== null
}

async function oidcDiscovery(issuer: string): Promise<Discovery> {
  const now = Date.now()
  if (discoveryCache && now - discoveryCache.at < 3600_000) {
    return discoveryCache.data
  }
  const url = `${issuer}/.well-known/openid-configuration`
  const res = await fetch(url, { headers: { Accept: 'application/json' } })
  if (!res.ok) {
    throw new Error(`OIDC discovery failed: ${res.status} ${url}`)
  }
  const data = (await res.json()) as Discovery
  discoveryCache = { at: now, data }
  return data
}

function randomString(bytes = 32): string {
  const arr = new Uint8Array(bytes)
  crypto.getRandomValues(arr)
  return base64Url(arr)
}

function base64Url(data: ArrayBuffer | Uint8Array): string {
  const bytes = data instanceof Uint8Array ? data : new Uint8Array(data)
  let s = ''
  for (let i = 0; i < bytes.length; i++) s += String.fromCharCode(bytes[i])
  return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
}

async function sha256(plain: string): Promise<ArrayBuffer> {
  return crypto.subtle.digest('SHA-256', new TextEncoder().encode(plain))
}

async function pkceChallenge(verifier: string): Promise<string> {
  return base64Url(await sha256(verifier))
}

/** Begin authorization-code + PKCE login at the IdP. */
export async function beginLogin(returnTo = '/'): Promise<void> {
  const cfg = getOidcConfig()
  if (!cfg) {
    throw new Error(
      'OIDC is not configured. Set VITE_OIDC_ISSUER and VITE_OIDC_CLIENT_ID at image build.',
    )
  }
  const discovery = await oidcDiscovery(cfg.issuer)
  const authorize =
    discovery.authorization_endpoint || `${cfg.issuer}/oauth/v2/authorize`

  const verifier = randomString(32)
  const state = randomString(16)
  const challenge = await pkceChallenge(verifier)
  sessionStorage.setItem(STORAGE.verifier, verifier)
  sessionStorage.setItem(STORAGE.state, state)
  sessionStorage.setItem(STORAGE.returnTo, returnTo)

  const url = new URL(authorize)
  url.searchParams.set('client_id', cfg.clientId)
  url.searchParams.set('redirect_uri', cfg.redirectUri)
  url.searchParams.set('response_type', 'code')
  url.searchParams.set('scope', cfg.scopes)
  url.searchParams.set('state', state)
  url.searchParams.set('code_challenge', challenge)
  url.searchParams.set('code_challenge_method', 'S256')
  window.location.assign(url.toString())
}

export type TokenBundle = {
  access_token: string
  id_token?: string
  refresh_token?: string
  expires_in?: number
  token_type?: string
}

/** Exchange authorization code on /auth/callback. */
export async function completeLogin(params: URLSearchParams): Promise<{
  tokens: TokenBundle
  returnTo: string
}> {
  const cfg = getOidcConfig()
  if (!cfg) throw new Error('OIDC is not configured')

  const err = params.get('error')
  if (err) {
    throw new Error(params.get('error_description') || err)
  }
  const code = params.get('code')
  const state = params.get('state')
  const expected = sessionStorage.getItem(STORAGE.state)
  const verifier = sessionStorage.getItem(STORAGE.verifier)
  const returnTo = sessionStorage.getItem(STORAGE.returnTo) || '/'
  sessionStorage.removeItem(STORAGE.state)
  sessionStorage.removeItem(STORAGE.verifier)
  sessionStorage.removeItem(STORAGE.returnTo)

  if (!code || !state || !expected || state !== expected || !verifier) {
    throw new Error('Invalid or expired login state. Try signing in again.')
  }

  const discovery = await oidcDiscovery(cfg.issuer)
  const tokenUrl = discovery.token_endpoint || `${cfg.issuer}/oauth/v2/token`

  const body = new URLSearchParams()
  body.set('grant_type', 'authorization_code')
  body.set('code', code)
  body.set('redirect_uri', cfg.redirectUri)
  body.set('client_id', cfg.clientId)
  body.set('code_verifier', verifier)

  const res = await fetch(tokenUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      Accept: 'application/json',
    },
    body,
  })
  const data = (await res.json().catch(() => ({}))) as TokenBundle & {
    error?: string
    error_description?: string
  }
  if (!res.ok || !data.access_token) {
    throw new Error(data.error_description || data.error || 'Token exchange failed')
  }
  return { tokens: data, returnTo }
}

/** RP-initiated logout (discovery end_session when available). */
export async function beginLogout(idToken?: string | null): Promise<void> {
  const cfg = getOidcConfig()
  if (!cfg) {
    window.location.assign('/login')
    return
  }
  try {
    const discovery = await oidcDiscovery(cfg.issuer)
    const endSession =
      discovery.end_session_endpoint || `${cfg.issuer}/oidc/v1/end_session`
    const url = new URL(endSession)
    if (idToken) url.searchParams.set('id_token_hint', idToken)
    url.searchParams.set('post_logout_redirect_uri', `${window.location.origin}/login`)
    url.searchParams.set('client_id', cfg.clientId)
    window.location.assign(url.toString())
  } catch {
    window.location.assign('/login')
  }
}
