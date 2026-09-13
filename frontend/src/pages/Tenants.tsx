import { type FormEvent, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, ApiError, type Tenant } from '../api/client'
import { EmptyState } from '../components/EmptyState'
import { StatusBadge } from '../components/StatusBadge'
import { useAuth } from '../auth/AuthContext'
import { Navigate } from 'react-router-dom'

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
    if (isAdmin) load()
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
      <div className="page-header">
        <div>
          <h1>Businesses</h1>
          <p>Client organizations (admin only)</p>
        </div>
      </div>
      {error && <div className="alert error">{error}</div>}

      <div className="card">
        <h2>Onboard client</h2>
        <form onSubmit={onCreate} className="grid-2">
          <div>
            <label>Name</label>
            <input value={name} onChange={(e) => setName(e.target.value)} required placeholder="Acme Retail" />
          </div>
          <div>
            <label>Slug</label>
            <input value={slug} onChange={(e) => setSlug(e.target.value)} placeholder="acme-retail" />
          </div>
          <div className="form-actions">
            <button className="btn primary" type="submit" disabled={busy}>{busy ? 'Creating…' : 'Create tenant'}</button>
          </div>
        </form>
      </div>

      {items.length === 0 ? (
        <EmptyState title="No tenants yet" hint="Create a client organization to begin onboarding." />
      ) : (
        <div className="card">
          <table>
            <thead>
              <tr><th>Name</th><th>Slug</th><th>Status</th><th>Created</th><th></th></tr>
            </thead>
            <tbody>
              {items.map((t) => (
                <tr key={t.id}>
                  <td>{t.name}</td>
                  <td className="mono">{t.slug}</td>
                  <td><StatusBadge value={t.status} /></td>
                  <td className="muted tiny">{new Date(t.created_at).toLocaleString()}</td>
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
