import { type FormEvent, useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, ApiError, type Tenant, type Webhook } from '../api/client'
import { EmptyState } from '../components/EmptyState'
import { useAuth } from '../auth/authState'
import { button, card, control, dangerButton, errorAlert, label, mono, pageDescription, pageHeader, pageTitle, primaryButton, successAlert, table, tableWrap } from '../components/ui'

export function Webhooks() {
  const { isAdmin, user } = useAuth()
  const [items, setItems] = useState<Webhook[]>([])
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [selectedTenantId, setSelectedTenantId] = useState(user?.tenant_id || '')
  const tenantId = isAdmin ? selectedTenantId : user?.tenant_id || ''
  const [url, setUrl] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [msg, setMsg] = useState<string | null>(null)
  const [secretOnce, setSecretOnce] = useState<string | null>(null)
  const [secretAck, setSecretAck] = useState(false)
  const [busy, setBusy] = useState(false)

  const load = useCallback(async () => {
    if (!tenantId && !isAdmin) return
    if (!tenantId) return
    try {
      setItems(await api.get<Webhook[]>(`/v1/webhooks?tenant_id=${tenantId}`))
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Could not load notification URLs')
    }
  }, [isAdmin, tenantId])

  useEffect(() => {
    if (isAdmin) {
      api.get<Tenant[]>('/v1/tenants').then(setTenants).catch(() => {})
    }
  }, [isAdmin])

  useEffect(() => {
    void Promise.resolve().then(load)
  }, [load])

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
      <div className={pageHeader}>
        <div>
          <h1 className={pageTitle}>App endpoints</h1>
          <p className={pageDescription}>
            Tell <em>your</em> system when a payment is Paid or Failed. This is separate from M-Pesa → NetPay URLs on
            each shortcode.
          </p>
        </div>
      </div>
      <p className="mb-4 text-xs text-[var(--muted)]">
        <Link to="/integrations">← Paybills &amp; tills</Link>
        {' · '}
        <Link to="/intents">Take a payment</Link>
      </p>
      {error && <div className={errorAlert} role="alert">{error}</div>}
      {msg && <div className={successAlert} role="status">{msg}</div>}
      {secretOnce && (
        <div className="mb-4 rounded-lg border border-[var(--accent-2)]/30 bg-[var(--accent-2)]/10 px-4 py-3 text-sm text-[var(--text)]">
          <strong>Copy this signing secret now — it won’t be shown again.</strong>
          <div className="mt-2 break-all font-mono text-xs">{secretOnce}</div>
          <div className="mt-2 flex flex-wrap gap-2">
            <button type="button" className={primaryButton} onClick={copySecret}>
              Copy secret
            </button>
            <button type="button" className={button} onClick={() => setSecretAck(true)}>
              I’ve copied it
            </button>
          </div>
          {secretAck && <p className="mt-2 text-xs text-[var(--muted)]">You can leave this page. Store the secret in your app config.</p>}
        </div>
      )}

      <div className={card}>
        <h2 className="mb-3 text-base font-semibold">Add a notification URL</h2>
        {isAdmin && (
          <>
            <label className={label}>Business</label>
            <select className={control} value={tenantId} onChange={(e) => setSelectedTenantId(e.target.value)}>
              <option value="">Select…</option>
              {tenants.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
            {!tenantId && tenants.length === 0 && (
              <p className="text-xs text-[var(--muted)]">No businesses yet. Create one under Businesses first.</p>
            )}
          </>
        )}
        <form onSubmit={onCreate}>
          <label className={label}>HTTPS address</label>
          <input
            className={control}
            type="url"
            required
            pattern="https://.*"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://your-app.com/hooks/payments"
          />
          <button className={`${primaryButton} mt-4`} type="submit" disabled={busy || !tenantId}>
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
        <div className={tableWrap}>
          <table className={table}>
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
                  <td className={`${mono} max-w-64 break-all`}>{w.url}</td>
                  <td className="text-xs text-[var(--muted)]">
                    {w.last_live_at ? new Date(w.last_live_at).toLocaleString() : '—'}
                  </td>
                  <td>
                    <button type="button" className={dangerButton} onClick={() => onDelete(w.id)}>
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
