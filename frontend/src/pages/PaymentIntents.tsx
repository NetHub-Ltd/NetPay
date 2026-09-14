import { type FormEvent, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { subscribeLiveMessages } from '../hooks/useWebSocket'
import { api, ApiError, type Integration, type PaymentIntent } from '../api/client'
import { DataTable } from '../components/DataTable'
import { StatusBadge, formatKes, statusHint, paymentLifecycleBucket } from '../components/StatusBadge'

export function PaymentIntents() {
  const navigate = useNavigate()
  const [items, setItems] = useState<PaymentIntent[]>([])
  const [integrations, setIntegrations] = useState<Integration[]>([])
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [busy, setBusy] = useState(false)
  const [lastCreatedId, setLastCreatedId] = useState<string | null>(null)
  const [form, setForm] = useState({
    integration_public_id: '',
    phone: '',
    amount: '1',
    account_reference: 'PAY',
    description: 'Payment',
  })
  const [showAdvanced, setShowAdvanced] = useState(false)

  async function load() {
    try {
      setItems(await api.get<PaymentIntent[]>('/v1/payment-intents'))
      const integ = await api.get<Integration[]>('/v1/integrations')
      setIntegrations(integ)
      if (!form.integration_public_id && integ[0]?.public_id) {
        setForm((f) => ({ ...f, integration_public_id: integ[0].public_id }))
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Failed to load payments')
    }
  }

  useEffect(() => {
    load()
  }, [])

  useEffect(() => {
    return subscribeLiveMessages((m) => {
      if (m.type === 'payment.update' || m.type === 'notification') load()
    })
  }, [])

  async function onCreate(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    setSuccess(null)
    try {
      const amountMajor = Number(form.amount)
      if (!amountMajor || amountMajor < 1) {
        setError('Enter an amount of at least 1 KES')
        return
      }
      const amount_minor = Math.round(amountMajor * 100)
      const idempotencyKey =
        typeof crypto !== 'undefined' && 'randomUUID' in crypto
          ? crypto.randomUUID()
          : `web-${Date.now()}-${Math.random().toString(36).slice(2)}`
      const res = await api.post<{ id: string; status: string; idempotent_replay?: boolean }>(
        '/v1/payment-intents',
        {
          integration_public_id: form.integration_public_id,
          phone: form.phone,
          amount_minor,
          account_reference: form.account_reference,
          description: form.description,
        },
        { headers: { 'Idempotency-Key': idempotencyKey } },
      )
      setLastCreatedId(res.id)
      setSuccess(
        res.idempotent_replay
          ? 'Same request was already sent — showing the original payment.'
          : 'STK push sent. Ask the customer to enter their M-Pesa PIN.',
      )
      setShowForm(false)
      await load()
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Could not start payment')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div data-testid="intents-page">
      <div className="page-header">
        <div>
          <h1>Payments</h1>
          <p>Collect money with M-Pesa STK Push. Status updates when the customer completes the prompt.</p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <Link className="btn" to="/docs">Help</Link>
          <button className="btn primary" type="button" onClick={() => setShowForm((v) => !v)}>
            {showForm ? 'Cancel' : 'Take a payment'}
          </button>
        </div>
      </div>

      {error && <div className="alert error">{error}</div>}
      {success && (
        <div className="alert ok">
          {success}{' '}
          {lastCreatedId && (
            <Link to={`/intents/${lastCreatedId}`}>View payment</Link>
          )}
        </div>
      )}

      {showForm && (
        <form className="card" onSubmit={onCreate} style={{ marginBottom: '1rem' }}>
          <h2 style={{ marginTop: 0 }}>New payment</h2>
          <p className="muted" style={{ marginTop: 0 }}>
            We generate a secure idempotency key automatically so double-clicks cannot charge twice.
          </p>
          <label>
            Integration
            <select
              required
              value={form.integration_public_id}
              onChange={(e) => setForm({ ...form, integration_public_id: e.target.value })}
            >
              <option value="">Select…</option>
              {integrations.map((i) => (
                <option key={i.id} value={i.public_id}>
                  {i.public_id} ({i.shortcode})
                </option>
              ))}
            </select>
          </label>
          <label>
            Customer phone
            <input
              required
              placeholder="2547…"
              value={form.phone}
              onChange={(e) => setForm({ ...form, phone: e.target.value })}
            />
          </label>
          <label>
            Amount (KES)
            <input
              required
              type="number"
              min="1"
              step="1"
              value={form.amount}
              onChange={(e) => setForm({ ...form, amount: e.target.value })}
            />
          </label>
          <button type="button" className="btn" onClick={() => setShowAdvanced((v) => !v)}>
            {showAdvanced ? 'Hide advanced' : 'Advanced options'}
          </button>
          {showAdvanced && (
            <>
              <label>
                Account reference
                <input
                  maxLength={12}
                  value={form.account_reference}
                  onChange={(e) => setForm({ ...form, account_reference: e.target.value })}
                />
              </label>
              <label>
                Description
                <input
                  maxLength={32}
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                />
              </label>
            </>
          )}
          <div style={{ marginTop: '0.75rem' }}>
            <button className="btn primary" type="submit" disabled={busy}>
              {busy ? 'Sending…' : 'Send STK Push'}
            </button>
          </div>
        </form>
      )}

      <DataTable
        rows={items}
        getRowId={(p) => p.id}
        searchPlaceholder="Search phone, amount…"
        defaultPageSize={10}
        maxHeight="min(440px, 55vh)"
        emptyTitle="No payments yet"
        emptyHint="Use “Take a payment” to send a prompt to a customer’s phone."
        filters={[
          { id: 'processing', label: 'Processing' },
          { id: 'successful', label: 'Successful' },
          { id: 'failed', label: 'Failed' },
        ]}
        filterFn={(p, id) => paymentLifecycleBucket(p.status) === id}
        onRowClick={(p) => navigate(`/intents/${p.id}`)}
        columns={[
          {
            id: 'status',
            header: 'Status',
            searchValue: (p) => `${p.status} ${p.failure_reason || ''}`,
            cell: (p) => (
              <>
                <StatusBadge value={p.status} />
                {p.failure_reason && (
                  <div className="muted tiny" style={{ maxWidth: 220 }}>
                    {p.failure_reason}
                  </div>
                )}
                {!p.failure_reason && p.status === 'provider_requested' && (
                  <div className="muted tiny">{statusHint(p.status)}</div>
                )}
              </>
            ),
          },
          {
            id: 'amount',
            header: 'Amount',
            searchValue: (p) => formatKes(p.amount_minor, p.amount, p.currency),
            cell: (p) => formatKes(p.amount_minor, p.amount, p.currency),
          },
          {
            id: 'phone',
            header: 'Phone',
            searchValue: (p) => p.phone || '',
            cell: (p) => <span className="mono">{p.phone}</span>,
          },
          {
            id: 'when',
            header: 'When',
            searchValue: (p) => p.created_at || '',
            cell: (p) => (
              <span className="muted">
                {p.created_at ? new Date(p.created_at).toLocaleString() : '—'}
              </span>
            ),
          },
          {
            id: 'open',
            header: '',
            cell: (p) => (
              <Link to={`/intents/${p.id}`} onClick={(e) => e.stopPropagation()}>
                Open
              </Link>
            ),
          },
        ]}
      />
    </div>
  )
}
