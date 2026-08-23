import { type FormEvent, useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api, ApiError, type Tenant, type Webhook } from '../api/client'
import { EmptyState } from '../components/EmptyState'
import { useAuth } from '../auth/AuthContext'

export function Webhooks() {
  const { isAdmin } = useAuth()
  const [params] = useSearchParams()
  const presetTenant = params.get('tenant_id') || ''
  const [items, setItems] = useState<Webhook[]>([])
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [tenantId, setTenantId] = useState(presetTenant)
  const [url, setUrl] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [secretOnce, setSecretOnce] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function load(tid?: string) {
    const q = tid || tenantId
    if (!q) { setItems([]); return }
    try {
      setItems(await api.get<Webhook[]>(`/v1/webhooks?tenant_id=${q}`))
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Failed to load webhooks')
    }
  }

  useEffect(() => {
    if (isAdmin) {
      api.get<Tenant[]>('/v1/tenants').then((t) => {
        setTenants(t)
        if (!tenantId && t[0]) {
          setTenantId(t[0].id)
          load(t[0].id)
        } else if (tenantId) load(tenantId)
      }).catch(() => {})
    } else if (tenantId) load(tenantId)
  }, [])

  useEffect(() => {
    if (tenantId) load(tenantId)
  }, [tenantId])

  async function onCreate(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    setSecretOnce(null)
    try {
      const created = await api.post<Webhook>('/v1/webhooks', { tenant_id: tenantId, url })
      setSecretOnce(created.secret)
      setUrl('')
      await load()
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Webhook rejected (liveness or limit)')
    } finally {
      setBusy(false)
    }
  }

  async function onDelete(id: string) {
    if (!confirm('Remove this webhook?')) return
    try {
      await api.delete(`/v1/webhooks/${id}`)
      await load()
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Delete failed')
    }
  }

  return (
    <div data-testid="webhooks-page">
      <div className="page-header">
        <div>
          <h1>Webhooks</h1>
          <p>Max 3 per client · HTTPS only · liveness probe before save</p>
        </div>
      </div>
      {error && <div className="alert error">{error}</div>}
      {secretOnce && (
        <div className="alert info">
          Signing secret (shown once):
          <div className="secret-once">{secretOnce}</div>
        </div>
      )}

      <div className="card">
        <h2>Add webhook</h2>
        {isAdmin && (
          <>
            <label>Tenant</label>
            <select value={tenantId} onChange={(e) => setTenantId(e.target.value)}>
              <option value="">Select</option>
              {tenants.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select>
          </>
        )}
        <form onSubmit={onCreate}>
          <label>HTTPS URL</label>
          <input type="url" required pattern="https://.*" value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://example.com/hooks/nethub" />
          <button className="btn primary" type="submit" disabled={busy || !tenantId}>{busy ? 'Probing…' : 'Save after liveness'}</button>
        </form>
      </div>

      {!tenantId ? (
        <EmptyState title="Select a tenant" hint="Webhooks are scoped per client." />
      ) : items.length === 0 ? (
        <EmptyState title="No webhooks" hint="Add an HTTPS endpoint; we probe it before saving." />
      ) : (
        <div className="card">
          <table>
            <thead>
              <tr><th>URL</th><th>Last live</th><th></th></tr>
            </thead>
            <tbody>
              {items.map((w) => (
                <tr key={w.id}>
                  <td className="mono">{w.url}</td>
                  <td className="muted tiny">{w.last_live_at ? new Date(w.last_live_at).toLocaleString() : '—'}</td>
                  <td><button type="button" className="btn danger" onClick={() => onDelete(w.id)}>Remove</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
