import { type FormEvent, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, ApiError, type Integration, type PaymentIntent } from '../api/client'
import { EmptyState } from '../components/EmptyState'
import { StatusBadge } from '../components/StatusBadge'

export function PaymentIntents() {
  const [items, setItems] = useState<PaymentIntent[]>([])
  const [integrations, setIntegrations] = useState<Integration[]>([])
  const [error, setError] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [busy, setBusy] = useState(false)
  const [form, setForm] = useState({
    integration_public_id: '',
    phone: '254708374149',
    amount: '1',
    account_reference: 'TEST',
    description: 'NetHub test',
  })

  async function load() {
    try {
      setItems(await api.get<PaymentIntent[]>('/v1/payment-intents'))
      setIntegrations(await api.get<Integration[]>('/v1/integrations'))
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
      await api.post('/v1/payment-intents', {
        ...form,
        amount: Number(form.amount),
      })
      setShowForm(false)
      await load()
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'STK initiate failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div data-testid="intents-page">
      <div className="page-header">
        <div>
          <h1>Payment intents</h1>
          <p>STK Push collections · matched on CheckoutRequestID</p>
        </div>
        <button className="btn primary" type="button" onClick={() => setShowForm((v) => !v)}>
          {showForm ? 'Cancel' : 'New STK Push'}
        </button>
      </div>
      {error && <div className="alert error">{error}</div>}

      {showForm && (
        <div className="card">
          <h2>Initiate STK</h2>
          <form onSubmit={onCreate}>
            <label>Integration</label>
            <select required value={form.integration_public_id} onChange={(e) => setForm({ ...form, integration_public_id: e.target.value })}>
              <option value="">Select</option>
              {integrations.map((i) => (
                <option key={i.id} value={i.public_id}>{i.public_id} · {i.shortcode}</option>
              ))}
            </select>
            <div className="grid-2">
              <div>
                <label>Phone (MSISDN)</label>
                <input required value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
              </div>
              <div>
                <label>Amount (KES)</label>
                <input required type="number" min="1" step="1" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} />
              </div>
              <div>
                <label>Account reference</label>
                <input value={form.account_reference} onChange={(e) => setForm({ ...form, account_reference: e.target.value })} maxLength={12} />
              </div>
              <div>
                <label>Description</label>
                <input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} maxLength={32} />
              </div>
            </div>
            <button className="btn primary" type="submit" disabled={busy}>{busy ? 'Sending…' : 'Send STK'}</button>
          </form>
        </div>
      )}

      {items.length === 0 ? (
        <EmptyState title="No payment intents" hint="Create an STK Push against a configured integration." />
      ) : (
        <div className="card">
          <table>
            <thead>
              <tr><th>Status</th><th>Amount</th><th>Phone</th><th>Checkout ID</th><th>Created</th><th></th></tr>
            </thead>
            <tbody>
              {items.map((p) => (
                <tr key={p.id}>
                  <td><StatusBadge value={p.status} /></td>
                  <td>{p.amount} {p.currency}</td>
                  <td className="mono">{p.phone}</td>
                  <td className="mono tiny">{p.provider_checkout_id || '—'}</td>
                  <td className="muted tiny">{new Date(p.created_at).toLocaleString()}</td>
                  <td><Link to={`/intents/${p.id}`}>Open</Link></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
