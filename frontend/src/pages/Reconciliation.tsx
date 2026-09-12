import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, ApiError } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { EmptyState } from '../components/EmptyState'
import { StatusBadge } from '../components/StatusBadge'

type ReconRow = {
  id: string
  kind: string
  status: string
  message: string
  provider_ref?: string | null
  payment_intent_id?: string | null
  resolved_note?: string | null
  created_at?: string
}

const KIND_LABEL: Record<string, string> = {
  unmatched_netpay: 'Paid without ledger line',
  stale_pending: 'Stuck waiting on M-Pesa',
  unmatched_provider: 'Provider has payment we don’t',
  amount_mismatch: 'Amount mismatch',
}

export function Reconciliation() {
  const { isAdmin } = useAuth()
  const [items, setItems] = useState<ReconRow[]>([])
  const [error, setError] = useState<string | null>(null)
  const [msg, setMsg] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function load() {
    try {
      setItems(await api.get<ReconRow[]>('/v1/reconciliation/exceptions'))
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Could not load exceptions')
    }
  }

  useEffect(() => {
    load()
  }, [])

  async function scan() {
    setBusy(true)
    setError(null)
    setMsg(null)
    try {
      const res = await api.post<{ exceptions_created: number; notes: string[] }>('/v1/reconciliation/scan', {})
      setMsg(
        `Scan finished. New items: ${res.exceptions_created}.` +
          (res.notes?.length ? ` Notes: ${res.notes.join('; ')}` : ''),
      )
      await load()
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Scan failed')
    } finally {
      setBusy(false)
    }
  }

  async function resolve(id: string) {
    setBusy(true)
    setError(null)
    try {
      await api.post(`/v1/reconciliation/exceptions/${id}/resolve`, {
        resolved_note: 'Reviewed and closed in UI',
      })
      await load()
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Resolve failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div data-testid="recon-page">
      <div className="page-header">
        <div>
          <h1>Needs attention</h1>
          <p>Open items where money status and records may not line up. Resolve after you investigate.</p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <Link className="btn" to="/docs">
            How-to guides
          </Link>
          {isAdmin && (
            <button className="btn primary" type="button" disabled={busy} onClick={scan}>
              {busy ? 'Scanning…' : 'Run scan'}
            </button>
          )}
        </div>
      </div>

      {error && <div className="alert error">{error}</div>}
      {msg && <div className="alert ok">{msg}</div>}

      {items.length === 0 ? (
        <EmptyState
          title="All clear"
          hint="No open exceptions. Admins can run a scan after busy periods to double-check."
        />
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Issue</th>
                <th>Message</th>
                <th>Payment</th>
                <th>When</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items.map((row) => (
                <tr key={row.id}>
                  <td>
                    <StatusBadge value={row.status} />
                    <div className="muted" style={{ fontSize: '0.85rem' }}>
                      {KIND_LABEL[row.kind] || row.kind}
                    </div>
                  </td>
                  <td>{row.message}</td>
                  <td>
                    {row.payment_intent_id ? (
                      <Link to={`/intents/${row.payment_intent_id}`}>Open payment</Link>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td className="muted">{row.created_at ? new Date(row.created_at).toLocaleString() : '—'}</td>
                  <td>
                    <button className="btn" type="button" disabled={busy} onClick={() => resolve(row.id)}>
                      Resolve
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
