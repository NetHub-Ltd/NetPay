import { type FormEvent, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
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
  const [secretAck, setSecretAck] = useState(false)
  const [busy, setBusy] = useState(false)

  async function load() {
    if (!tenantId && !isAdmin) return
    if (!tenantId) {
      setItems([])
      return
    }
    try {
      setItems(await api.get<Webhook[]>(`/v1/webhooks?tenant_id=${tenantId}`))
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
    setSecretAck(false)
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
      setError(
        err instanceof ApiError
          ? err.detail
          : 'Could not save (check HTTPS and that the URL responds)',
      )
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

  function copySecret() {
    if (!secretOnce) return
    navigator.clipboard.writeText(secretOnce).catch(() => {})
  }

  return (
    <div data-testid="webhooks-page">
      <div className="page-header">
        <div>
          <h1>Payment notifications</h1>
          <p>
            Tell <em>your</em> system when a payment is Paid or Failed. This is separate from M-Pesa → NetPay URLs on
            each shortcode.
          </p>
        </div>
      </div>
      <p className="muted tiny">
        <Link to="/integrations">← Paybills &amp; tills</Link>
        {' · '}
        <Link to="/intents">Take a payment</Link>
      </p>
      {error && <div className="alert error">{error}</div>}
      {msg && <div className="alert ok">{msg}</div>}
      {secretOnce && (
        <div className="alert info">
          <strong>Copy this signing secret now — it won’t be shown again.</strong>
          <div className="secret-once">{secretOnce}</div>
          <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem', flexWrap: 'wrap' }}>
            <button type="button" className="btn primary" onClick={copySecret}>
              Copy secret
            </button>
            <button type="button" className="btn" onClick={() => setSecretAck(true)}>
              I’ve copied it
            </button>
          </div>
          {secretAck && <p className="muted tiny">You can leave this page. Store the secret in your app config.</p>}
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
            {!tenantId && tenants.length === 0 && (
              <p className="muted tiny">No businesses yet. Create one under Businesses first.</p>
            )}
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
