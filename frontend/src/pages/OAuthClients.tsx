import { type FormEvent, useEffect, useState } from 'react'
import { Navigate, useSearchParams } from 'react-router-dom'
import { api, ApiError, type OAuthClientOut, type Tenant } from '../api/client'
import { useAuth } from '../auth/authState'
import { EmptyState } from '../components/EmptyState'
import { card, control, errorAlert, label, pageDescription, pageHeader, pageTitle, primaryButton } from '../components/ui'

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
      <div className={pageHeader}>
        <div>
        <h1 className={pageTitle}>OAuth clients</h1>
        <p className={pageDescription}>Client-credentials for machine access (admin)</p>
        </div>
      </div>
      {error && <div className={errorAlert} role="alert">{error}</div>}
      {created && (
        <div className="mb-4 rounded-lg border border-[var(--accent-2)]/30 bg-[var(--accent-2)]/10 px-4 py-3 text-sm text-[var(--text)]" role="status">
          Client created — copy the secret now; it is not shown again.
          <div className="mt-2 break-all font-mono">client_id: {created.client_id}</div>
          <div className="mt-2 break-all font-mono">client_secret: {created.client_secret}</div>
        </div>
      )}

      <div className={card}>
        <h2 className="mb-3 text-base font-semibold">Create client</h2>
        <form className="max-w-xl" onSubmit={onCreate}>
          <label className={label}>Tenant</label>
          <select className={control} required value={tenantId} onChange={(e) => setTenantId(e.target.value)}>
            <option value="">Select</option>
            {tenants.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
          </select>
          <label className={label}>Name</label>
          <input className={control} required value={name} onChange={(e) => setName(e.target.value)} />
          <button className={`${primaryButton} mt-4`} type="submit" disabled={busy}>
            {busy ? 'Creating…' : 'Create client'}
          </button>
        </form>
      </div>

      {!tenants.length && <EmptyState title="No tenants" hint="Create a tenant first." />}
    </div>
  )
}
