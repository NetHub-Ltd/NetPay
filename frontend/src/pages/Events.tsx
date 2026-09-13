import { useEffect, useState } from 'react'
import { api, ApiError, type GatewayEvent } from '../api/client'
import { EmptyState } from '../components/EmptyState'
import { useLiveStatus } from '../hooks/useWebSocket'

export function Events() {
  const [items, setItems] = useState<GatewayEvent[]>([])
  const [error, setError] = useState<string | null>(null)
  const [msg, setMsg] = useState<string | null>(null)
  const { connected } = useLiveStatus()

  async function load() {
    try {
      setItems(await api.get<GatewayEvent[]>('/v1/events'))
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Failed to load events')
    }
  }

  useEffect(() => {
    load()
    const t = window.setInterval(load, 10000)
    return () => clearInterval(t)
  }, [])

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
      <div className="page-header">
        <div>
          <h1>Event log</h1>
          <p>Replayable gateway events · {connected ? 'live polling on' : 'offline'}</p>
        </div>
        <button className="btn" type="button" onClick={load}>Refresh</button>
      </div>
      {error && <div className="alert error">{error}</div>}
      {msg && <div className="alert ok">{msg}</div>}

      {items.length === 0 ? (
        <EmptyState title="No events yet" hint="Onboarding, STK, and callbacks appear here." />
      ) : (
        <div className="card">
          <table>
            <thead>
              <tr><th>When</th><th>Category</th><th>Action</th><th>Message</th><th></th></tr>
            </thead>
            <tbody>
              {items.map((ev) => (
                <tr key={ev.id}>
                  <td className="muted tiny">{new Date(ev.created_at).toLocaleString()}</td>
                  <td>{ev.category}</td>
                  <td className="mono">{ev.action}</td>
                  <td>{ev.message}</td>
                  <td>
                    {ev.is_replayable ? (
                      <button type="button" className="btn ghost" onClick={() => replay(ev.id)}>Replay</button>
                    ) : (
                      <span className="muted tiny">—</span>
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
