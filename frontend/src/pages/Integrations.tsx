import { type FormEvent, useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api, ApiError, type Integration, type Tenant } from '../api/client'
import { EmptyState } from '../components/EmptyState'
import { StatusBadge } from '../components/StatusBadge'
import { useAuth } from '../auth/AuthContext'

export function Integrations() {
  const { isAdmin } = useAuth()
  const [params] = useSearchParams()
  const presetTenant = params.get('tenant_id') || ''
  const [items, setItems] = useState<Integration[]>([])
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [error, setError] = useState<string | null>(null)
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
        try { setTenants(await api.get<Tenant[]>('/v1/tenants')) } catch { /* ignore */ }
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Failed to load')
    }
  }

  useEffect(() => { load() }, [])

  async function onCreate(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await api.post('/v1/integrations', form)
      setShowForm(false)
      await load()
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Create failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div data-testid="integrations-page">
      <div className="page-header">
        <div>
          <h1>Integrations</h1>
          <p>Paybill / Till + Daraja credentials (public id gw_…)</p>
        </div>
        <button className="btn primary" type="button" onClick={() => setShowForm((v) => !v)}>
          {showForm ? 'Cancel' : 'Add integration'}
        </button>
      </div>
      {error && <div className="alert error">{error}</div>}

      {showForm && (
        <div className="card">
          <h2>Sandbox / production credentials</h2>
          <form onSubmit={onCreate}>
            {isAdmin && (
              <>
                <label>Tenant</label>
                <select required value={form.tenant_id} onChange={(e) => setForm({ ...form, tenant_id: e.target.value })}>
                  <option value="">Select tenant</option>
                  {tenants.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
                </select>
              </>
            )}
            {!isAdmin && <input type="hidden" value={form.tenant_id} />}
            <div className="grid-2">
              <div>
                <label>Shortcode</label>
                <input required value={form.shortcode} onChange={(e) => setForm({ ...form, shortcode: e.target.value })} placeholder="174379" />
              </div>
              <div>
                <label>Type</label>
                <select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>
                  <option value="paybill">Paybill</option>
                  <option value="till">Till</option>
                </select>
              </div>
              <div>
                <label>Environment</label>
                <select value={form.environment} onChange={(e) => setForm({ ...form, environment: e.target.value })}>
                  <option value="sandbox">Sandbox</option>
                  <option value="production">Production</option>
                </select>
              </div>
            </div>
            <label>Consumer key</label>
            <input required value={form.consumer_key} onChange={(e) => setForm({ ...form, consumer_key: e.target.value })} autoComplete="off" />
            <label>Consumer secret</label>
            <input required type="password" value={form.consumer_secret} onChange={(e) => setForm({ ...form, consumer_secret: e.target.value })} autoComplete="off" />
            <label>Passkey</label>
            <input required type="password" value={form.passkey} onChange={(e) => setForm({ ...form, passkey: e.target.value })} autoComplete="off" />
            <button className="btn primary" type="submit" disabled={busy}>{busy ? 'Saving…' : 'Save integration'}</button>
          </form>
        </div>
      )}

      {items.length === 0 ? (
        <EmptyState title="No integrations" hint="Add sandbox M-Pesa credentials to start STK / C2B." />
      ) : (
        <div className="card">
          <table>
            <thead>
              <tr><th>Public ID</th><th>Shortcode</th><th>Env</th><th>Status</th><th></th></tr>
            </thead>
            <tbody>
              {items.map((i) => (
                <tr key={i.id}>
                  <td className="mono">{i.public_id}</td>
                  <td>{i.shortcode}</td>
                  <td><StatusBadge value={i.environment} /></td>
                  <td><StatusBadge value={i.status} /></td>
                  <td><Link to={`/integrations/${i.id}`}>Open</Link></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
