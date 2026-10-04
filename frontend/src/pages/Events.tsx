import { useCallback, useEffect, useState } from 'react'
import { api, ApiError, type GatewayEvent } from '../api/client'
import { EmptyState } from '../components/EmptyState'
import { useLiveStatus } from '../hooks/liveEvents'
import { errorAlert, pageDescription, pageHeader, pageTitle, successAlert, table, tableWrap, button } from '../components/ui'

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
      <div className={pageHeader}>
        <div>
          <h1 className={pageTitle}>Event log</h1>
          <p className={pageDescription}>Replayable gateway events · {connected ? 'live polling on' : 'offline'}</p>
        </div>
        <button className={button} type="button" onClick={() => void load()}>
          Refresh
        </button>
      </div>
      {error && <div className={errorAlert} role="alert">{error}</div>}
      {msg && <div className={successAlert} role="status">{msg}</div>}

      {items.length === 0 ? (
        <EmptyState title="No events yet" hint="Onboarding, STK, and callbacks appear here." />
      ) : (
        <div className={tableWrap}>
          <table className={table}>
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
                      <button type="button" className={button} onClick={() => void replay(ev.id)}>
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
