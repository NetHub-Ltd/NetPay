import { useEffect, useMemo, useState } from 'react'
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

type TimelineStep = {
  at?: string
  kind: string
  label: string
  success?: boolean
  failure_reason?: string
  status?: string
}

function parseJson(raw?: string | null): Record<string, unknown> | null {
  if (!raw) return null
  try {
    const v = typeof raw === 'string' ? JSON.parse(raw) : raw
    return v && typeof v === 'object' ? (v as Record<string, unknown>) : null
  } catch {
    return null
  }
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="detail-field">
      <div className="detail-field-label">{label}</div>
      <div className="detail-field-value">{children}</div>
    </div>
  )
}

function KvTable({ data, prefer }: { data: Record<string, unknown>; prefer?: string[] }) {
  const keys = prefer?.filter((k) => data[k] !== undefined && data[k] !== null && data[k] !== '') || []
  const rest = Object.keys(data).filter((k) => !keys.includes(k) && data[k] !== undefined && data[k] !== null && data[k] !== '')
  const ordered = [...keys, ...rest]
  if (ordered.length === 0) return <p className="muted tiny">No fields</p>
  return (
    <dl className="kv-list">
      {ordered.map((k) => {
        const v = data[k]
        const display =
          typeof v === 'object' ? JSON.stringify(v) : String(v)
        return (
          <div className="kv-row" key={k}>
            <dt>{k}</dt>
            <dd className={typeof v === 'string' && v.length > 24 ? 'mono tiny' : undefined}>{display}</dd>
          </div>
        )
      })}
    </dl>
  )
}

const REQUEST_PREFER = [
  'BusinessShortCode',
  'Amount',
  'PartyA',
  'PhoneNumber',
  'PartyB',
  'TransactionType',
  'AccountReference',
  'TransactionDesc',
  'CallBackURL',
  'Timestamp',
]
const RESPONSE_PREFER = [
  'ResponseCode',
  'ResponseDescription',
  'CustomerMessage',
  'CheckoutRequestID',
  'MerchantRequestID',
  'ResultCode',
  'ResultDesc',
]

export function PaymentIntentDetail() {
  const { id } = useParams()
  const [item, setItem] = useState<PaymentIntent | null>(null)
  const [ledger, setLedger] = useState<LedgerRow[]>([])
  const [error, setError] = useState<string | null>(null)
  const [msg, setMsg] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [timeline, setTimeline] = useState<{ steps: TimelineStep[] } | null>(null)
  const [showTech, setShowTech] = useState(false)

  async function load() {
    try {
      setItem(await api.get<PaymentIntent>(`/v1/payment-intents/${id}`))
      try {
        setLedger(await api.get<LedgerRow[]>(`/v1/payment-intents/${id}/ledger`))
      } catch {
        setLedger([])
      }
      try {
        setTimeline(await api.get(`/v1/payment-intents/${id}/timeline`))
      } catch {
        setTimeline(null)
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Not found')
    }
  }

  useEffect(() => {
    load()
  }, [id])

  async function queryNetwork() {
    setBusy(true)
    setError(null)
    setMsg(null)
    try {
      await api.post(`/v1/payment-intents/${id}/query-provider`, {})
      setMsg('Asked the network for the latest result.')
      await load()
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Network query failed')
    } finally {
      setBusy(false)
    }
  }

  async function simulate() {
    setBusy(true)
    setError(null)
    setMsg(null)
    try {
      await api.post(`/v1/payment-intents/${id}/simulate`, {})
      setMsg('Simulated success applied.')
      await load()
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Simulate failed')
    } finally {
      setBusy(false)
    }
  }

  const req = useMemo(() => parseJson(item?.stk_request_json), [item?.stk_request_json])
  const res = useMemo(() => parseJson(item?.stk_response_json), [item?.stk_response_json])

  if (error && !item) return <div className="alert error" data-testid="intent-detail-page">{error}</div>
  if (!item) return <div data-testid="intent-detail-page">Loading…</div>

  const hint = statusHint(item.status, item.failure_reason)
  const steps = timeline?.steps || []

  return (
    <div data-testid="intent-detail-page" className="payment-detail">
      <div className="page-header">
        <div>
          <p className="muted" style={{ margin: 0 }}>
            <Link to="/intents">← Payments</Link>
          </p>
          <h1>
            {formatKes(item.amount_minor, item.amount, item.currency)}
            <span className="muted" style={{ fontWeight: 500, fontSize: '1rem', marginLeft: '0.65rem' }}>
              to {item.phone}
            </span>
          </h1>
          <p className="muted tiny" style={{ margin: '0.25rem 0 0' }}>
            {item.created_at ? new Date(item.created_at).toLocaleString() : ''}
            {item.account_reference ? ` · Ref ${item.account_reference}` : ''}
          </p>
        </div>
        <StatusBadge value={item.status} />
      </div>

      {error && <div className="alert error">{error}</div>}
      {item.failure_reason && item.status !== 'succeeded' && (
        <div className="alert error">{item.failure_reason}</div>
      )}
      {msg && <div className="alert ok">{msg}</div>}
      {hint && !item.failure_reason && (
        <p className="muted" style={{ marginTop: 0 }}>
          {hint}
        </p>
      )}

      <div className="detail-grid">
        <section className="card detail-main">
          <h2>Timeline</h2>
          {steps.length === 0 ? (
            <p className="muted tiny">No timeline events yet.</p>
          ) : (
            <ol className="detail-timeline">
              {steps.map((s, i) => (
                <li key={i} className={s.success === false ? 'is-bad' : s.kind === 'status' && (s.label === 'Paid' || s.status === 'succeeded') ? 'is-good' : ''}>
                  <div className="detail-timeline-dot" aria-hidden />
                  <div className="detail-timeline-body">
                    <div className="detail-timeline-label">{s.label}</div>
                    <div className="muted tiny">
                      {s.at ? new Date(s.at).toLocaleString() : ''}
                      {s.failure_reason ? ` · ${s.failure_reason}` : ''}
                      {s.success === false ? ' · did not succeed' : ''}
                    </div>
                  </div>
                </li>
              ))}
            </ol>
          )}
        </section>

        <aside className="detail-side">
          <section className="card">
            <h2>Summary</h2>
            <Field label="Amount">{formatKes(item.amount_minor, item.amount, item.currency)}</Field>
            <Field label="Phone">
              <span className="mono">{item.phone}</span>
            </Field>
            <Field label="Reference">{item.account_reference || '—'}</Field>
            <Field label="Description">{item.description || '—'}</Field>
            {item.status_callback_url && (
              <Field label="Status callback">
                <span className="mono tiny">{item.status_callback_url}</span>
              </Field>
            )}
          </section>

          <section className="card">
            <h2>Network</h2>
            <Field label="Checkout ID">
              <span className="mono tiny">{item.provider_checkout_id || '—'}</span>
            </Field>
            <Field label="Receipt / txn">
              <span className="mono tiny">{item.provider_transaction_id || '—'}</span>
            </Field>
            <div className="detail-actions">
              {(item.status === 'created' || item.status === 'provider_requested') && item.provider_checkout_id && (
                <button className="btn" type="button" disabled={busy} onClick={queryNetwork}>
                  {busy ? 'Checking…' : 'Check with network'}
                </button>
              )}
              {(item.status === 'created' || item.status === 'provider_requested') && (
                <button className="btn" type="button" disabled={busy} onClick={simulate}>
                  {busy ? 'Working…' : 'Simulate success (dev)'}
                </button>
              )}
              {(item.status === 'failed' || item.status === 'expired') && (
                <Link className="btn primary" to="/intents">
                  Start a new payment
                </Link>
              )}
            </div>
          </section>
        </aside>
      </div>

      {(req || res) && (
        <section className="card" style={{ marginTop: '1rem' }}>
          <h2>Phone prompt exchange</h2>
          <p className="muted tiny" style={{ marginTop: 0 }}>
            What we sent to the network and what came back. Secrets are redacted.
          </p>
          <div className="detail-exchange">
            {req && (
              <div>
                <h3 className="detail-subhead">Request</h3>
                <KvTable data={req} prefer={REQUEST_PREFER} />
              </div>
            )}
            {res && (
              <div>
                <h3 className="detail-subhead">Response</h3>
                <KvTable data={res} prefer={RESPONSE_PREFER} />
              </div>
            )}
          </div>
          <button type="button" className="btn ghost" style={{ marginTop: '0.75rem' }} onClick={() => setShowTech((v) => !v)}>
            {showTech ? 'Hide raw JSON' : 'Show raw JSON'}
          </button>
          {showTech && (
            <div className="detail-raw">
              {item.stk_request_json && (
                <>
                  <div className="muted tiny">Request</div>
                  <pre className="mono tiny">{item.stk_request_json}</pre>
                </>
              )}
              {item.stk_response_json && (
                <>
                  <div className="muted tiny">Response</div>
                  <pre className="mono tiny">{item.stk_response_json}</pre>
                </>
              )}
            </div>
          )}
        </section>
      )}

      <section className="card" style={{ marginTop: '1rem' }}>
        <h2>Ledger</h2>
        {ledger.length === 0 ? (
          <p className="muted">No ledger entries yet. A credit appears when the payment is successful.</p>
        ) : (
          <div className="table-wrap">
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
                    <td>{row.entry_type === 'collection_credit' ? 'Collection credit' : row.entry_type}</td>
                    <td>{formatKes(row.amount_minor, null, row.currency)}</td>
                    <td className="mono tiny">{row.provider_ref || '—'}</td>
                    <td className="muted tiny">{row.created_at ? new Date(row.created_at).toLocaleString() : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <p className="muted tiny" style={{ marginTop: '1rem' }}>
        Payment id <span className="mono">{item.id}</span>
        {(item.status === 'provider_requested' || item.status === 'failed') && (
          <>
            {' '}
            · See <Link to="/docs">Help</Link> and <Link to="/status">System status</Link>
          </>
        )}
      </p>
    </div>
  )
}
