import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type Health as HealthT } from '../api/client'
import { StatusBadge } from '../components/StatusBadge'
import { DataTable } from '../components/DataTable'
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

type OutboundRow = {
  id: string
  created_at?: string | null
  operation: string
  label?: string
  response_status?: number | null
  success: boolean
  error_message?: string | null
  duration_ms?: number | null
  payment_intent_id?: string | null
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
  const [outbound, setOutbound] = useState<OutboundRow[]>([])
  const [border-[var(--danger)]/30 bg-[var(--danger)]/10 text-[var(--danger)], setError] = useState<string | null>(null)
  const { connected, lastMessage } = useLiveStatus()

  const load = useCallback(async () => {
    try {
      setData(await api.get<HealthT>('/health'))
      try {
        setEdge(await api.get<EdgeConnection>('/v1/system/edge-connection'))
      } catch {
        setEdge(null)
      }
      try {
        setOutbound(await api.get<OutboundRow[]>('/v1/system/outbound-requests?limit=25'))
      } catch {
        setOutbound([])
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Could not load status')
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  useEffect(() => {
    if (!lastMessage || lastMessage.type !== 'edge.connection') return
    const p = lastMessage.payload as EdgeConnection | undefined
    if (p && typeof p.status === 'string') setEdge(p)
  }, [lastMessage])

  return (
    <div data-testid="health-page">
      <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1>System status</h1>
          <p>
            Service health, edge link, and recent calls to the payment network.
            {connected ? ' Live updates on.' : ' Live channel reconnecting…'}
          </p>
        </div>
        <button type="button" className="inline-flex items-center justify-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--panel)] px-3 py-2 text-sm font-medium text-[var(--text)] no-underline shadow-[var(--shadow-sm)] hover:bg-[var(--panel-2)] hover:no-underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--accent)] disabled:cursor-not-allowed disabled:opacity-50" onClick={load}>
          Refresh
        </button>
      </div>
      {border-[var(--danger)]/30 bg-[var(--danger)]/10 text-[var(--danger)] && <div className="mb-4 rounded-lg border px-4 py-3 text-sm border-[var(--danger)]/30 bg-[var(--danger)]/10 text-[var(--danger)]">{border-[var(--danger)]/30 bg-[var(--danger)]/10 text-[var(--danger)]}</div>}

      {edge && (
        <div className="mb-4 rounded-[var(--radius)] border border-[var(--border)] bg-[var(--panel)] p-4 shadow-[var(--shadow)]" style={{ marginBottom: '1rem' }}>
          <h2>Edge connection</h2>
          <p style={{ marginTop: 0 }}>{edge.label}</p>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <div>
              <div className="text-[var(--muted)] text-xs">Status</div>
              <StatusBadge
                value={edge.status === 'connected' ? 'border-[var(--accent-2)]/30 bg-[var(--accent-2)]/10 text-[var(--text)]' : edge.status === 'errors' ? 'failed' : edge.status}
              />
            </div>
            <div>
              <div className="text-[var(--muted)] text-xs">Last message</div>
              <div>{fmt(edge.last_inbound_at)}</div>
              <div className="text-[var(--muted)] text-xs">
                {edge.last_inbound_event_type || '—'} · {edge.last_inbound_status || '—'}
              </div>
            </div>
            <div>
              <div className="text-[var(--muted)] text-xs">Last heartbeat</div>
              <div>{fmt(edge.last_heartbeat_at)}</div>
              <div className="text-[var(--muted)] text-xs">Failed deliveries (24h): {edge.dead_events_last_24h ?? 0}</div>
            </div>
          </div>
        </div>
      )}

      <div className="mb-4 rounded-[var(--radius)] border border-[var(--border)] bg-[var(--panel)] p-4 shadow-[var(--shadow)]" style={{ marginBottom: '1rem' }}>
        <h2>Provider calls</h2>
        <p className="text-[var(--muted)] text-xs" style={{ marginTop: 0 }}>
          Recent requests NetPay made to the payment network (login, phone prompts, connect shortcode).
        </p>
        <DataTable
          rows={outbound}
          getRowId={(r) => r.id}
          searchPlaceholder="Search operations…"
          defaultPageSize={10}
          maxHeight="min(360px, 45vh)"
          emptyTitle="No provider calls yet"
          emptyHint="Phone prompts and network login appear here after you use them."
          columns={[
            {
              id: 'when',
              header: 'When',
              searchValue: (r) => r.created_at || '',
              cell: (r) => <span className="text-[var(--muted)] text-xs">{fmt(r.created_at)}</span>,
            },
            {
              id: 'what',
              header: 'What',
              searchValue: (r) => r.label || r.operation,
              cell: (r) => r.label || r.operation,
            },
            {
              id: 'result',
              header: 'Result',
              cell: (r) => (
                <>
                  <StatusBadge value={r.success ? 'border-[var(--accent-2)]/30 bg-[var(--accent-2)]/10 text-[var(--text)]' : 'failed'} />
                  {r.response_status != null && (
                    <span className="text-[var(--muted)] text-xs"> · HTTP {r.response_status}</span>
                  )}
                </>
              ),
            },
            {
              id: 'detail',
              header: 'Detail',
              searchValue: (r) => r.error_message || '',
              cell: (r) => (
                <span className="text-[var(--muted)] text-xs">{(r.error_message || '—').slice(0, 120)}</span>
              ),
            },
            {
              id: 'link',
              header: '',
              cell: (r) =>
                r.payment_intent_id ? (
                  <Link to={`/intents/${r.payment_intent_id}`}>Payment</Link>
                ) : (
                  '—'
                ),
            },
          ]}
        />
      </div>

      {data && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <div className="mb-4 rounded-[var(--radius)] border border-[var(--border)] bg-[var(--panel)] p-4 shadow-[var(--shadow)]">
            <div className="text-[var(--muted)] text-xs">Database</div>
            <div>{data.database ? 'OK' : 'Down'}</div>
          </div>
          <div className="mb-4 rounded-[var(--radius)] border border-[var(--border)] bg-[var(--panel)] p-4 shadow-[var(--shadow)]">
            <div className="text-[var(--muted)] text-xs">Redis</div>
            <div>{data.redis}</div>
          </div>
          <div className="mb-4 rounded-[var(--radius)] border border-[var(--border)] bg-[var(--panel)] p-4 shadow-[var(--shadow)]">
            <div className="text-[var(--muted)] text-xs">Admin ready</div>
            <div>{data.admin_ready ? 'Yes' : 'No'}</div>
          </div>
          <div className="mb-4 rounded-[var(--radius)] border border-[var(--border)] bg-[var(--panel)] p-4 shadow-[var(--shadow)]">
            <div className="text-[var(--muted)] text-xs">Environment</div>
            <div>{data.environment}</div>
          </div>
          <div className="mb-4 rounded-[var(--radius)] border border-[var(--border)] bg-[var(--panel)] p-4 shadow-[var(--shadow)]">
            <div className="text-[var(--muted)] text-xs">Version</div>
            <div>{data.version}</div>
          </div>
          <div className="mb-4 rounded-[var(--radius)] border border-[var(--border)] bg-[var(--panel)] p-4 shadow-[var(--shadow)]">
            <div className="text-[var(--muted)] text-xs">Overall</div>
            <StatusBadge value={data.status} />
          </div>
        </div>
      )}
    </div>
  )
}
