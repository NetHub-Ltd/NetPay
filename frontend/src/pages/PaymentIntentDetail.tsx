import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, ApiError, type PaymentIntent } from '../api/client'
import { StatusBadge, formatKes, statusHint } from '../components/StatusBadge'

type LedgerRow = {
  id: string
  entry_type: string
  amount_minor: number
  currency: string
  provider_ref?: string | null
  created_at?: string
}

const STEPS = ['created', 'provider_requested', 'succeeded'] as const

function stepIndex(status: string): number {
  if (status === 'succeeded') return 2
  if (status === 'provider_requested') return 1
  if (status === 'failed' || status === 'expired') return 1
  return 0
}

export function PaymentIntentDetail() {
  const { id } = useParams()
  const [item, setItem] = useState<PaymentIntent | null>(null)
  const [ledger, setLedger] = useState<LedgerRow[]>([])
  const [error, setError] = useState<string | null>(null)
  const [msg, setMsg] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function load() {
    try {
      setItem(await api.get<PaymentIntent>(`/v1/payment-intents/${id}`))
      try {
        setLedger(await api.get<LedgerRow[]>(`/v1/payment-intents/${id}/ledger`))
      } catch {
        setLedger([])
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Not found')
    }
  }

  useEffect(() => {
    load()
  }, [id])

  async function simulate() {
    setBusy(true)
    setError(null)
    setMsg(null)
    try {
      await api.post(`/v1/payment-intents/${id}/simulate`, {})
      setMsg('Simulated success applied — ledger should show a collection credit.')
      await load()
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Simulate failed')
    } finally {
      setBusy(false)
    }
  }

  if (error && !item) return <div className="alert error" data-testid="intent-detail-page">{error}</div>
  if (!item) return <div data-testid="intent-detail-page">Loading…</div>

  const idx = stepIndex(item.status)
  const terminalBad = item.status === 'failed' || item.status === 'expired'

  return (
    <div data-testid="intent-detail-page">
      <div className="page-header">
        <div>
          <p className="muted" style={{ margin: 0 }}>
            <Link to="/intents">← Payments</Link>
          </p>
          <h1>Payment</h1>
          <p className="mono muted">{item.id}</p>
        </div>
        <StatusBadge value={item.status} />
      </div>

      {error && <div className="alert error">{error}</div>}
      {item.failure_reason && (
        <div className="alert error">Could not complete: {item.failure_reason}</div>
      )}
      {msg && <div className="alert ok">{msg}</div>}

      {(item as { stk_request_json?: string; stk_response_json?: string; status_callback_url?: string }).stk_request_json && (
        <div className="card" style={{ marginBottom: '1rem' }}>
          <h2>Provider call</h2>
          <p className="muted tiny" style={{ marginTop: 0 }}>
            What we sent to the network and what came back (secrets redacted).
          </p>
          <div className="muted tiny">Request</div>
          <pre className="mono tiny" style={{ whiteSpace: 'pre-wrap', maxHeight: 180, overflow: 'auto' }}>
            {(item as { stk_request_json?: string }).stk_request_json}
          </pre>
          <div className="muted tiny">Response</div>
          <pre className="mono tiny" style={{ whiteSpace: 'pre-wrap', maxHeight: 180, overflow: 'auto' }}>
            {(item as { stk_response_json?: string }).stk_response_json || '—'}
          </pre>
        </div>
      )}


      <div className="card" style={{ marginBottom: '1rem' }}>
        <p style={{ marginTop: 0 }}>{statusHint(item.status)}</p>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
          {STEPS.map((s, i) => (
            <span
              key={s}
              className={`badge ${i <= idx && !terminalBad ? 'status-ok' : terminalBad && i <= idx ? 'status-err' : 'status-neutral'}`}
            >
              {s === 'provider_requested' ? 'Waiting' : s === 'succeeded' ? 'Paid' : 'Created'}
            </span>
          ))}
          {terminalBad && <StatusBadge value={item.status} />}
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <h2>Summary</h2>
          <p>
            <span className="muted">Amount</span>
            <br />
            <strong>{formatKes(item.amount_minor, item.amount, item.currency)}</strong>
          </p>
          <p>
            <span className="muted">Phone</span>
            <br />
            <span className="mono">{item.phone}</span>
          </p>
          <p>
            <span className="muted">Reference</span>
            <br />
            {item.account_reference || '—'}
          </p>
          {item.failure_reason && (
            <p>
              <span className="muted">Reason</span>
              <br />
              {item.failure_reason}
            </p>
          )}
        </div>
        <div className="card">
          <h2>Provider</h2>
          <p>
            <span className="muted">Checkout ID</span>
            <br />
            <span className="mono">{item.provider_checkout_id || '—'}</span>
          </p>
          <p>
            <span className="muted">Receipt / txn</span>
            <br />
            <span className="mono">{item.provider_transaction_id || '—'}</span>
          </p>
          {(item.status === 'created' || item.status === 'provider_requested') && (
            <button className="btn" type="button" disabled={busy} onClick={simulate}>
              {busy ? 'Working…' : 'Simulate success (dev)'}
            </button>
          )}
          {(item.status === 'failed' || item.status === 'expired') && (
            <p>
              <Link className="btn primary" to="/intents">
                Start a new payment
              </Link>
            </p>
          )}
        </div>
      </div>

      <div className="card" style={{ marginTop: '1rem' }}>
        <h2>Ledger</h2>
        {ledger.length === 0 ? (
          <p className="muted">No ledger entries yet. A collection credit appears when status becomes Paid.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Type</th>
                <th>Amount</th>
                <th>Provider ref</th>
                <th>When</th>
              </tr>
            </thead>
            <tbody>
              {ledger.map((row) => (
                <tr key={row.id}>
                  <td>{row.entry_type}</td>
                  <td>{formatKes(row.amount_minor, null, row.currency)}</td>
                  <td className="mono">{row.provider_ref || '—'}</td>
                  <td className="muted">{row.created_at ? new Date(row.created_at).toLocaleString() : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
