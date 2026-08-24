import { type FormEvent, useEffect, useState } from 'react'
import { Navigate, useSearchParams } from 'react-router-dom'
import { api, ApiError, type OAuthClientOut, type Tenant } from '../api/client'
import { useAuth } from '../auth/AuthContext'
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
      if (!tenantId && t[0]) setTenantId(t[0].id)
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
      <div className="page-header">
        <div>
          <h1>OAuth clients</h1>
          <p>Client-credentials for machine access (admin)</p>
        </div>
      </div>
      {error && <div className="alert error">{error}</div>}
      {created && (
        <div className="alert info">
          Client created — copy the secret now; it is not shown again.
          <div className="secret-once">client_id: {created.client_id}</div>
          <div className="secret-once" style={{ marginTop: 8 }}>client_secret: {created.client_secret}</div>
        </div>
      )}

      <div className="card">
        <h2>Create client</h2>
        <form onSubmit={onCreate}>
          <label>Tenant</label>
          <select required value={tenantId} onChange={(e) => setTenantId(e.target.value)}>
            <option value="">Select</option>
            {tenants.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
          </select>
          <label>Name</label>
          <input required value={name} onChange={(e) => setName(e.target.value)} />
          <button className="btn primary" type="submit" disabled={busy || !tenantId}>{busy ? 'Creating…' : 'Create OAuth client'}</button>
        </form>
      </div>

      {!tenants.length && <EmptyState title="No tenants" hint="Create a tenant first." />}
    </div>
  )
}
