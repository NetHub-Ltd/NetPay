import { type FormEvent, useCallback, useEffect, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { Building2, Plus } from 'lucide-react'
import { api, ApiError, type Tenant } from '../api/client'
import { EmptyState } from '../components/EmptyState'
import { PageHeader } from '../components/PageHeader'
import { useAuth } from '../auth/authState'
import { Button, Input, Modal } from '../components/primitives'
import { mono, table, tableWrap } from '../components/ui'

export function Tenants() {
  const { isAdmin } = useAuth()
  const [items, setItems] = useState<Tenant[]>([])
  const [error, setError] = useState<string | null>(null)
  const [msg, setMsg] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [busy, setBusy] = useState(false)
  const [name, setName] = useState('')

  const load = useCallback(async () => {
    try {
      setItems(await api.get<Tenant[]>('/v1/tenants'))
      setError(null)
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Could not load businesses')
    }
  }, [])

  useEffect(() => {
    if (isAdmin) void Promise.resolve().then(load)
  }, [isAdmin, load])

  if (!isAdmin) return <Navigate to="/forbidden" replace />

  async function onCreate(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    setMsg(null)
    try {
      await api.post<Tenant>('/v1/tenants', { name: name.trim() })
      setName('')
      setShowForm(false)
      setMsg('Business created. You can add shortcodes for it next.')
      await load()
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Could not create business')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <PageHeader
        title="Businesses"
        description="Organizations that own shortcodes and payment activity (admin only)."
        actions={
          <Button leftIcon={<Plus size={16} />} onClick={() => setShowForm(true)}>
            Add business
          </Button>
        }
      />

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

      {items.length === 0 ? (
        <EmptyState
          icon={<Building2 size={22} />}
          title="No businesses yet"
          hint="Create a business, then attach shortcodes and users to it."
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
        <form id="np-tenant-form" onSubmit={(e) => void onCreate(e)}>
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
