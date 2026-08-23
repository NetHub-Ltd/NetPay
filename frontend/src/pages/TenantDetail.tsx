import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, type Tenant } from '../api/client'
import { StatusBadge } from '../components/StatusBadge'

export function TenantDetail() {
  const { id } = useParams()
  const [tenant, setTenant] = useState<Tenant | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.get<Tenant[]>('/v1/tenants')
      .then((list) => {
        const t = list.find((x) => x.id === id)
        if (!t) setError('Tenant not found')
        else setTenant(t)
      })
      .catch((e) => setError(e.message))
  }, [id])

  if (error) return <div className="alert error" data-testid="tenant-detail-page">{error}</div>
  if (!tenant) return <div data-testid="tenant-detail-page">Loading…</div>

  return (
    <div data-testid="tenant-detail-page">
      <div className="page-header">
        <div>
          <h1>{tenant.name}</h1>
          <p className="mono">{tenant.slug} · {tenant.id}</p>
        </div>
        <StatusBadge value={tenant.status} />
      </div>
      <div className="card">
        <h2>Quick links</h2>
        <div className="btn-row">
          <Link className="btn" to={`/integrations?tenant_id=${tenant.id}`}>Integrations</Link>
          <Link className="btn" to={`/webhooks?tenant_id=${tenant.id}`}>Webhooks</Link>
          <Link className="btn" to={`/intents?tenant_id=${tenant.id}`}>Payment intents</Link>
          <Link className="btn" to={`/oauth-clients?tenant_id=${tenant.id}`}>OAuth clients</Link>
        </div>
      </div>
    </div>
  )
}
