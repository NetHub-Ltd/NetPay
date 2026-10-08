import { type FormEvent, type MouseEvent, useState } from 'react'
import { Navigate, useNavigate, useSearchParams } from 'react-router-dom'
import { Building2, Pencil, Plus, Trash2 } from 'lucide-react'
import { api, ApiError, type Tenant } from '../api/client'
import { useAuth } from '../auth/authState'
import { useWorkspace } from '../workspace/useWorkspace'
import { Button, ConfirmModal, Input, Modal } from '../components/primitives'
import { BUSINESS_CATEGORIES } from '../lib/businessCategories'
import { DismissibleBanner } from '../components/DismissibleBanner'

const selectClass =
  'w-full rounded-xl border border-[var(--border)] bg-[var(--panel)] px-3.5 py-2.5 text-sm shadow-[var(--shadow-sm)] focus:border-[var(--accent)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/25'

const emptyForm = {
  name: '',
  category: 'retail',
  email: '',
  phone_number: '',
  status: 'active',
}

export function SelectBusiness() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const switching = params.get('switch') === '1'
  const { user, loading: authLoading } = useAuth()
  const {
    businesses,
    loading,
    activeTenantId,
    setActiveTenantId,
    clearActiveTenant,
    refreshBusinesses,
  } = useWorkspace()
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<Tenant | null>(null)
  const [busy, setBusy] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<Tenant | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [form, setForm] = useState(emptyForm)

  // Resume into app only when a business is already chosen and user is not switching
  if (authLoading || loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[var(--bg)] text-sm text-[var(--muted)]">
        Loading your businesses…
      </div>
    )
  }
  if (!user) return <Navigate to="/login" replace />
  if (activeTenantId && !switching) return <Navigate to="/dashboard" replace />

  function openCreate() {
    setEditing(null)
    setForm(emptyForm)
    setShowForm(true)
    setError(null)
  }

  function openEdit(b: Tenant, e: MouseEvent) {
    e.stopPropagation()
    setEditing(b)
    setForm({
      name: b.name || '',
      category: b.category || 'retail',
      email: b.email || '',
      phone_number: b.phone_number || '',
      status: b.status || 'active',
    })
    setShowForm(true)
    setError(null)
  }

  async function choose(id: string) {
    setActiveTenantId(id)
    navigate('/dashboard', { replace: true })
  }

  async function onSave(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      if (editing) {
        await api.patch<Tenant>(`/v1/tenants/${editing.id}`, {
          name: form.name.trim(),
          category: form.category || null,
          email: form.email.trim() || null,
          phone_number: form.phone_number.trim() || null,
          status: form.status,
        })
      } else {
        const created = await api.post<Tenant>('/v1/tenants', {
          name: form.name.trim(),
          category: form.category || null,
          email: form.email.trim() || null,
          phone_number: form.phone_number.trim() || null,
          status: 'active',
        })
        await refreshBusinesses()
        setShowForm(false)
        // Creating does not force lock-in — user still chooses Open
        if (created?.id && businesses.length === 0) {
          setActiveTenantId(created.id)
          navigate('/dashboard', { replace: true })
          return
        }
      }
      await refreshBusinesses()
      setShowForm(false)
      setEditing(null)
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Could not save business')
    } finally {
      setBusy(false)
    }
  }

  async function onDelete(b: Tenant) {
    setDeleteTarget(null)
    setBusy(true)
    setError(null)
    try {
      await api.delete(`/v1/tenants/${b.id}`)
      if (activeTenantId === b.id) clearActiveTenant()
      await refreshBusinesses()
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Could not delete business')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--bg)] px-4 py-10">
      <div className="w-full max-w-lg space-y-6">
        <div className="text-center">
          <div className="mx-auto mb-3 flex size-12 items-center justify-center rounded-xl bg-[var(--accent)] text-white">
            <Building2 size={22} />
          </div>
          <h1 className="m-0 text-xl font-bold text-[var(--text)]">
            {switching ? 'Switch business' : 'Choose a business'}
          </h1>
          <p className="mb-0 mt-2 text-sm text-[var(--muted)]">
            Work in one business at a time. Open a card to continue, or create, edit, or delete
            businesses here.
          </p>
        </div>

        {error && (
        <DismissibleBanner tone="error" onDismiss={() => setError(null)}>
          {error}
        </DismissibleBanner>
      )}

        {businesses.length > 0 && (
          <ul className="m-0 list-none space-y-2 p-0">
            {businesses.map((b) => (
              <li key={b.id}>
                <div className="flex items-stretch gap-1 rounded-2xl border border-[var(--border)] bg-[var(--panel)] shadow-[var(--shadow-sm)]">
                  <button
                    type="button"
                    className="min-w-0 flex-1 px-4 py-3 text-left transition hover:bg-[var(--panel-2)]"
                    onClick={() => void choose(b.id)}
                    disabled={busy}
                  >
                    <span className="block font-semibold text-[var(--text)]">{b.name}</span>
                    <span className="text-xs capitalize text-[var(--muted)]">
                      {b.category || 'Business'} · {b.status}
                      {activeTenantId === b.id ? ' · current' : ''}
                    </span>
                  </button>
                  <div className="flex shrink-0 items-center gap-0.5 pr-2">
                    <button
                      type="button"
                      className="rounded-lg p-2 text-[var(--muted)] hover:bg-[var(--panel-2)] hover:text-[var(--text)]"
                      aria-label={`Edit ${b.name}`}
                      disabled={busy}
                      onClick={(e) => openEdit(b, e)}
                    >
                      <Pencil size={16} strokeWidth={1.75} />
                    </button>
                    <button
                      type="button"
                      className="rounded-lg p-2 text-[var(--muted)] hover:bg-[var(--danger-soft)] hover:text-[var(--danger)]"
                      aria-label={`Delete ${b.name}`}
                      disabled={busy}
                      onClick={(e) => { e.stopPropagation(); setDeleteTarget(b) }}
                    >
                      <Trash2 size={16} strokeWidth={1.75} />
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}

        {businesses.length === 0 && !showForm && (
          <p className="text-center text-sm text-[var(--muted)]">No businesses yet — create one to continue.</p>
        )}

        <Button className="w-full" variant={businesses.length ? 'secondary' : 'primary'} leftIcon={<Plus size={16} />} onClick={openCreate}>
          Create a business
        </Button>

        {switching && activeTenantId && (
          <button
            type="button"
            className="w-full text-center text-sm text-[var(--muted)] underline"
            onClick={() => navigate('/dashboard')}
          >
            Cancel — stay in current business
          </button>
        )}

        <Modal
          open={showForm}
          onClose={() => !busy && setShowForm(false)}
          title={editing ? 'Edit business' : 'New business'}
        >
          <form className="space-y-3" onSubmit={(e) => void onSave(e)}>
            <Input
              label="Business name"
              required
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
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
            />
            <Input
              label="Phone"
              value={form.phone_number}
              onChange={(e) => setForm({ ...form, phone_number: e.target.value })}
            />
            {editing && (
              <label className="flex flex-col gap-1.5 text-sm">
                <span className="font-medium">Status</span>
                <select
                  className={selectClass}
                  value={form.status}
                  onChange={(e) => setForm({ ...form, status: e.target.value })}
                >
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                </select>
              </label>
            )}
            <div className="flex flex-wrap gap-2 pt-2">
              <Button type="submit" loading={busy}>
                {editing ? 'Save changes' : 'Create'}
              </Button>
              <Button type="button" variant="secondary" disabled={busy} onClick={() => setShowForm(false)}>
                Cancel
              </Button>
            </div>
          </form>
        </Modal>
      </div>

      <ConfirmModal
        open={!!deleteTarget}
        title="Delete this business?"
        body={
          deleteTarget
            ? `Delete “${deleteTarget.name}”? This cannot be undone from the app. Prefer deactivating if you may need history.`
            : ''
        }
        confirmLabel="Delete"
        danger
        busy={busy}
        onCancel={() => !busy && setDeleteTarget(null)}
        onConfirm={() => deleteTarget && void onDelete(deleteTarget)}
      />
    </div>
  )
}
