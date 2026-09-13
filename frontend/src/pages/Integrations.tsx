import { type FormEvent, useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { api, ApiError, type Integration, type Tenant, type Webhook } from '../api/client'
import { EmptyState } from '../components/EmptyState'
import { StatusBadge } from '../components/StatusBadge'
import { useAuth } from '../auth/AuthContext'

export function Integrations() {
  const { isAdmin, user } = useAuth()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const presetTenant = params.get('tenant_id') || user?.tenant_id || ''
  const [items, setItems] = useState<Integration[]>([])
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [webhookCount, setWebhookCount] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [msg, setMsg] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [busy, setBusy] = useState(false)
  const [form, setForm] = useState({
    tenant_id: presetTenant,
    shortcode: '',
    type: 'paybill',
    environment: 'sandbox',
    consumer_key: '',
    consumer_secret: '',
    passkey: '',
  })


  async function load() {
    try {
      const integ = await api.get<Integration[]>('/v1/integrations')
      setItems(integ)
      if (isAdmin) {
        try {
          setTenants(await api.get<Tenant[]>('/v1/tenants'))
        } catch {
          /* ignore */
        }
      }
      const tid = user?.tenant_id || form.tenant_id
      if (tid) {
        try {
          const hooks = await api.get<Webhook[]>(`/v1/webhooks?tenant_id=${tid}`)
          setWebhookCount(hooks.length)
        } catch {
          setWebhookCount(0)
        }
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Could not load paybills & tills')
    }
  }

  useEffect(() => {
    load()
  }, [])

  async function onCreate(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    setMsg(null)
    const tenant_id = isAdmin ? form.tenant_id : user?.tenant_id || ''
    if (!tenant_id) {
      setError(
        isAdmin
          ? 'Choose a business before saving.'
          : 'Your account isn’t linked to a business. Ask an admin to link you, then try again.',
      )
      setBusy(false)
      return
    }
    try {
      const created = await api.post<Integration>('/v1/integrations', { ...form, tenant_id })
      setShowForm(false)
      setMsg('Shortcode saved. Next: connect M-Pesa so Safaricom can send results to NetPay.')
      await load()
      if (created?.id) {
        navigate(`/integrations/${created.id}`)
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Could not save')
    } finally {
      setBusy(false)
    }
  }

  async function onRetire(id: string, shortcode: string) {
    const ok = window.confirm(
      `Retire shortcode ${shortcode}?\n\nIt will no longer appear in your list. Existing payments keep their history. You can add the shortcode again later if needed.`,
    )
    if (!ok) return
    setBusy(true)
    setError(null)
    try {
      await api.delete(`/v1/integrations/${id}`)
      setMsg(`Shortcode ${shortcode} was retired.`)
      await load()
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Could not retire this shortcode')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div data-testid="integrations-page">
      <div className="page-header">
        <div>
          <h1>Paybills &amp; tills</h1>
          <p>Your M-Pesa shortcodes — the numbers customers pay to.</p>
        </div>
        <button className="btn primary" type="button" onClick={() => setShowForm((v) => !v)}>
          {showForm ? 'Cancel' : 'Add shortcode'}
        </button>
      </div>
      {error && <div className="alert error">{error}</div>}
      {msg && <div className="alert ok">{msg}</div>}

      <div className="card">
        <h2>Setup checklist</h2>
        <p className="muted tiny" style={{ marginTop: 0 }}>
          Complete these so payments can settle and your app can be notified.
        </p>
        <ol style={{ margin: '0.5rem 0 0', paddingLeft: '1.25rem' }}>
          <li>
            <strong>Add a shortcode</strong>
            {items.length > 0 ? ' — done' : ' — use Add shortcode'}
          </li>
          <li>
            <strong>Connect M-Pesa</strong> — open a shortcode and register URLs with Safaricom
            {items[0] && (
              <>
                {' '}
                (<Link to={`/integrations/${items[0].id}`}>open latest</Link>)
              </>
            )}
          </li>
          <li>
            <strong>Notify your app</strong> —{' '}
            <Link to="/webhooks">Payment notifications</Link>
            {webhookCount > 0 ? ' — at least one URL saved' : ' — add an HTTPS URL'}
          </li>
        </ol>
      </div>

      {showForm && (
        <div className="card">
          <h2>Add a paybill or till</h2>
          <p className="muted tiny">
            Use the shortcode and API details from the Safaricom Daraja portal (sandbox or live).
          </p>
          <form onSubmit={onCreate}>
            {isAdmin && (
              <>
                <label>Business</label>
                <select
                  required
                  value={form.tenant_id}
                  onChange={(e) => setForm({ ...form, tenant_id: e.target.value })}
                >
                  <option value="">Select…</option>
                  {tenants.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name}
                    </option>
                  ))}
                </select>
              </>
            )}
            {!isAdmin && !user?.tenant_id && (
              <div className="alert error">
                Your account isn’t linked to a business. Ask an admin to link you before adding a shortcode.
              </div>
            )}
            <div className="grid-3">
              <div>
                <label>Shortcode</label>
                <input
                  required
                  value={form.shortcode}
                  onChange={(e) => setForm({ ...form, shortcode: e.target.value })}
                  placeholder="e.g. 174379"
                />
              </div>
              <div>
                <label>Type</label>
                <select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>
                  <option value="paybill">Paybill</option>
                  <option value="till">Till number</option>
                </select>
              </div>
              <div>
                <label>Environment</label>
                <select
                  value={form.environment}
                  onChange={(e) => setForm({ ...form, environment: e.target.value })}
                >
                  <option value="sandbox">Test (sandbox)</option>
                  <option value="production">Live</option>
                </select>
              </div>
            </div>
            <label>Consumer key</label>
            <input
              required
              value={form.consumer_key}
              onChange={(e) => setForm({ ...form, consumer_key: e.target.value })}
              autoComplete="off"
            />
            <label>Consumer secret</label>
            <input
              required
              type="password"
              value={form.consumer_secret}
              onChange={(e) => setForm({ ...form, consumer_secret: e.target.value })}
              autoComplete="off"
            />
            <label>Passkey (Lipa Na M-Pesa)</label>
            <input
              required
              type="password"
              value={form.passkey}
              onChange={(e) => setForm({ ...form, passkey: e.target.value })}
              autoComplete="off"
            />
            <button
              className="btn primary"
              type="submit"
              disabled={busy || (!isAdmin && !user?.tenant_id) || (isAdmin && !form.tenant_id)}
            >
              {busy ? 'Saving…' : 'Save shortcode'}
            </button>
          </form>
        </div>
      )}

      {items.length === 0 ? (
        <EmptyState
          title="No paybills or tills yet"
          hint="Add a shortcode to start sending payment requests to customers."
        />
      ) : (
        <div className="card">
          <table>
            <thead>
              <tr>
                <th>Shortcode</th>
                <th>Type</th>
                <th>Environment</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items.map((i) => (
                <tr key={i.id}>
                  <td>
                    <strong>{i.shortcode}</strong>
                    <div className="muted tiny mono">{i.public_id}</div>
                  </td>
                  <td>{i.type === 'till' ? 'Till' : 'Paybill'}</td>
                  <td>{i.environment === 'production' ? 'Live' : 'Test'}</td>
                  <td>
                    <StatusBadge value={i.status} />
                  </td>
                  <td style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                    <Link to={`/integrations/${i.id}`}>Open</Link>
                    <button
                      type="button"
                      className="btn danger"
                      disabled={busy}
                      onClick={() => onRetire(i.id, i.shortcode)}
                    >
                      Retire
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
