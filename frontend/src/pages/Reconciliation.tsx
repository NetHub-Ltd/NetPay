import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { AlertTriangle } from 'lucide-react'
import { api, ApiError } from '../api/client'
import { useAuth } from '../auth/authState'
import { EmptyState } from '../components/EmptyState'
import { PageHeader } from '../components/PageHeader'
import { StatusBadge } from '../components/StatusBadge'
import { Button } from '../components/primitives'
import { table, tableWrap } from '../components/ui'
import { DismissibleBanner } from '../components/DismissibleBanner'

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

  const load = useCallback(async () => {
    try {
      setItems(await api.get<ReconRow[]>('/v1/reconciliation/exceptions'))
      setError(null)
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Could not load items that need attention')
    }
  }, [])

  useEffect(() => {
    void Promise.resolve().then(load)
  }, [load])

  async function scan() {
    setBusy(true)
    setError(null)
    setMsg(null)
    try {
      const res = await api.post<{ exceptions_created: number; notes: string[] }>(
        '/v1/reconciliation/scan',
        {},
      )
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
      setError(e instanceof ApiError ? e.detail : 'Could not resolve')
    } finally {
      setBusy(false)
    }
  }

  const open = items.filter((r) => r.status !== 'resolved')

  return (
    <div data-testid="recon-page">
      <PageHeader
        title="Needs attention"
        description="Payments and matches that need a human look before you treat them as closed."
        actions={
          isAdmin ? (
            <Button loading={busy} onClick={() => void scan()}>
              {busy ? 'Scanning…' : 'Run scan'}
            </Button>
          ) : undefined
        }
      />

      {error && (
        <DismissibleBanner tone="error" onDismiss={() => setError(null)}>
          {error}
        </DismissibleBanner>
      )}
      {msg && (
        <div className="mb-4 rounded-xl border border-[var(--accent)]/25 bg-[var(--accent-soft)] px-4 py-3 text-sm">
          {msg}
        </div>
      )}

      {open.length === 0 ? (
        <EmptyState
          icon={<AlertTriangle size={22} />}
          title="Nothing needs attention"
          hint="When amounts or references don’t match, or a payment is stuck, it will show up here."
          action={
            isAdmin ? (
              <Button variant="secondary" loading={busy} onClick={() => void scan()}>
                Run scan
              </Button>
            ) : undefined
          }
        />
      ) : (
        <div className={tableWrap}>
          <table className={table}>
            <thead>
              <tr>
                <th>Issue</th>
                <th>Status</th>
                <th>Message</th>
                <th>Payment</th>
                <th>When</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {open.map((row) => (
                <tr key={row.id}>
                  <td className="text-sm font-medium">
                    {KIND_LABEL[row.kind] || row.kind}
                  </td>
                  <td>
                    <StatusBadge value={row.status} />
                  </td>
                  <td className="max-w-xs text-sm text-[var(--muted)]">{row.message}</td>
                  <td>
                    {row.payment_intent_id ? (
                      <Link to={`/intents/${row.payment_intent_id}`}>Open payment</Link>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td className="text-xs text-[var(--muted)]">
                    {row.created_at ? new Date(row.created_at).toLocaleString() : '—'}
                  </td>
                  <td>
                    <Button
                      size="sm"
                      variant="secondary"
                      disabled={busy}
                      onClick={() => void resolve(row.id)}
                    >
                      Mark resolved
                    </Button>
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
