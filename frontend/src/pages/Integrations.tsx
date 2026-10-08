import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Landmark, Plus } from 'lucide-react'
import { useWorkspace } from '../workspace/useWorkspace'
import { api, ApiError, type Integration } from '../api/client'
import { EmptyState } from '../components/EmptyState'
import { PageHeader } from '../components/PageHeader'
import { StatusBadge } from '../components/StatusBadge'
import { Button } from '../components/primitives'
import { mono, table, tableWrap } from '../components/ui'
import { DismissibleBanner } from '../components/DismissibleBanner'
import { TableSkeleton } from '../components/Skeleton'

export function Integrations() {
  const navigate = useNavigate()
  const { activeTenantId, activeBusiness } = useWorkspace()
  const [items, setItems] = useState<Integration[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const biz = activeBusiness?.name || 'this business'

  const load = useCallback(async () => {
    if (!activeTenantId) {
      setItems([])
      setLoading(false)
      return
    }
    setLoading(true)
    try {
      const list = await api.get<Integration[]>(`/v1/integrations?tenant_id=${activeTenantId}`)
      setItems(list)
      setError(null)
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Could not load shortcodes')
      setItems([])
    } finally {
      setLoading(false)
    }
  }, [activeTenantId])

  useEffect(() => {
    void Promise.resolve().then(load)
  }, [load])

  return (
    <div data-testid="integrations-page">
      <PageHeader
        title="Shortcodes"
        description={`Paybills and tills for ${biz}.`}
        actions={
          <Button leftIcon={<Plus size={16} />} onClick={() => navigate('/integrations/new')}>
            Add shortcode
          </Button>
        }
      />

      {error && (
        <DismissibleBanner tone="error" onDismiss={() => setError(null)}>
          {error}
          <div className="mt-2">
            <Button variant="secondary" size="sm" onClick={() => void load()}>
              Retry
            </Button>
          </div>
        </DismissibleBanner>
      )}
      {loading ? (
        <TableSkeleton rows={4} />
      ) : items.length === 0 ? (
        <EmptyState
          icon={<Landmark size={22} />}
          title="No shortcodes yet"
          hint={`Add a paybill or till for ${biz}. Credentials are verified before save.`}
          action={
            <Button leftIcon={<Plus size={16} />} onClick={() => navigate('/integrations/new')}>
              Add shortcode
            </Button>
          }
        />
      ) : (
        <div className={tableWrap}>
          <table className={table}>
            <thead>
              <tr>
                <th>Shortcode</th>
                <th>Type</th>
                <th>Environment</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items.map((i) => (
                <tr key={i.id}>
                  <td>
                    <strong>{i.shortcode}</strong>
                    <div className={`${mono} text-xs text-[var(--muted)]`}>{i.public_id}</div>
                  </td>
                  <td>{i.type === 'till' ? 'Till' : 'Paybill'}</td>
                  <td>{i.environment === 'production' ? 'Live' : 'Test'}</td>
                  <td>
                    <StatusBadge value={i.connected ? 'connected' : i.status} />
                  </td>
                  <td>
                    <Link to={`/integrations/${i.id}`}>Open</Link>
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
