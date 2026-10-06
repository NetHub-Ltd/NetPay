import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useWorkspace } from '../workspace/useWorkspace'
import { Landmark, Plus } from 'lucide-react'
import { api, ApiError, type Integration, type Tenant } from '../api/client'
import { EmptyState } from '../components/EmptyState'
import { PageHeader } from '../components/PageHeader'
import { StatusBadge } from '../components/StatusBadge'
import { Button } from '../components/primitives'
import { mono, table, tableWrap } from '../components/ui'

const selectClass =
  'w-full rounded-xl border border-[var(--border)] bg-[var(--panel)] px-3.5 py-2.5 text-sm shadow-[var(--shadow-sm)] focus:border-[var(--accent)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/25'

export function Integrations() {
  const navigate = useNavigate()
  const { activeTenantId } = useWorkspace()
  const [params, setParams] = useSearchParams()
  const [businesses, setBusinesses] = useState<Tenant[]>([])
  const [items, setItems] = useState<Integration[]>([])
  const [error, setError] = useState<string | null>(null)
  const [msg, setMsg] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const selectedTenant = params.get('tenant_id') || activeTenantId || ''

  const activeBusinesses = useMemo(
    () => businesses.filter((b) => b.status === 'active'),
    [businesses],
  )

  const load = useCallback(async () => {
    try {
      const tenants = await api.get<Tenant[]>('/v1/tenants')
      setBusinesses(tenants)
      const tid = params.get('tenant_id')
      const path = tid ? `/v1/integrations?tenant_id=${tid}` : '/v1/integrations'
      setItems(await api.get<Integration[]>(path))
      setError(null)
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Could not load shortcodes')
    }
  }, [params])

  useEffect(() => {
    void Promise.resolve().then(load)
  }, [load])

  function setTenantFilter(tenantId: string) {
    const next = new URLSearchParams(params)
    if (tenantId) next.set('tenant_id', tenantId)
    else next.delete('tenant_id')
    setParams(next)
  }

  async function onRetire(id: string, shortcode: string) {
    if (!window.confirm(`Retire shortcode ${shortcode}?`)) return
    setBusy(true)
    try {
      await api.delete(`/v1/integrations/${id}`)
      setMsg(`Shortcode ${shortcode} retired.`)
      await load()
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Could not retire shortcode')
    } finally {
      setBusy(false)
    }
  }

  const businessName = (tid: string) => businesses.find((b) => b.id === tid)?.name || tid.slice(0, 8)

  return (
    <div>
      <PageHeader
        title="Shortcodes"
        description="Manage paybills and tills across your businesses. Create from here or inside a business."
        actions={
          <Button
            leftIcon={<Plus size={16} />}
            disabled={activeBusinesses.length === 0}
            title={activeBusinesses.length === 0 ? 'Create an active business first' : undefined}
            onClick={() => {
              navigate(`/integrations/new?tenant_id=${selectedTenant || activeTenantId || ''}`)
            }}
          >
            Add shortcode
          </Button>
        }
      />

      <div className="mb-4 flex max-w-sm flex-col gap-1.5 text-sm">
        <span className="font-medium">Business</span>
        <select
          className={selectClass}
          value={selectedTenant}
          onChange={(e) => setTenantFilter(e.target.value)}
        >
          <option value="">All businesses</option>
          {businesses.map((b) => (
            <option key={b.id} value={b.id}>
              {b.name}
              {b.status !== 'active' ? ' (inactive)' : ''}
            </option>
          ))}
        </select>
      </div>

      {error && (
        <div className="mb-4 rounded-xl border border-[var(--danger)]/25 bg-[var(--danger-soft)] px-4 py-3 text-sm text-[var(--danger)]" role="alert">
          {error}
        </div>
      )}
      {msg && (
        <div className="mb-4 rounded-xl border border-[var(--accent)]/25 bg-[var(--accent-soft)] px-4 py-3 text-sm">
          {msg}
        </div>
      )}

      {businesses.length === 0 ? (
        <EmptyState
          icon={<Landmark size={22} />}
          title="Create a business first"
          hint="Shortcodes belong to a business. Add one, then come back to attach paybills or tills."
          action={
            <Link to="/tenants" className="no-underline">
              <Button>Go to businesses</Button>
            </Link>
          }
        />
      ) : items.length === 0 ? (
        <EmptyState
          icon={<Landmark size={22} />}
          title="No shortcodes yet"
          hint="Add a shortcode and pin it to a business. Credentials are verified before save."
          action={
            activeBusinesses.length > 0 ? (
              <Button
                leftIcon={<Plus size={16} />}
                onClick={() => {
                  navigate(`/integrations/new?tenant_id=${selectedTenant || activeTenantId || ''}`)
                }}
              >
                Add shortcode
              </Button>
            ) : (
              <Link to="/tenants" className="no-underline">
                <Button>Activate a business</Button>
              </Link>
            )
          }
        />
      ) : (
        <div className={tableWrap}>
          <table className={table}>
            <thead>
              <tr>
                <th>Shortcode</th>
                <th>Business</th>
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
                  <td>
                    <Link to={`/tenants/${i.tenant_id}`}>{businessName(i.tenant_id)}</Link>
                  </td>
                  <td>{i.type === 'till' ? 'Till' : 'Paybill'}</td>
                  <td>{i.environment === 'production' ? 'Live' : 'Test'}</td>
                  <td>
                    <StatusBadge value={i.connected ? 'connected' : i.status} />
                  </td>
                  <td>
                    <div className="flex flex-wrap justify-end gap-2">
                      <Link to={`/integrations/${i.id}`} className="no-underline">
                        <Button size="sm">Manage</Button>
                      </Link>
                      <Button size="sm" variant="secondary" disabled={busy} onClick={() => void onRetire(i.id, i.shortcode)}>
                        Retire
                      </Button>
                    </div>
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
