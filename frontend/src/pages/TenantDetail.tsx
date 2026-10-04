import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, type Tenant } from '../api/client'
import { StatusBadge } from '../components/StatusBadge'
import { button, card, errorAlert, mono, pageDescription, pageHeader, pageTitle } from '../components/ui'

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

  if (error) return <div className={errorAlert} role="alert" data-testid="tenant-detail-page">{error}</div>
  if (!tenant) return <div data-testid="tenant-detail-page">Loading…</div>

  return (
    <div data-testid="tenant-detail-page">
      <div className={pageHeader}>
        <div>
          <h1 className={pageTitle}>{tenant.name}</h1>
          <p className={`${pageDescription} ${mono}`}>{tenant.slug} · {tenant.id}</p>
        </div>
        <StatusBadge value={tenant.status} />
      </div>
      <div className={card}>
        <h2 className="mb-3 text-base font-semibold">Quick links</h2>
        <div className="flex flex-wrap gap-2">
          <Link className={button} to={`/integrations?tenant_id=${tenant.id}`}>Integrations</Link>
          <Link className={button} to={`/webhooks?tenant_id=${tenant.id}`}>Webhooks</Link>
          <Link className={button} to={`/intents?tenant_id=${tenant.id}`}>Payment intents</Link>
          <Link className={button} to={`/oauth-clients?tenant_id=${tenant.id}`}>OAuth clients</Link>
        </div>
      </div>
    </div>
  )
}
