import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { emitNotification, subscribeLiveMessages } from '../hooks/liveEvents'
import { api, ApiError, type PaymentIntent } from '../api/client'
import { StatusBadge } from '../components/StatusBadge'
import { formatKes, statusHint } from '../components/statusUtils'
import { PageHeader } from '../components/PageHeader'
import { card, errorAlert, successAlert, table, button, primaryButton, ghostButton } from '../components/ui'

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
    <div className="mb-3 last:mb-0">
      <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-[var(--muted)]">{label}</div>
      <div className="break-words text-sm">{children}</div>
    </div>
  )
}

function KvTable({ data, prefer }: { data: Record<string, unknown>; prefer?: string[] }) {
  const keys = prefer?.filter((k) => data[k] !== undefined && data[k] !== null && data[k] !== '') || []
  const rest = Object.keys(data).filter((k) => !keys.includes(k) && data[k] !== undefined && data[k] !== null && data[k] !== '')
  const ordered = [...keys, ...rest]
  if (ordered.length === 0) return <p className="text-xs text-[var(--muted)]">No fields</p>
  return (
    <dl className="m-0">
      {ordered.map((k) => {
        const v = data[k]
        const display =
          typeof v === 'object' ? JSON.stringify(v) : String(v)
        return (
          <div className="grid grid-cols-[minmax(7rem,38%)_1fr] gap-x-3 gap-y-2 border-b border-[var(--border)] py-2 text-sm last:border-0" key={k}>
            <dt className="m-0 font-medium text-[var(--muted)]">{k}</dt>
            <dd className={`m-0 break-words ${typeof v === 'string' && v.length > 24 ? 'font-mono text-xs' : ''}`}>{display}</dd>
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

  const load = useCallback(async () => {
    if (!id) return null
    try {
      const next = await api.get<PaymentIntent>(`/v1/payment-intents/${id}`)
      setItem((prev) => {
        if (prev && prev.status !== next.status) {
          const terminal = next.status === 'succeeded' || next.status === 'failed' || next.status === 'expired'
          if (terminal) {
            emitNotification({
              id: `local-${next.id}-${next.status}`,
              title:
                next.status === 'succeeded'
                  ? 'Payment successful'
                  : next.status === 'expired'
                    ? 'Payment expired'
                    : 'Payment failed',
              body: `${formatKes(next.amount_minor, next.amount, next.currency)} · ${next.phone || ''}`.trim(),
              level: next.status === 'succeeded' ? 'success' : 'error',
              href: `/intents/${next.id}`,
              status: next.status,
              intent_id: next.id,
              ts: new Date().toISOString(),
            })
          }
        }
        return next
      })
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
      setError(null)
      return next
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Not found')
      return null
    }
  }, [id])

  // Initial load
  useEffect(() => {
    void Promise.resolve().then(load)
  }, [load])

  // Live bus: any payment.update for this intent → reload
  useEffect(() => {
    if (!id) return
    return subscribeLiveMessages((m) => {
      const payload = m.payload || {}
      const intentId = String(payload.intent_id || '')
      if (m.type === 'payment.update' || m.type === 'notification') {
        if (!intentId || intentId === id) void load()
      }
    })
  }, [id, load])

  const status = item?.status
  const checkoutId = item?.provider_checkout_id

  // Poll while waiting for customer / network (STK ResponseCode 0 is not "paid")
  useEffect(() => {
    const waiting = status === 'created' || status === 'provider_requested'
    if (!waiting) return
    const poll = window.setInterval(() => {
      void load()
    }, 4000)
    return () => window.clearInterval(poll)
  }, [status, load])

  // Periodically ask Daraja STK query while still processing (callback may be delayed)
  useEffect(() => {
    if (!checkoutId || !id) return
    const waiting = status === 'created' || status === 'provider_requested'
    if (!waiting) return
    let cancelled = false
    const tick = async () => {
      try {
        await api.post(`/v1/payment-intents/${id}/query-provider`, {})
        if (!cancelled) await load()
      } catch {
        /* keep polling; network may be flaky */
      }
    }
    const first = window.setTimeout(() => void tick(), 8000)
    const every = window.setInterval(() => void tick(), 20000)
    return () => {
      cancelled = true
      window.clearTimeout(first)
      window.clearInterval(every)
    }
  }, [status, checkoutId, id, load])

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

  if (error && !item) return <div className={errorAlert} role="alert" data-testid="intent-detail-page">{error}</div>
  if (!item) return <div data-testid="intent-detail-page">Loading…</div>

  const hint = statusHint(item.status, item.failure_reason)
  const steps = timeline?.steps || []

  return (
    <div data-testid="intent-detail-page" className="space-y-4">
      <p className="mb-2 text-sm text-[var(--muted)]">
        <Link to="/intents">← Payments</Link>
      </p>
      <PageHeader
        title={`${formatKes(item.amount_minor, item.amount, item.currency)} to ${item.phone || '—'}`}
        description={
          [
            item.created_at ? new Date(item.created_at).toLocaleString() : '',
            item.account_reference ? `Ref ${item.account_reference}` : '',
          ]
            .filter(Boolean)
            .join(' · ')
        }
        actions={<StatusBadge value={item.status} />}
      />

      {error && <div className={errorAlert} role="alert">{error}</div>}
      {item.failure_reason && item.status !== 'succeeded' && (
        <div className={errorAlert} role="alert">{item.failure_reason}</div>
      )}
      {msg && <div className={successAlert} role="status">{msg}</div>}
      {hint && !item.failure_reason && (
        <div className="rounded-xl border border-[var(--border)] bg-[var(--panel)] px-4 py-3 text-sm shadow-[var(--shadow-sm)]">
          <p className="m-0 font-medium text-[var(--text)]">{hint}</p>
          {(item.status === 'created' || item.status === 'provider_requested') && (
            <p className="mb-0 mt-2 text-xs text-[var(--muted)]">
              This page updates automatically (live + poll). The STK reply{' '}
              <em>Success. Request accepted for processing</em> only means the phone prompt was accepted — not that
              money moved. Status becomes Paid/Failed after the customer responds, a callback arrives, or you use{' '}
              <strong>Check with network</strong>.
            </p>
          )}
        </div>
      )}

      <div className="grid items-start gap-4 lg:grid-cols-[1.4fr_1fr]">
        <section className={card}>
          <h2 className="mb-3 text-base font-semibold">Timeline</h2>
          {steps.length === 0 ? (
            <p className="text-xs text-[var(--muted)]">No timeline events yet.</p>
          ) : (
            <ol className="m-0 list-none space-y-4 border-l border-[var(--border)] pl-4">
              {steps.map((s, i) => (
                <li key={`${s.at || ''}-${s.kind}-${i}`} className="relative">
                  <span className={`absolute -left-[1.28rem] top-1 size-2.5 rounded-full ring-4 ring-[var(--panel)] ${s.success === false ? 'bg-[var(--danger)]' : 'bg-[var(--accent)]'}`} aria-hidden />
                  <div>
                    <div className="text-sm font-semibold">{s.label}</div>
                    <div className="text-xs text-[var(--muted)]">
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

        <aside className="flex flex-col gap-4">
          <section className={card}>
            <h2 className="mb-3 text-base font-semibold">Summary</h2>
            <Field label="Amount">{formatKes(item.amount_minor, item.amount, item.currency)}</Field>
            <Field label="Phone">
              <span className="font-mono">{item.phone}</span>
            </Field>
            <Field label="Reference">{item.account_reference || '—'}</Field>
            <Field label="Description">{item.description || '—'}</Field>
            {item.status_callback_url && (
              <Field label="Status callback">
                <span className="break-all font-mono text-xs">{item.status_callback_url}</span>
              </Field>
            )}
          </section>

          <section className={card}>
            <h2 className="mb-3 text-base font-semibold">Network</h2>
            <Field label="Checkout ID">
              <span className="break-all font-mono text-xs">{item.provider_checkout_id || '—'}</span>
            </Field>
            <Field label="Receipt / txn">
              <span className="break-all font-mono text-xs">{item.provider_transaction_id || '—'}</span>
            </Field>
            <div className="mt-3 flex flex-wrap gap-2">
              {(item.status === 'created' || item.status === 'provider_requested') && item.provider_checkout_id && (
                <button className={button} type="button" disabled={busy} onClick={queryNetwork}>
                  {busy ? 'Checking…' : 'Check with network'}
                </button>
              )}
              {(item.status === 'created' || item.status === 'provider_requested') && (
                <button className={button} type="button" disabled={busy} onClick={simulate}>
                  {busy ? 'Working…' : 'Simulate success (dev)'}
                </button>
              )}
              {(item.status === 'failed' || item.status === 'expired') && (
                <Link className={primaryButton} to="/intents">
                  Start a new payment
                </Link>
              )}
            </div>
          </section>
        </aside>
      </div>

      {(req || res) && (
        <section className={card}>
          <h2 className="mb-2 text-base font-semibold">Phone prompt exchange</h2>
          <p className="mb-4 text-xs text-[var(--muted)]">
            What we sent to the network and what came back. Secrets are redacted.
          </p>
          <div className="grid gap-5 md:grid-cols-2">
            {req && (
              <div>
                <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--muted)]">Request</h3>
                <KvTable data={req} prefer={REQUEST_PREFER} />
              </div>
            )}
            {res && (
              <div>
                <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--muted)]">Response</h3>
                <KvTable data={res} prefer={RESPONSE_PREFER} />
              </div>
            )}
          </div>
          <button type="button" className={`${ghostButton} mt-3`} onClick={() => setShowTech((v) => !v)}>
            {showTech ? 'Hide raw JSON' : 'Show raw JSON'}
          </button>
          {showTech && (
            <div className="mt-3 rounded-lg border border-[var(--border)] bg-[var(--panel-2)] p-3">
              {item.stk_request_json && (
                <>
                  <div className="text-xs text-[var(--muted)]">Request</div>
                  <pre className="my-2 max-h-52 overflow-auto whitespace-pre-wrap break-words font-mono text-xs">{item.stk_request_json}</pre>
                </>
              )}
              {item.stk_response_json && (
                <>
                  <div className="text-xs text-[var(--muted)]">Response</div>
                  <pre className="my-2 max-h-52 overflow-auto whitespace-pre-wrap break-words font-mono text-xs">{item.stk_response_json}</pre>
                </>
              )}
            </div>
          )}
        </section>
      )}

      <section className={card}>
        <h2 className="mb-3 text-base font-semibold">Ledger</h2>
        {ledger.length === 0 ? (
          <p className="text-sm text-[var(--muted)]">No ledger entries yet. A credit appears when the payment is successful.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className={table}>
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
                    <td className="font-mono text-xs">{row.provider_ref || '—'}</td>
                    <td className="text-xs text-[var(--muted)]">{row.created_at ? new Date(row.created_at).toLocaleString() : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <p className="mt-4 text-xs text-[var(--muted)]">
        Payment id <span className="font-mono">{item.id}</span>
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
