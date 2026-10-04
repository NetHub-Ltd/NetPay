import { type FormEvent, useEffect, useState } from 'react'
import { Navigate, useSearchParams } from 'react-router-dom'
import { api, ApiError, type OAuthClientOut, type Tenant } from '../api/client'
import { useAuth } from '../auth/authState'
import { EmptyState } from '../components/EmptyState'

export function OAuthClients() {
  const { isAdmin } = useAuth()
  const [params] = useSearchParams()
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [tenantId, setTenantId] = useState(params.get('tenant_id') || '')
  const [name, setName] = useState('Default API client')
  const [created, setCreated] = useState<OAuthClientOut | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (!isAdmin) return
    api.get<Tenant[]>('/v1/tenants').then((t) => {
      setTenants(t)
      setTenantId((current) => current || t[0]?.id || '')
    }).catch(() => {})
  }, [isAdmin])

  if (!isAdmin) return <Navigate to="/forbidden" replace />

  async function onCreate(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    setCreated(null)
    try {
      const res = await api.post<OAuthClientOut>('/v1/oauth-clients', { tenant_id: tenantId, name })
      setCreated(res)
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Create failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div data-testid="oauth-page">
      <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1>OAuth clients</h1>
          <p>Client-credentials for machine access (admin)</p>
        </div>
      </div>
      {error && <div className="mb-4 rounded-lg border px-4 py-3 text-sm border-[var(--danger)]/30 bg-[var(--danger)]/10 text-[var(--danger)]">{error}</div>}
      {created && (
        <div className="mb-4 rounded-lg border px-4 py-3 text-sm border-[var(--accent-2)]/30 bg-[var(--accent-2)]/10 text-[var(--text)]">
          Client created — copy the secret now; it is not shown again.
          <div className="mt-1 break-all font-mono">client_id: {created.client_id}</div>
          <div className="mt-1 break-all font-mono" style={{ marginTop: 8 }}>client_secret: {created.client_secret}</div>
        </div>
      )}

      <div className="mb-4 rounded-[var(--radius)] border border-[var(--border)] bg-[var(--panel)] p-4 shadow-[var(--shadow)]">
        <h2>Create client</h2>
        <form onSubmit={onCreate}>
          <label>Tenant</label>
          <select required value={tenantId} onChange={(e) => setTenantId(e.target.value)}>
            <option value="">Select</option>
            {tenants.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
          </select>
          <label>Name</label>
          <input required value={name} onChange={(e) => setName(e.target.value)} />
          <button className="inline-flex items-center justify-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--panel)] px-3 py-2 text-sm font-medium text-[var(--text)] no-underline shadow-[var(--shadow)]" type="submit" disabled={busy}>
            {busy ? 'Creating…' : 'Create client'}
          </button>
        </form>
      </div>

      {!tenants.length && <EmptyState title="No tenants" hint="Create a tenant first." />}
    </div>
  )
}
