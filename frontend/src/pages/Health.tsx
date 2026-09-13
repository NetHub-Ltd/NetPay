import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type Health as HealthT } from '../api/client'
import { StatusBadge } from '../components/StatusBadge'
import { useLiveStatus } from '../hooks/useWebSocket'

type EdgeConnection = {
  status: string
  label: string
  last_inbound_at?: string | null
  last_inbound_event_type?: string | null
  last_inbound_status?: string | null
  last_heartbeat_at?: string | null
  dead_events_last_24h?: number
}

function fmt(iso?: string | null) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

export function Health() {
  const [data, setData] = useState<HealthT | null>(null)
  const [edge, setEdge] = useState<EdgeConnection | null>(null)
  const [error, setError] = useState<string | null>(null)
  const { connected, lastMessage } = useLiveStatus()

  const load = useCallback(async () => {
    try {
      setData(await api.get<HealthT>('/health'))
      try {
        setEdge(await api.get<EdgeConnection>('/v1/system/edge-connection'))
      } catch {
        setEdge(null)
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Could not load status')
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  // Live updates from NetPay hub only (edge never polled from the browser)
  useEffect(() => {
    if (!lastMessage || lastMessage.type !== 'edge.connection') return
    const p = lastMessage.payload as EdgeConnection | undefined
    if (p && typeof p.status === 'string') {
      setEdge(p)
    }
  }, [lastMessage])

  return (
    <div data-testid="health-page">
      <div className="page-header">
        <div>
          <h1>System status</h1>
          <p>
            Service health and the link from M-Pesa edge into NetPay.
            {connected ? ' Live updates on.' : ' Live channel reconnecting…'}
          </p>
        </div>
        <button type="button" className="btn" onClick={load}>
          Refresh
        </button>
      </div>
      {error && <div className="alert error">{error}</div>}

      {edge && (
        <div className="card" style={{ marginBottom: '1rem' }}>
          <h2>M-Pesa edge connection</h2>
          <p style={{ marginTop: 0 }}>{edge.label}</p>
          <div className="grid-3">
            <div>
              <div className="muted tiny">Status</div>
              <StatusBadge
                value={edge.status === 'connected' ? 'ok' : edge.status === 'errors' ? 'failed' : edge.status}
              />
            </div>
            <div>
              <div className="muted tiny">Last message</div>
              <div>{fmt(edge.last_inbound_at)}</div>
              <div className="muted tiny">
                {edge.last_inbound_event_type || '—'} · {edge.last_inbound_status || '—'}
              </div>
            </div>
            <div>
              <div className="muted tiny">Last heartbeat</div>
              <div>{fmt(edge.last_heartbeat_at)}</div>
              <div className="muted tiny">Failed deliveries (24h): {edge.dead_events_last_24h ?? 0}</div>
            </div>
          </div>
          <p className="muted tiny" style={{ marginBottom: 0 }}>
            Updates stream from NetPay when the edge delivers events (including heartbeats). This page does not call
            the edge worker. See <Link to="/docs">Help</Link>.
          </p>
        </div>
      )}

      {data && (
        <div className="grid-3">
          <div className="card">
            <div className="muted tiny">Database</div>
            <div>{data.database ? 'OK' : 'Down'}</div>
          </div>
          <div className="card">
            <div className="muted tiny">Redis</div>
            <div>{data.redis}</div>
          </div>
          <div className="card">
            <div className="muted tiny">Admin ready</div>
            <div>{data.admin_ready ? 'Yes' : 'No'}</div>
          </div>
          <div className="card">
            <div className="muted tiny">Environment</div>
            <div>{data.environment}</div>
          </div>
          <div className="card">
            <div className="muted tiny">Version</div>
            <div>{data.version}</div>
          </div>
          <div className="card">
            <div className="muted tiny">Overall</div>
            <StatusBadge value={data.status} />
          </div>
        </div>
      )}
    </div>
  )
}
