import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api, ApiError, type PaymentIntent } from '../api/client'
import { StatusBadge } from '../components/StatusBadge'

export function PaymentIntentDetail() {
  const { id } = useParams()
  const [item, setItem] = useState<PaymentIntent | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [msg, setMsg] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function load() {
    try {
      setItem(await api.get<PaymentIntent>(`/v1/payment-intents/${id}`))
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Not found')
    }
  }

  useEffect(() => { load() }, [id])

  async function simulate() {
    setBusy(true)
    setError(null)
    setMsg(null)
    try {
      await api.post(`/v1/payment-intents/${id}/simulate`, { result_code: '0', result_desc: 'Success (simulated)' })
      setMsg('Simulated success callback applied')
      await load()
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Simulate failed')
    } finally {
      setBusy(false)
    }
  }

  if (error && !item) return <div className="alert error" data-testid="intent-detail-page">{error}</div>
  if (!item) return <div data-testid="intent-detail-page">Loading…</div>

  return (
    <div data-testid="intent-detail-page">
      <div className="page-header">
        <div>
          <h1>Intent</h1>
          <p className="mono">{item.id}</p>
        </div>
        <StatusBadge value={item.status} />
      </div>
      {error && <div className="alert error">{error}</div>}
      {msg && <div className="alert ok">{msg}</div>}

      <div className="grid-2">
        <div className="card">
          <h2>Payment</h2>
          <p><span className="muted">Amount</span><br /><strong>{item.amount} {item.currency}</strong></p>
          <p><span className="muted">Phone</span><br /><span className="mono">{item.phone}</span></p>
          <p><span className="muted">Reference</span><br />{item.account_reference || '—'}</p>
          <p><span className="muted">Description</span><br />{item.description || '—'}</p>
        </div>
        <div className="card">
          <h2>Provider</h2>
          <p><span className="muted">CheckoutRequestID</span><br /><span className="mono">{item.provider_checkout_id || '—'}</span></p>
          <p><span className="muted">MerchantRequestID</span><br /><span className="mono">{item.provider_merchant_id || '—'}</span></p>
          <p><span className="muted">Transaction ID</span><br /><span className="mono">{item.provider_transaction_id || '—'}</span></p>
          {item.failure_reason && <p><span className="muted">Failure</span><br />{item.failure_reason}</p>}
        </div>
      </div>

      <div className="card">
        <h2>Dev tools</h2>
        <p className="muted">Simulate a successful STK callback without waiting for Daraja (sandbox / test only).</p>
        <button className="btn" type="button" onClick={simulate} disabled={busy}>{busy ? 'Applying…' : 'Simulate success callback'}</button>
      </div>
    </div>
  )
}
