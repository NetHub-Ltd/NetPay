import { type FormEvent, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, ApiError, type Tenant } from '../api/client'
import { EmptyState } from '../components/EmptyState'
import { StatusBadge } from '../components/StatusBadge'
import { useAuth } from '../auth/authState'
import { Navigate } from 'react-router-dom'
import { card, control, errorAlert, label, mono, pageDescription, pageHeader, pageTitle, primaryButton, table, tableWrap } from '../components/ui'

export function Tenants() {
  const { isAdmin } = useAuth()
  const [items, setItems] = useState<Tenant[]>([])
  const [error, setError] = useState<string | null>(null)
  const [name, setName] = useState('')
  const [slug, setSlug] = useState('')
  const [busy, setBusy] = useState(false)

  async function load() {
    try {
      setItems(await api.get<Tenant[]>('/v1/tenants'))
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Failed to load tenants')
    }
  }

  useEffect(() => {
    if (isAdmin) void Promise.resolve().then(load)
  }, [isAdmin])

  if (!isAdmin) return <Navigate to="/forbidden" replace />

  async function onCreate(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await api.post('/v1/tenants', { name, slug: slug || name.toLowerCase().replace(/\s+/g, '-') })
      setName('')
      setSlug('')
      await load()
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Create failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div data-testid="tenants-page">
      <div className={pageHeader}>
        <div>
          <h1 className={pageTitle}>Businesses</h1>
          <p className={pageDescription}>Client organizations (admin only)</p>
        </div>
      </div>
      {error && <div className={errorAlert} role="alert">{error}</div>}

      <div className={card}>
        <h2 className="mb-3 text-base font-semibold">Onboard client</h2>
        <form onSubmit={onCreate} className="grid gap-4 md:grid-cols-2">
          <div>
            <label className={label}>Name</label>
            <input className={control} value={name} onChange={(e) => setName(e.target.value)} required placeholder="Acme Retail" />
          </div>
          <div>
            <label className={label}>Slug</label>
            <input className={control} value={slug} onChange={(e) => setSlug(e.target.value)} placeholder="acme-retail" />
          </div>
          <div className="md:col-span-2">
            <button className={primaryButton} type="submit" disabled={busy}>{busy ? 'Creating…' : 'Create tenant'}</button>
          </div>
        </form>
      </div>

      {items.length === 0 ? (
        <EmptyState title="No tenants yet" hint="Create a client organization to begin onboarding." />
      ) : (
        <div className={tableWrap}>
          <table className={table}>
            <thead>
              <tr><th>Name</th><th>Slug</th><th>Status</th><th>Created</th><th></th></tr>
            </thead>
            <tbody>
              {items.map((t) => (
                <tr key={t.id}>
                  <td>{t.name}</td>
                  <td className={mono}>{t.slug}</td>
                  <td><StatusBadge value={t.status} /></td>
                  <td className="text-xs text-[var(--muted)]">{new Date(t.created_at).toLocaleString()}</td>
                  <td><Link to={`/tenants/${t.id}`}>Open</Link></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
