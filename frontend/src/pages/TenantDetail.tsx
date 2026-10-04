import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, ApiError, type Tenant } from '../api/client'
import { PageHeader } from '../components/PageHeader'
import { PageLoader, Button } from '../components/primitives'
import { StatusBadge } from '../components/StatusBadge'
import { mono } from '../components/ui'

export function TenantDetail() {
  const { id } = useParams()
  const [tenant, setTenant] = useState<Tenant | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    let cancelled = false
    void api
      .get<Tenant>(`/v1/tenants/${id}`)
      .then((t) => {
        if (!cancelled) {
          setTenant(t)
          setError(null)
        }
      })
      .catch((e) => {
        if (!cancelled) {
          setError(e instanceof ApiError ? e.detail : e.message || 'Could not load business')
        }
      })
    return () => {
      cancelled = true
    }
  }, [id])

  if (!id) {
    return (
      <div
        className="rounded-xl border border-[var(--danger)]/25 bg-[var(--danger-soft)] px-4 py-3 text-sm text-[var(--danger)]"
        role="alert"
      >
        Business not found
      </div>
    )
  }

  if (error) {
    return (
      <div
        className="rounded-xl border border-[var(--danger)]/25 bg-[var(--danger-soft)] px-4 py-3 text-sm text-[var(--danger)]"
        role="alert"
      >
        {error}
      </div>
    )
  }
  if (!tenant) return <PageLoader label="Loading business…" />

  return (
    <div data-testid="tenant-detail-page">
      <PageHeader
        title={tenant.name}
        description={`${tenant.slug || ''} · ${tenant.id}`.trim()}
        actions={<StatusBadge value={tenant.status} />}
      />
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--panel)] p-5 shadow-[var(--shadow-sm)]">
        <h2 className="mb-3 mt-0 text-base font-semibold">What you can do next</h2>
        <div className="flex flex-wrap gap-2">
          <Link to={`/integrations?tenant_id=${tenant.id}`} className="no-underline">
            <Button size="sm">Shortcodes</Button>
          </Link>
          <Link to={`/webhooks?tenant_id=${tenant.id}`} className="no-underline">
            <Button size="sm" variant="secondary">
              Notifications
            </Button>
          </Link>
          <Link to="/intents" className="no-underline">
            <Button size="sm" variant="secondary">
              Payments
            </Button>
          </Link>
          <Link to={`/oauth-clients?tenant_id=${tenant.id}`} className="no-underline">
            <Button size="sm" variant="secondary">
              API clients
            </Button>
          </Link>
        </div>
        <p className={`mb-0 mt-4 text-xs text-[var(--muted)] ${mono}`}>{tenant.id}</p>
      </div>
    </div>
  )
}
