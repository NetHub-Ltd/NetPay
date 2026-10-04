import { type FormEvent, useCallback, useEffect, useState } from 'react'
import { Link, Navigate, useSearchParams } from 'react-router-dom'
import { Building2, Plus } from 'lucide-react'
import { api, ApiError, type Tenant } from '../api/client'
import { EmptyState } from '../components/EmptyState'
import { PageHeader } from '../components/PageHeader'
import { useAuth } from '../auth/authState'
import { Button, Input, Modal } from '../components/primitives'
import { mono, table, tableWrap } from '../components/ui'

export function Tenants() {
  const { isAdmin, user, establishSession } = useAuth()
  const [params] = useSearchParams()
  const wantSelf = params.get('self') === '1'
  const [items, setItems] = useState<Tenant[]>([])
  const [error, setError] = useState<string | null>(null)
  const [msg, setMsg] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(wantSelf && !user?.tenant_id)
  const [busy, setBusy] = useState(false)
  const [name, setName] = useState('')

  const load = useCallback(async () => {
    if (!isAdmin) return
    try {
      setItems(await api.get<Tenant[]>('/v1/tenants'))
      setError(null)
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Could not load businesses')
    }
  }, [isAdmin])

  useEffect(() => {
    if (isAdmin) void Promise.resolve().then(load)
  }, [isAdmin, load])

  // Non-admin with a business: no admin list — send home
  if (!isAdmin && user?.tenant_id && !wantSelf) {
    return <Navigate to="/dashboard" replace />
  }
  if (!isAdmin && user?.tenant_id && wantSelf) {
    return <Navigate to="/dashboard" replace />
  }

  async function onCreateAdmin(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    setMsg(null)
    try {
      const slug = name
        .trim()
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-|-$/g, '')
        .slice(0, 40)
      await api.post<Tenant>('/v1/tenants', { name: name.trim(), slug })
      setName('')
      setShowForm(false)
      setMsg('Business created.')
      await load()
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Could not create business')
    } finally {
      setBusy(false)
    }
  }

  async function onSelfRegister(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    setMsg(null)
    try {
      await api.post<Tenant>('/v1/tenants/self', { name: name.trim() })
      setMsg('Business created. You can add a shortcode next.')
      setShowForm(false)
      const token = sessionStorage.getItem('nethub_token')
      if (token) {
        try {
          await establishSession(token)
        } catch {
          /* ignore */
        }
      }
      window.location.assign('/integrations')
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Could not create business')
      setBusy(false)
    }
  }

  // Free-tier self-serve only
  if (!isAdmin) {
    return (
      <div>
        <PageHeader
          title="Your business"
          description="Free tier includes one business workspace linked to your account."
        />
        {error && (
          <div
            className="mb-4 rounded-xl border border-[var(--danger)]/25 bg-[var(--danger-soft)] px-4 py-3 text-sm text-[var(--danger)]"
            role="alert"
          >
            {error}
          </div>
        )}
        {msg && (
          <div className="mb-4 rounded-xl border border-[var(--accent)]/25 bg-[var(--accent-soft)] px-4 py-3 text-sm">
            {msg}
          </div>
        )}
        <EmptyState
          icon={<Building2 size={22} />}
          title="Create your business"
          hint="One workspace on the free tier. You can add a shortcode right after."
          action={
            <Button leftIcon={<Plus size={16} />} onClick={() => setShowForm(true)}>
              Create business
            </Button>
          }
        />
        <Modal
          open={showForm}
          title="Create business"
          onClose={() => !busy && setShowForm(false)}
          footer={
            <>
              <Button variant="secondary" disabled={busy} onClick={() => setShowForm(false)}>
                Cancel
              </Button>
              <Button form="np-self-biz" type="submit" loading={busy}>
                Create
              </Button>
            </>
          }
        >
          <form id="np-self-biz" onSubmit={(e) => void onSelfRegister(e)}>
            <Input
              label="Business name"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Acme Retail"
            />
          </form>
        </Modal>
      </div>
    )
  }

  return (
    <div>
      <PageHeader
        title="Businesses"
        description="Organizations that own shortcodes and payment activity (admin)."
        actions={
          <Button leftIcon={<Plus size={16} />} onClick={() => setShowForm(true)}>
            Add business
          </Button>
        }
      />

      {error && (
        <div
          className="mb-4 rounded-xl border border-[var(--danger)]/25 bg-[var(--danger-soft)] px-4 py-3 text-sm text-[var(--danger)]"
          role="alert"
        >
          {error}
        </div>
      )}
      {msg && (
        <div className="mb-4 rounded-xl border border-[var(--accent)]/25 bg-[var(--accent-soft)] px-4 py-3 text-sm">
          {msg}
        </div>
      )}

      {items.length === 0 ? (
        <EmptyState
          icon={<Building2 size={22} />}
          title="No businesses yet"
          hint="Create a business, then attach shortcodes."
          action={
            <Button leftIcon={<Plus size={16} />} onClick={() => setShowForm(true)}>
              Add business
            </Button>
          }
        />
      ) : (
        <div className={tableWrap}>
          <table className={table}>
            <thead>
              <tr>
                <th>Name</th>
                <th>Id</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items.map((t) => (
                <tr key={t.id}>
                  <td className="font-semibold">{t.name}</td>
                  <td className={`${mono} text-xs text-[var(--muted)]`}>{t.id}</td>
                  <td>
                    <Link to={`/tenants/${t.id}`} className="no-underline">
                      <Button size="sm" variant="secondary">
                        Open
                      </Button>
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal
        open={showForm}
        title="Add business"
        onClose={() => !busy && setShowForm(false)}
        footer={
          <>
            <Button variant="secondary" disabled={busy} onClick={() => setShowForm(false)}>
              Cancel
            </Button>
            <Button form="np-tenant-form" type="submit" loading={busy}>
              Save
            </Button>
          </>
        }
      >
        <form id="np-tenant-form" onSubmit={(e) => void onCreateAdmin(e)}>
          <Input
            label="Business name"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Acme Retail"
          />
        </form>
      </Modal>
    </div>
  )
}
