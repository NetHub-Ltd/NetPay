import { type FormEvent, useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Building2, Plus } from 'lucide-react'
import { api, ApiError, type Tenant } from '../api/client'
import { EmptyState } from '../components/EmptyState'
import { PageHeader } from '../components/PageHeader'
import { StatusBadge } from '../components/StatusBadge'
import { useAuth } from '../auth/authState'
import { Button, Input, Modal } from '../components/primitives'
import { BUSINESS_CATEGORIES } from '../lib/businessCategories'
import { mono, table, tableWrap } from '../components/ui'

const selectClass =
  'w-full rounded-xl border border-[var(--border)] bg-[var(--panel)] px-3.5 py-2.5 text-sm shadow-[var(--shadow-sm)] focus:border-[var(--accent)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/25'

export function Tenants() {
  const { establishSession } = useAuth()
  const [items, setItems] = useState<Tenant[]>([])
  const [error, setError] = useState<string | null>(null)
  const [msg, setMsg] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [busy, setBusy] = useState(false)
  const [form, setForm] = useState({
    name: '',
    category: 'retail',
    email: '',
    phone_number: '',
  })

  const load = useCallback(async () => {
    try {
      setItems(await api.get<Tenant[]>('/v1/tenants'))
      setError(null)
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Could not load businesses')
    }
  }, [])

  useEffect(() => {
    void Promise.resolve().then(load)
  }, [load])

  async function onCreate(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    setMsg(null)
    try {
      await api.post<Tenant>('/v1/tenants', {
        name: form.name.trim(),
        category: form.category || null,
        email: form.email.trim() || null,
        phone_number: form.phone_number.trim() || null,
        status: 'active',
      })
      setForm({ name: '', category: 'retail', email: '', phone_number: '' })
      setShowForm(false)
      setMsg('Business created.')
      const token = sessionStorage.getItem('nethub_token')
      if (token) {
        try {
          await establishSession(token)
        } catch {
          /* ignore */
        }
      }
      await load()
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Could not create business')
    } finally {
      setBusy(false)
    }
  }

  async function toggleStatus(t: Tenant) {
    const next = t.status === 'active' ? 'inactive' : 'active'
    setBusy(true)
    try {
      await api.patch<Tenant>(`/v1/tenants/${t.id}`, { status: next })
      await load()
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Could not update status')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <PageHeader
        title="Manage businesses"
        description="Create or update businesses. Day-to-day work uses Working in on the sidebar — this page is for managing the list."
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
          hint="Create a business with contact details, then add shortcodes inside it."
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
                <th>Category</th>
                <th>Contact</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items.map((t) => (
                <tr key={t.id}>
                  <td>
                    <Link to={`/tenants/${t.id}`} className="font-semibold text-[var(--text)]">
                      {t.name}
                    </Link>
                    <div className={`${mono} text-xs text-[var(--muted)]`}>{t.slug}</div>
                  </td>
                  <td className="text-sm capitalize text-[var(--muted)]">
                    {t.category || '—'}
                  </td>
                  <td className="text-sm text-[var(--muted)]">
                    {[t.email, t.phone_number].filter(Boolean).join(' · ') || '—'}
                  </td>
                  <td>
                    <StatusBadge value={t.status} />
                  </td>
                  <td>
                    <div className="flex flex-wrap justify-end gap-2">
                      <Link to={`/tenants/${t.id}`} className="no-underline">
                        <Button size="sm">Open</Button>
                      </Link>
                      <Button
                        size="sm"
                        variant="secondary"
                        disabled={busy}
                        onClick={() => void toggleStatus(t)}
                      >
                        {t.status === 'active' ? 'Deactivate' : 'Activate'}
                      </Button>
                    </div>
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
        <form id="np-tenant-form" className="flex flex-col gap-3" onSubmit={(e) => void onCreate(e)}>
          <Input
            label="Business name"
            required
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            placeholder="e.g. Acme Retail"
          />
          <label className="flex flex-col gap-1.5 text-sm">
            <span className="font-medium">Category</span>
            <select
              className={selectClass}
              value={form.category}
              onChange={(e) => setForm({ ...form, category: e.target.value })}
            >
              {BUSINESS_CATEGORIES.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label}
                </option>
              ))}
            </select>
          </label>
          <Input
            label="Email"
            type="email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            placeholder="billing@business.co.ke"
          />
          <Input
            label="Phone"
            type="tel"
            value={form.phone_number}
            onChange={(e) => setForm({ ...form, phone_number: e.target.value })}
            placeholder="2547…"
          />
        </form>
      </Modal>
    </div>
  )
}
