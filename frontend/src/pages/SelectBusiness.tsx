import { type FormEvent, useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { Building2, Plus } from 'lucide-react'
import { api, ApiError } from '../api/client'
import { useAuth } from '../auth/authState'
import { useWorkspace } from '../workspace/useWorkspace'
import { Button, Input } from '../components/primitives'
import { BUSINESS_CATEGORIES } from '../lib/businessCategories'

const selectClass =
  'w-full rounded-xl border border-[var(--border)] bg-[var(--panel)] px-3.5 py-2.5 text-sm shadow-[var(--shadow-sm)] focus:border-[var(--accent)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/25'

export function SelectBusiness() {
  const navigate = useNavigate()
  const { user, loading: authLoading } = useAuth()
  const { businesses, loading, activeTenantId, setActiveTenantId, refreshBusinesses } =
    useWorkspace()
  const [showCreate, setShowCreate] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [form, setForm] = useState({
    name: '',
    category: 'retail',
    email: '',
    phone_number: '',
  })

  if (authLoading || loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[var(--bg)] text-sm text-[var(--muted)]">
        Loading your businesses…
      </div>
    )
  }
  if (!user) return <Navigate to="/login" replace />
  if (activeTenantId) return <Navigate to="/dashboard" replace />

  async function choose(id: string) {
    setActiveTenantId(id)
    navigate('/dashboard', { replace: true })
  }

  async function onCreate(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const created = await api.post<{ id: string }>('/v1/tenants', {
        name: form.name.trim(),
        category: form.category || null,
        email: form.email.trim() || null,
        phone_number: form.phone_number.trim() || null,
        status: 'active',
      })
      await refreshBusinesses()
      setActiveTenantId(created.id)
      navigate('/dashboard', { replace: true })
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Could not create business')
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
          <h1 className="m-0 text-xl font-bold text-[var(--text)]">Choose a business</h1>
          <p className="mb-0 mt-2 text-sm text-[var(--muted)]">
            NetPay works in one business at a time. Pick where you want to work, or create a new
            one.
          </p>
        </div>

        {error && (
          <div
            className="rounded-xl border border-[var(--danger)]/25 bg-[var(--danger-soft)] px-4 py-3 text-sm text-[var(--danger)]"
            role="alert"
          >
            {error}
          </div>
        )}

        {!showCreate && businesses.length > 0 && (
          <ul className="m-0 list-none space-y-2 p-0">
            {businesses.map((b) => (
              <li key={b.id}>
                <button
                  type="button"
                  className="flex w-full items-center justify-between rounded-2xl border border-[var(--border)] bg-[var(--panel)] px-4 py-3 text-left shadow-[var(--shadow-sm)] transition hover:border-[var(--accent)]/40"
                  onClick={() => void choose(b.id)}
                >
                  <span>
                    <span className="block font-semibold text-[var(--text)]">{b.name}</span>
                    <span className="text-xs text-[var(--muted)] capitalize">
                      {b.category || 'Business'} · {b.status}
                    </span>
                  </span>
                  <span className="text-sm font-medium text-[var(--accent)]">Open →</span>
                </button>
              </li>
            ))}
          </ul>
        )}

        {!showCreate && (
          <Button
            className="w-full"
            variant={businesses.length ? 'secondary' : 'primary'}
            leftIcon={<Plus size={16} />}
            onClick={() => setShowCreate(true)}
          >
            Create a business
          </Button>
        )}

        {showCreate && (
          <form
            className="space-y-3 rounded-2xl border border-[var(--border)] bg-[var(--panel)] p-5 shadow-[var(--shadow-sm)]"
            onSubmit={(e) => void onCreate(e)}
          >
            <h2 className="m-0 text-base font-semibold">New business</h2>
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
            <div className="flex flex-wrap gap-2 pt-2">
              <Button type="submit" loading={busy}>
                Create & continue
              </Button>
              {businesses.length > 0 && (
                <Button type="button" variant="secondary" disabled={busy} onClick={() => setShowCreate(false)}>
                  Back to list
                </Button>
              )}
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
