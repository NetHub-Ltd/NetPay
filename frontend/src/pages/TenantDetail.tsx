import { type FormEvent, useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Landmark, Plus } from 'lucide-react'
import { api, ApiError, type Integration, type Tenant } from '../api/client'
import { EmptyState } from '../components/EmptyState'
import { PageHeader } from '../components/PageHeader'
import { StatusBadge } from '../components/StatusBadge'
import { Button, Input, Modal, PageLoader } from '../components/primitives'
import { BUSINESS_CATEGORIES } from '../lib/businessCategories'
import { mono, table, tableWrap } from '../components/ui'

const selectClass =
  'w-full rounded-xl border border-[var(--border)] bg-[var(--panel)] px-3.5 py-2.5 text-sm shadow-[var(--shadow-sm)] focus:border-[var(--accent)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/25'

export function TenantDetail() {
  const { id } = useParams()
  const [tenant, setTenant] = useState<Tenant | null>(null)
  const [shortcodes, setShortcodes] = useState<Integration[]>([])
  const [error, setError] = useState<string | null>(null)
  const [msg, setMsg] = useState<string | null>(null)
  const [editOpen, setEditOpen] = useState(false)
  const [scOpen, setScOpen] = useState(false)
  const [busy, setBusy] = useState(false)
  const [form, setForm] = useState({
    name: '',
    category: 'retail',
    email: '',
    phone_number: '',
    status: 'active' as 'active' | 'inactive',
  })
  const [scForm, setScForm] = useState({
    shortcode: '',
    type: 'paybill',
    environment: 'sandbox',
    consumer_key: '',
    consumer_secret: '',
    passkey: '',
  })

  const load = useCallback(async () => {
    if (!id) return
    try {
      const t = await api.get<Tenant>(`/v1/tenants/${id}`)
      setTenant(t)
      setForm({
        name: t.name,
        category: t.category || 'other',
        email: t.email || '',
        phone_number: t.phone_number || '',
        status: (t.status === 'inactive' ? 'inactive' : 'active') as 'active' | 'inactive',
      })
      const list = await api.get<Integration[]>(`/v1/integrations?tenant_id=${id}`)
      setShortcodes(list)
      setError(null)
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Could not load business')
    }
  }, [id])

  useEffect(() => {
    void Promise.resolve().then(load)
  }, [load])

  async function onSave(e: FormEvent) {
    e.preventDefault()
    if (!id) return
    setBusy(true)
    setError(null)
    try {
      const updated = await api.patch<Tenant>(`/v1/tenants/${id}`, {
        name: form.name.trim(),
        category: form.category || null,
        email: form.email.trim() || null,
        phone_number: form.phone_number.trim() || null,
        status: form.status,
      })
      setTenant(updated)
      setEditOpen(false)
      setMsg('Business updated.')
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Could not save')
    } finally {
      setBusy(false)
    }
  }

  async function onToggle() {
    if (!tenant) return
    const next = tenant.status === 'active' ? 'inactive' : 'active'
    setBusy(true)
    try {
      const updated = await api.patch<Tenant>(`/v1/tenants/${tenant.id}`, { status: next })
      setTenant(updated)
      setForm((f) => ({ ...f, status: next }))
      setMsg(next === 'active' ? 'Business activated.' : 'Business deactivated.')
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Could not update status')
    } finally {
      setBusy(false)
    }
  }

  async function onDelete() {
    if (!tenant) return
    if (!window.confirm(`Remove business “${tenant.name}”? This hides it from your workspace.`)) return
    setBusy(true)
    try {
      await api.delete(`/v1/tenants/${tenant.id}`)
      window.location.assign('/tenants')
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Could not remove business')
      setBusy(false)
    }
  }

  async function onCreateShortcode(e: FormEvent) {
    e.preventDefault()
    if (!id) return
    setBusy(true)
    setError(null)
    try {
      const created = await api.post<Integration>('/v1/integrations', {
        tenant_id: id,
        ...scForm,
      })
      setScOpen(false)
      setScForm({
        shortcode: '',
        type: 'paybill',
        environment: 'sandbox',
        consumer_key: '',
        consumer_secret: '',
        passkey: '',
      })
      setMsg('Shortcode saved. Connect M-Pesa next so results reach NetPay.')
      await load()
      if (created?.id) window.location.assign(`/integrations/${created.id}`)
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Could not save shortcode')
    } finally {
      setBusy(false)
    }
  }

  async function onRetireSc(sc: Integration) {
    if (!window.confirm(`Retire shortcode ${sc.shortcode}?`)) return
    setBusy(true)
    try {
      await api.delete(`/v1/integrations/${sc.id}`)
      await load()
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Could not retire shortcode')
    } finally {
      setBusy(false)
    }
  }

  if (!id) {
    return (
      <div className="rounded-xl border border-[var(--danger)]/25 bg-[var(--danger-soft)] px-4 py-3 text-sm text-[var(--danger)]">
        Business not found
      </div>
    )
  }
  if (error && !tenant) {
    return (
      <div className="rounded-xl border border-[var(--danger)]/25 bg-[var(--danger-soft)] px-4 py-3 text-sm text-[var(--danger)]" role="alert">
        {error}
      </div>
    )
  }
  if (!tenant) return <PageLoader label="Loading business…" />

  return (
    <div data-testid="tenant-detail-page" className="space-y-6">
      <p className="mb-0 text-sm text-[var(--muted)]">
        <Link to="/tenants">← Businesses</Link>
      </p>
      <PageHeader
        title={tenant.name}
        description={[tenant.category, tenant.email, tenant.phone_number, tenant.slug]
          .filter(Boolean)
          .join(' · ')}
        actions={
          <div className="flex flex-wrap gap-2">
            <StatusBadge value={tenant.status} />
            <Button size="sm" variant="secondary" onClick={() => setEditOpen(true)}>
              Edit
            </Button>
            <Button size="sm" variant="secondary" disabled={busy} onClick={() => void onToggle()}>
              {tenant.status === 'active' ? 'Deactivate' : 'Activate'}
            </Button>
          </div>
        }
      />

      {error && (
        <div className="rounded-xl border border-[var(--danger)]/25 bg-[var(--danger-soft)] px-4 py-3 text-sm text-[var(--danger)]" role="alert">
          {error}
        </div>
      )}
      {msg && (
        <div className="rounded-xl border border-[var(--accent)]/25 bg-[var(--accent-soft)] px-4 py-3 text-sm">
          {msg}
        </div>
      )}

      <section>
        <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
          <h2 className="m-0 text-base font-semibold">Shortcodes</h2>
          <Button
            size="sm"
            leftIcon={<Plus size={16} />}
            disabled={tenant.status !== 'active'}
            title={tenant.status !== 'active' ? 'Activate the business first' : undefined}
            onClick={() => setScOpen(true)}
          >
            Add shortcode
          </Button>
        </div>
        {shortcodes.length === 0 ? (
          <EmptyState
            icon={<Landmark size={22} />}
            title="No shortcodes for this business"
            hint="Add a paybill or till. Credentials are verified with Safaricom before saving."
            action={
              tenant.status === 'active' ? (
                <Button leftIcon={<Plus size={16} />} onClick={() => setScOpen(true)}>
                  Add shortcode
                </Button>
              ) : undefined
            }
          />
        ) : (
          <div className={tableWrap}>
            <table className={table}>
              <thead>
                <tr>
                  <th>Shortcode</th>
                  <th>Type</th>
                  <th>Env</th>
                  <th>Status</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {shortcodes.map((s) => (
                  <tr key={s.id}>
                    <td>
                      <strong>{s.shortcode}</strong>
                      <div className={`${mono} text-xs text-[var(--muted)]`}>{s.public_id}</div>
                    </td>
                    <td>{s.type === 'till' ? 'Till' : 'Paybill'}</td>
                    <td>{s.environment === 'production' ? 'Live' : 'Test'}</td>
                    <td>
                      <StatusBadge value={s.connected ? 'connected' : s.status} />
                    </td>
                    <td>
                      <div className="flex flex-wrap justify-end gap-2">
                        <Link to={`/integrations/${s.id}`} className="no-underline">
                          <Button size="sm">Open</Button>
                        </Link>
                        <Button size="sm" variant="secondary" disabled={busy} onClick={() => void onRetireSc(s)}>
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
      </section>

      <div className="flex flex-wrap gap-2 border-t border-[var(--border)] pt-4">
        <Button size="sm" variant="danger" disabled={busy} onClick={() => void onDelete()}>
          Remove business
        </Button>
      </div>

      <Modal
        open={editOpen}
        title="Edit business"
        onClose={() => !busy && setEditOpen(false)}
        footer={
          <>
            <Button variant="secondary" disabled={busy} onClick={() => setEditOpen(false)}>
              Cancel
            </Button>
            <Button form="np-biz-edit" type="submit" loading={busy}>
              Save
            </Button>
          </>
        }
      >
        <form id="np-biz-edit" className="flex flex-col gap-3" onSubmit={(e) => void onSave(e)}>
          <Input label="Name" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <label className="flex flex-col gap-1.5 text-sm">
            <span className="font-medium">Category</span>
            <select className={selectClass} value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
              {BUSINESS_CATEGORIES.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label}
                </option>
              ))}
            </select>
          </label>
          <Input label="Email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          <Input label="Phone" value={form.phone_number} onChange={(e) => setForm({ ...form, phone_number: e.target.value })} />
          <label className="flex flex-col gap-1.5 text-sm">
            <span className="font-medium">Status</span>
            <select
              className={selectClass}
              value={form.status}
              onChange={(e) => setForm({ ...form, status: e.target.value as 'active' | 'inactive' })}
            >
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </label>
        </form>
      </Modal>

      <Modal
        open={scOpen}
        title="Add shortcode"
        onClose={() => !busy && setScOpen(false)}
        footer={
          <>
            <Button variant="secondary" disabled={busy} onClick={() => setScOpen(false)}>
              Cancel
            </Button>
            <Button form="np-sc-create" type="submit" loading={busy}>
              Save shortcode
            </Button>
          </>
        }
      >
        <p className="mb-3 mt-0 text-xs text-[var(--muted)]">
          Pinned to <strong>{tenant.name}</strong>. Keys are verified with Safaricom before saving.
        </p>
        <form id="np-sc-create" className="flex flex-col gap-3" onSubmit={(e) => void onCreateShortcode(e)}>
          <Input label="Shortcode" required value={scForm.shortcode} onChange={(e) => setScForm({ ...scForm, shortcode: e.target.value })} />
          <label className="flex flex-col gap-1.5 text-sm">
            <span className="font-medium">Type</span>
            <select className={selectClass} value={scForm.type} onChange={(e) => setScForm({ ...scForm, type: e.target.value })}>
              <option value="paybill">Paybill</option>
              <option value="till">Till</option>
            </select>
          </label>
          <label className="flex flex-col gap-1.5 text-sm">
            <span className="font-medium">Environment</span>
            <select
              className={selectClass}
              value={scForm.environment}
              onChange={(e) => setScForm({ ...scForm, environment: e.target.value })}
            >
              <option value="sandbox">Test (sandbox)</option>
              <option value="production">Live</option>
            </select>
          </label>
          <Input label="Consumer key" required value={scForm.consumer_key} onChange={(e) => setScForm({ ...scForm, consumer_key: e.target.value })} autoComplete="off" />
          <Input label="Consumer secret" required type="password" value={scForm.consumer_secret} onChange={(e) => setScForm({ ...scForm, consumer_secret: e.target.value })} autoComplete="off" />
          <Input label="Passkey" required type="password" value={scForm.passkey} onChange={(e) => setScForm({ ...scForm, passkey: e.target.value })} autoComplete="off" />
        </form>
      </Modal>
    </div>
  )
}
