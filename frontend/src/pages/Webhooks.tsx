import { type FormEvent, useEffect, useState } from 'react'
import { api, ApiError, type Tenant, type Webhook } from '../api/client'
import { EmptyState } from '../components/EmptyState'
import { useAuth } from '../auth/AuthContext'

export function Webhooks() {
  const { isAdmin, user } = useAuth()
  const [items, setItems] = useState<Webhook[]>([])
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [tenantId, setTenantId] = useState(user?.tenant_id || '')
  const [url, setUrl] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [msg, setMsg] = useState<string | null>(null)
  const [secretOnce, setSecretOnce] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function load() {
    if (!tenantId && !isAdmin) return
    try {
      const q = tenantId ? `?tenant_id=${tenantId}` : ''
      setItems(await api.get<Webhook[]>(`/v1/webhooks${q}`))
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Could not load notification URLs')
    }
  }

  useEffect(() => {
    if (isAdmin) {
      api.get<Tenant[]>('/v1/tenants').then(setTenants).catch(() => {})
    } else if (user?.tenant_id) {
      setTenantId(user.tenant_id)
    }
  }, [isAdmin, user])

  useEffect(() => {
    load()
  }, [tenantId])

  async function onCreate(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    setMsg(null)
    setSecretOnce(null)
    try {
      const res = await api.post<{ id: string; secret?: string }>('/v1/webhooks', {
        tenant_id: tenantId,
        url,
      })
      if (res.secret) setSecretOnce(res.secret)
      setUrl('')
      setMsg('Notification URL saved. We will POST payment updates to this address.')
      await load()
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Could not save (check HTTPS and that the URL responds)')
    } finally {
      setBusy(false)
    }
  }

  async function onDelete(id: string) {
    const ok = window.confirm(
      'Stop sending payment updates to this URL?\n\nYour app will no longer receive automatic notices when a payment status changes.',
    )
    if (!ok) return
    try {
      await api.delete(`/v1/webhooks/${id}`)
      setMsg('Notification URL removed.')
      await load()
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Could not remove')
    }
  }

  return (
    <div data-testid="webhooks-page">
      <div className="page-header">
        <div>
          <h1>Payment notifications</h1>
          <p>
            Tell your system when a payment is Paid or Failed. We only call HTTPS addresses (up to 3 per business).
          </p>
        </div>
      </div>
      {error && <div className="alert error">{error}</div>}
      {msg && <div className="alert ok">{msg}</div>}
      {secretOnce && (
        <div className="alert info">
          Signing secret (copy now — shown once):
          <div className="secret-once">{secretOnce}</div>
        </div>
      )}

      <div className="card">
        <h2>Add a notification URL</h2>
        {isAdmin && (
          <>
            <label>Business</label>
            <select value={tenantId} onChange={(e) => setTenantId(e.target.value)}>
              <option value="">Select…</option>
              {tenants.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
          </>
        )}
        <form onSubmit={onCreate}>
          <label>HTTPS address</label>
          <input
            type="url"
            required
            pattern="https://.*"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://your-app.com/hooks/payments"
          />
          <button className="btn primary" type="submit" disabled={busy || !tenantId}>
            {busy ? 'Checking URL…' : 'Save URL'}
          </button>
        </form>
      </div>

      {!tenantId ? (
        <EmptyState title="Choose a business" hint="Notification URLs belong to a business account." />
      ) : items.length === 0 ? (
        <EmptyState
          title="No notification URLs"
          hint="Add an HTTPS endpoint. We check that it responds before saving."
        />
      ) : (
        <div className="card">
          <table>
            <thead>
              <tr>
                <th>URL</th>
                <th>Last checked</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items.map((w) => (
                <tr key={w.id}>
                  <td className="mono">{w.url}</td>
                  <td className="muted tiny">
                    {w.last_live_at ? new Date(w.last_live_at).toLocaleString() : '—'}
                  </td>
                  <td>
                    <button type="button" className="btn danger" onClick={() => onDelete(w.id)}>
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
