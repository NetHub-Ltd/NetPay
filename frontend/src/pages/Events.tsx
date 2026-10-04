import { useCallback, useEffect, useState } from 'react'
import { api, ApiError, type GatewayEvent } from '../api/client'
import { EmptyState } from '../components/EmptyState'
import { useLiveStatus } from '../hooks/liveEvents'

export function Events() {
  const [items, setItems] = useState<GatewayEvent[]>([])
  const [error, setError] = useState<string | null>(null)
  const [msg, setMsg] = useState<string | null>(null)
  const { connected } = useLiveStatus()

  const load = useCallback(async () => {
    try {
      setItems(await api.get<GatewayEvent[]>('/v1/events'))
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Failed to load events')
    }
  }, [])

  useEffect(() => {
    void Promise.resolve().then(load)
    const t = window.setInterval(() => void load(), 10000)
    return () => clearInterval(t)
  }, [load])

  async function replay(id: string) {
    setMsg(null)
    setError(null)
    try {
      await api.post(`/v1/events/${id}/replay`)
      setMsg(`Replay requested for ${id.slice(0, 8)}…`)
      await load()
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Replay failed')
    }
  }

  return (
    <div data-testid="events-page">
      <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1>Event log</h1>
          <p>Replayable gateway events · {connected ? 'live polling on' : 'offline'}</p>
        </div>
        <button className="inline-flex items-center justify-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--panel)] px-3 py-2 text-sm font-medium text-[var(--text)] no-underline shadow-[var(--shadow)]" type="button" onClick={() => load()}>
          Refresh
        </button>
      </div>
      {error && <div className="mb-4 rounded-lg border px-4 py-3 text-sm border-[var(--danger)]/30 bg-[var(--danger)]/10 text-[var(--danger)]">{error}</div>}
      {msg && <div className="mb-4 rounded-lg border px-4 py-3 text-sm border-[var(--accent-2)]/30 bg-[var(--accent-2)]/10 text-[var(--text)]">{msg}</div>}

      {items.length === 0 ? (
        <EmptyState title="No events yet" hint="Onboarding, STK, and callbacks appear here." />
      ) : (
        <div className="mb-4 rounded-[var(--radius)] border border-[var(--border)] bg-[var(--panel)] p-4 shadow-[var(--shadow)]">
          <table>
            <thead>
              <tr><th>When</th><th>Category</th><th>Action</th><th>Message</th><th></th></tr>
            </thead>
            <tbody>
              {items.map((ev) => (
                <tr key={ev.id}>
                  <td className="text-[var(--muted)] text-xs">{new Date(ev.created_at).toLocaleString()}</td>
                  <td>{ev.category}</td>
                  <td className="font-mono text-[0.85em]">{ev.action}</td>
                  <td>{ev.message}</td>
                  <td>
                    {ev.is_replayable ? (
                      <button type="button" className="inline-flex items-center justify-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--panel)] px-3 py-2 text-sm font-medium text-[var(--text)] no-underline shadow-[var(--shadow)]" onClick={() => replay(ev.id)}>
                        Replay
                      </button>
                    ) : (
                      <span className="text-[var(--muted)] text-xs">—</span>
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
