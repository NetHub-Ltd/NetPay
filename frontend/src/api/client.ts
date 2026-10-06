const TOKEN_KEY = 'nethub_token'
const ID_TOKEN_KEY = 'nethub_id_token'

export function getToken(): string | null {
  return sessionStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string | null) {
  if (token) sessionStorage.setItem(TOKEN_KEY, token)
  else sessionStorage.removeItem(TOKEN_KEY)
}

export function getIdToken(): string | null {
  return sessionStorage.getItem(ID_TOKEN_KEY)
}

export function setIdToken(token: string | null) {
  if (token) sessionStorage.setItem(ID_TOKEN_KEY, token)
  else sessionStorage.removeItem(ID_TOKEN_KEY)
}

export function clearSessionTokens() {
  sessionStorage.removeItem(TOKEN_KEY)
  sessionStorage.removeItem(ID_TOKEN_KEY)
}

export class ApiError extends Error {
  status: number
  detail: string
  constructor(status: number, detail: string) {
    super(detail)
    this.status = status
    this.detail = detail
  }
}

/** Flatten FastAPI detail (string | object) for UI. */
export function formatApiDetail(detail: unknown): string {
  if (detail == null) return 'Request failed'
  if (typeof detail === 'string') return detail
  if (typeof detail === 'object' && detail !== null) {
    const d = detail as Record<string, unknown>
    if (typeof d.message === 'string') {
      const parts = [d.message]
      if (d.source) parts.push(`Source: ${String(d.source)}`)
      if (d.stage) parts.push(`Stage: ${String(d.stage)}`)
      if (d.hint) parts.push(String(d.hint))
      return parts.join(' · ')
    }
    return JSON.stringify(detail)
  }
  return String(detail)
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers || {})
  if (!headers.has('Content-Type') && options.body) {
    headers.set('Content-Type', 'application/json')
  }
  const token = getToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)

  const res = await fetch(path, { ...options, headers })
  if (res.status === 204) return undefined as T

  const text = await res.text()
  let data: unknown = null
  try {
    data = text ? JSON.parse(text) : null
  } catch {
    data = text
  }

  if (!res.ok) {
    let detail = res.statusText || 'Request failed'
    if (typeof data === 'object' && data && 'detail' in data) {
      const d = (data as { detail: unknown }).detail
      detail = formatApiDetail(d)
    }
    throw new ApiError(res.status, detail)
  }
  return data as T
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown, init?: RequestInit) =>
    request<T>(path, {
      method: 'POST',
      body: body !== undefined ? JSON.stringify(body) : undefined,
      ...init,
      headers: {
        ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
        ...(init?.headers || {}),
      },
    }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, {
      method: 'PATCH',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
}

export type User = {
  id: string
  email: string
  display_name?: string | null
  full_name?: string | null
  username?: string | null
  role: 'admin' | 'user'
  tenant_id?: string | null
  tenant_name?: string | null
  tenant_tier?: string | null
  is_active: boolean
}

export type TokenResponse = {
  access_token: string
  token_type: string
  role: string
  email: string
  tenant_id?: string | null
}

export type Health = {
  status: string
  database: boolean
  redis: string
  admin_ready: boolean
  environment: string
  version: string
}

export type Tenant = {
  id: string
  name: string
  slug: string
  status: string
  category?: string | null
  email?: string | null
  phone_number?: string | null
  created_at?: string
}


export type Readiness = {
  has_business: boolean
  has_shortcode: boolean
  has_connected_shortcode: boolean
  has_notifications: boolean
  has_api_client: boolean
  ready_to_collect: boolean
  next_step:
    | 'create_business'
    | 'add_shortcode'
    | 'connect_mpesa'
    | 'add_notification'
    | 'connect_system'
    | 'take_payment'
    | 'done'
  tenant_id?: string | null
  primary_integration_id?: string | null
  shortcode_count: number
  connected_count: number
  notification_count?: number
  api_client_count?: number
}

export type Integration = {
  id: string
  tenant_id: string
  public_id: string
  shortcode: string
  type: string
  environment: string
  status: string
  connected?: boolean
  confirmation_url?: string | null
  validation_url?: string | null
  stk_callback_url?: string | null
  created_at?: string
}

export type Webhook = {
  id: string
  tenant_id: string
  url: string
  secret: string
  last_live_at?: string | null
  created_at: string
}

export type PaymentIntent = {
  id: string
  tenant_id: string
  integration_id: string
  status: string
  amount: string | number
  amount_minor?: number
  currency: string
  phone: string
  account_reference?: string | null
  description?: string | null
  provider_checkout_id?: string | null
  provider_merchant_id?: string | null
  provider_transaction_id?: string | null
  failure_reason?: string | null
  status_callback_url?: string | null
  stk_request_json?: string | null
  stk_response_json?: string | null
  metadata_json?: string | null
  created_at: string
  updated_at?: string
}

export type GatewayEvent = {
  id: string
  category: string
  action: string
  message: string
  payment_intent_id?: string | null
  is_replayable: boolean
  created_at: string
}

export type OAuthClientOut = {
  client_id: string
  client_secret: string
  name: string
  tenant_id: string
}
