import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type Health as HealthT } from '../api/client'
import { StatusBadge } from '../components/StatusBadge'
import { DataTable } from '../components/DataTable'
import { useLiveStatus } from '../hooks/liveEvents'
import { PageHeader } from '../components/PageHeader'
import { Button } from '../components/primitives'
import { card } from '../components/ui'
import { DismissibleBanner } from '../components/DismissibleBanner'

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
    void Promise.resolve().then(load)
  }, [load])

  const liveEdge =
    lastMessage?.type === 'edge.connection' &&
    typeof lastMessage.payload?.status === 'string'
      ? (lastMessage.payload as EdgeConnection)
      : null
  const displayedEdge = liveEdge || edge

  return (
    <div data-testid="health-page">
      <PageHeader
        title="System status"
        description={
          connected
            ? 'Service health, edge link, and recent network calls. Live updates on.'
            : 'Service health, edge link, and recent network calls. Live channel reconnecting…'
        }
        actions={
          <Button variant="secondary" onClick={() => void load()}>
            Refresh
          </Button>
        }
      />
      {error && (
        <DismissibleBanner tone="error" onDismiss={() => setError(null)}>{error}</DismissibleBanner>
      )}

      {displayedEdge && (
        <div className={card}>
          <h2 className="mb-2 text-base font-bold">Edge connection</h2>
          <p className="mb-4">{displayedEdge.label}</p>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <div>
              <div className="text-[var(--muted)] text-xs">Status</div>
              <StatusBadge
                value={displayedEdge.status === 'connected' ? 'ok' : displayedEdge.status === 'errors' ? 'failed' : displayedEdge.status}
              />
            </div>
            <div>
              <div className="text-[var(--muted)] text-xs">Last message</div>
              <div>{fmt(displayedEdge.last_inbound_at)}</div>
              <div className="text-[var(--muted)] text-xs">
                {displayedEdge.last_inbound_event_type || '—'} · {displayedEdge.last_inbound_status || '—'}
              </div>
            </div>
            <div>
              <div className="text-[var(--muted)] text-xs">Last heartbeat</div>
              <div>{fmt(displayedEdge.last_heartbeat_at)}</div>
              <div className="text-[var(--muted)] text-xs">Failed deliveries (24h): {displayedEdge.dead_events_last_24h ?? 0}</div>
            </div>
          </div>
        </div>
      )}

      <div className={card}>
        <h2 className="mb-2 text-base font-bold">Provider calls</h2>
        <p className="mb-4 text-xs text-[var(--muted)]">
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
                  <StatusBadge value={r.success ? 'ok' : 'failed'} />
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
          <div className={card}>
            <div className="text-[var(--muted)] text-xs">Database</div>
            <div>{data.database ? 'OK' : 'Down'}</div>
          </div>
          <div className={card}>
            <div className="text-[var(--muted)] text-xs">Redis</div>
            <div>{data.redis}</div>
          </div>
          <div className={card}>
            <div className="text-[var(--muted)] text-xs">Admin ready</div>
            <div>{data.admin_ready ? 'Yes' : 'No'}</div>
          </div>
          <div className={card}>
            <div className="text-[var(--muted)] text-xs">Environment</div>
            <div>{data.environment}</div>
          </div>
          <div className={card}>
            <div className="text-[var(--muted)] text-xs">Version</div>
            <div>{data.version}</div>
          </div>
          <div className={card}>
            <div className="text-[var(--muted)] text-xs">Overall</div>
            <StatusBadge value={data.status} />
          </div>
        </div>
      )}
    </div>
  )
}
