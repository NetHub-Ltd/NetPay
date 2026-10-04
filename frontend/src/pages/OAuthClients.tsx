import { type FormEvent, useEffect, useState } from 'react'
import { Navigate, useSearchParams } from 'react-router-dom'
import { KeyRound } from 'lucide-react'
import { api, ApiError, type Tenant } from '../api/client'
import { EmptyState } from '../components/EmptyState'
import { PageHeader } from '../components/PageHeader'
import { useAuth } from '../auth/authState'
import { Button, Input, Modal } from '../components/primitives'
import { mono } from '../components/ui'

type OAuthClientOut = {
  client_id: string
  client_secret: string
  name: string
  tenant_id: string
}

export function OAuthClients() {
  const { isAdmin } = useAuth()
  const [params] = useSearchParams()
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [tenantId, setTenantId] = useState(params.get('tenant_id') || '')
  const [name, setName] = useState('Default API client')
  const [created, setCreated] = useState<OAuthClientOut | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [showForm, setShowForm] = useState(false)

  useEffect(() => {
    if (!isAdmin) return
    api
      .get<Tenant[]>('/v1/tenants')
      .then((t) => {
        setTenants(t)
        setTenantId((current) => current || t[0]?.id || '')
      })
      .catch(() => {})
  }, [isAdmin])

  if (!isAdmin) return <Navigate to="/forbidden" replace />

  async function onCreate(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    setCreated(null)
    try {
      const res = await api.post<OAuthClientOut>('/v1/oauth/clients', {
        tenant_id: tenantId,
        name: name.trim(),
      })
      setCreated(res)
      setShowForm(false)
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Could not create API client')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <PageHeader
        title="Apps & API access"
        description="Machine credentials for systems that call NetPay on behalf of a business (admin only)."
        actions={
          <Button
            disabled={!tenantId}
            onClick={() => {
              setError(null)
              setShowForm(true)
            }}
          >
            Create client
          </Button>
        }
      />

      {error && (
        <div className="mb-4 rounded-xl border border-[var(--danger)]/25 bg-[var(--danger-soft)] px-4 py-3 text-sm text-[var(--danger)]" role="alert">
          {error}
        </div>
      )}

      {created && (
        <div className="mb-4 rounded-xl border border-[var(--warn)]/30 bg-[var(--warn-soft)] px-4 py-3 text-sm">
          <p className="m-0 font-semibold">Copy the secret now — it will not be shown again.</p>
          <p className="mb-1 mt-3 text-xs text-[var(--muted)]">Client ID</p>
          <code className={`${mono} break-all`}>{created.client_id}</code>
          <p className="mb-1 mt-3 text-xs text-[var(--muted)]">Client secret</p>
          <code className={`${mono} break-all`}>{created.client_secret}</code>
          <div className="mt-3">
            <Button size="sm" variant="secondary" onClick={() => setCreated(null)}>
              Dismiss
            </Button>
          </div>
        </div>
      )}

      {!tenantId && tenants.length === 0 ? (
        <EmptyState
          icon={<KeyRound size={22} />}
          title="No businesses yet"
          hint="Create a business first, then issue API credentials for it."
        />
      ) : (
        <p className="text-sm text-[var(--muted)]">
          Choose a business and create a client when your backend needs to call NetPay with
          client-credentials.
        </p>
      )}

      <Modal
        open={showForm}
        title="Create API client"
        onClose={() => !busy && setShowForm(false)}
        footer={
          <>
            <Button variant="secondary" disabled={busy} onClick={() => setShowForm(false)}>
              Cancel
            </Button>
            <Button form="np-oauth-form" type="submit" loading={busy} disabled={!tenantId}>
              Create
            </Button>
          </>
        }
      >
        <form id="np-oauth-form" className="flex flex-col gap-3" onSubmit={(e) => void onCreate(e)}>
          <label className="flex flex-col gap-1.5 text-sm">
            <span className="font-medium">Business</span>
            <select
              className="rounded-xl border border-[var(--border)] bg-[var(--panel)] px-3.5 py-2.5 text-sm"
              required
              value={tenantId}
              onChange={(e) => setTenantId(e.target.value)}
            >
              <option value="">Select…</option>
              {tenants.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
          </label>
          <Input
            label="Name"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Production backend"
          />
        </form>
      </Modal>
    </div>
  )
}
