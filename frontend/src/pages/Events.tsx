import { useCallback, useEffect, useState } from 'react'
import { Activity } from 'lucide-react'
import { api, ApiError, type GatewayEvent } from '../api/client'
import { EmptyState } from '../components/EmptyState'
import { PageHeader } from '../components/PageHeader'
import { useLiveStatus } from '../hooks/liveEvents'
import { Button } from '../components/primitives'
import { mono, table, tableWrap } from '../components/ui'

export function Events() {
  const [items, setItems] = useState<GatewayEvent[]>([])
  const [error, setError] = useState<string | null>(null)
  const [msg, setMsg] = useState<string | null>(null)
  const [busyId, setBusyId] = useState<string | null>(null)
  const { connected } = useLiveStatus()

  const load = useCallback(async () => {
    try {
      setItems(await api.get<GatewayEvent[]>('/v1/events'))
      setError(null)
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Could not load activity')
    }
  }, [])

  useEffect(() => {
    void Promise.resolve().then(load)
    const t = window.setInterval(() => void load(), 10000)
    return () => clearInterval(t)
  }, [load])

  async function replay(id: string) {
    setBusyId(id)
    setMsg(null)
    setError(null)
    try {
      await api.post(`/v1/events/${id}/replay`)
      setMsg('Replay requested. Check this list in a moment for a new attempt.')
      await load()
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Could not replay this event')
    } finally {
      setBusyId(null)
    }
  }

  return (
    <div>
      <PageHeader
        title="Activity"
        description="Internal events NetPay processed — useful when something did not update as expected."
        actions={
          <span
            className={`rounded-full px-3 py-1 text-xs font-semibold ${
              connected
                ? 'bg-[var(--accent-soft)] text-[var(--accent-hover)]'
                : 'bg-[var(--panel-2)] text-[var(--muted)]'
            }`}
          >
            {connected ? 'Live updates on' : 'Live updates off'}
          </span>
        }
      />

      {error && (
        <div
          className="mb-4 rounded-xl border border-[var(--danger)]/25 bg-[var(--danger-soft)] px-4 py-3 text-sm text-[var(--danger)]"
          role="alert"
        >
          {error}
          <div className="mt-2">
            <Button variant="secondary" size="sm" onClick={() => void load()}>
              Retry
            </Button>
          </div>
        </div>
      )}
      {msg && (
        <div className="mb-4 rounded-xl border border-[var(--accent)]/25 bg-[var(--accent-soft)] px-4 py-3 text-sm">
          {msg}
        </div>
      )}

      {items.length === 0 ? (
        <EmptyState
          icon={<Activity size={22} />}
          title="No activity yet"
          hint="Events appear here as payments and system messages are processed."
          action={
            <Button variant="secondary" onClick={() => void load()}>
              Refresh
            </Button>
          }
        />
      ) : (
        <div className={tableWrap}>
          <table className={table}>
            <thead>
              <tr>
                <th>When</th>
                <th>What</th>
                <th>Detail</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items.map((ev) => (
                <tr key={ev.id}>
                  <td className="text-xs text-[var(--muted)]">
                    {ev.created_at ? new Date(ev.created_at).toLocaleString() : '—'}
                  </td>
                  <td className="text-sm">
                    <span className="font-medium">{ev.category}</span>
                    <div className={`${mono} text-xs text-[var(--muted)]`}>{ev.action}</div>
                  </td>
                  <td className="max-w-xs text-sm text-[var(--muted)]">{ev.message || '—'}</td>
                  <td>
                    {ev.is_replayable ? (
                      <Button
                        size="sm"
                        variant="secondary"
                        loading={busyId === ev.id}
                        onClick={() => void replay(ev.id)}
                      >
                        Replay
                      </Button>
                    ) : (
                      <span className="text-xs text-[var(--muted)]">—</span>
                    )}
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
