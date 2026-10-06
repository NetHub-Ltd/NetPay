import { type FormEvent, useCallback, useEffect, useState } from 'react'
import { KeyRound } from 'lucide-react'
import { api, ApiError } from '../api/client'
import { EmptyState } from '../components/EmptyState'
import { PageHeader } from '../components/PageHeader'
import { useWorkspace } from '../workspace/useWorkspace'
import { Button, Input, Modal } from '../components/primitives'
import { mono } from '../components/ui'

type OAuthClientCreated = {
  client_id: string
  client_secret: string
  name: string
  tenant_id: string
}

type OAuthClientRow = {
  client_id: string
  name: string
  tenant_id: string
  is_active: boolean
  created_at?: string | null
}

export function OAuthClients() {
  const { activeTenantId, activeBusiness } = useWorkspace()
  const [items, setItems] = useState<OAuthClientRow[]>([])
  const [name, setName] = useState('Default API client')
  const [created, setCreated] = useState<OAuthClientCreated | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)

  const load = useCallback(async () => {
    if (!activeTenantId) return
    setLoading(true)
    try {
      const rows = await api.get<OAuthClientRow[]>(
        `/v1/oauth/clients?tenant_id=${activeTenantId}`,
      )
      setItems(rows)
      setError(null)
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Could not load API clients')
      setItems([])
    } finally {
      setLoading(false)
    }
  }, [activeTenantId])

  useEffect(() => {
    void Promise.resolve().then(load)
  }, [load])

  async function onCreate(e: FormEvent) {
    e.preventDefault()
    if (!activeTenantId) {
      setError('Select a business in the sidebar first.')
      return
    }
    setBusy(true)
    setError(null)
    setCreated(null)
    try {
      const res = await api.post<OAuthClientCreated>('/v1/oauth/clients', {
        tenant_id: activeTenantId,
        name: name.trim() || 'API client',
      })
      setCreated(res)
      setShowForm(false)
      await load()
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Could not create API client')
    } finally {
      setBusy(false)
    }
  }

  const biz = activeBusiness?.name || 'this business'

  return (
    <div>
      <PageHeader
        title="Connect your system"
        description={`Let your backend start payments for ${biz} and receive results. Create a client, exchange it for a token, then call the payment API. Secret is shown only once.`}
        actions={
          <Button
            disabled={!activeTenantId}
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
        <div
          className="mb-4 rounded-xl border border-[var(--danger)]/25 bg-[var(--danger-soft)] px-4 py-3 text-sm text-[var(--danger)]"
          role="alert"
        >
          {error}
        </div>
      )}

      {created && (
        <div
          className="mb-4 rounded-xl border border-[var(--accent)]/30 bg-[var(--accent-soft)] px-4 py-3 text-sm"
          role="status"
        >
          <p className="m-0 font-semibold text-[var(--text)]">Client created — copy the secret now</p>
          <p className="mb-2 mt-1 text-xs text-[var(--muted)]">
            The secret is not shown again. Name: {created.name}
          </p>
          <div className="space-y-1 font-mono text-xs">
            <div>
              <span className="text-[var(--muted)]">client_id </span>
              <span className={mono}>{created.client_id}</span>
            </div>
            <div>
              <span className="text-[var(--muted)]">client_secret </span>
              <span className={mono}>{created.client_secret}</span>
            </div>
          </div>
          <Button className="mt-3" variant="secondary" size="sm" onClick={() => setCreated(null)}>
            Dismiss
          </Button>
        </div>
      )}

      {loading ? (
        <p className="text-sm text-[var(--muted)]">Loading…</p>
      ) : items.length === 0 ? (
        <EmptyState
          icon={<KeyRound size={22} />}
          title="No API clients yet"
          hint={`Create a client so your backend can request payments for ${biz}.`}
          action={
            <Button disabled={!activeTenantId} onClick={() => setShowForm(true)}>
              Create client
            </Button>
          }
        />
      ) : (
        <ul className="m-0 list-none space-y-2 p-0">
          {items.map((c) => (
            <li
              key={c.client_id}
              className="rounded-xl border border-[var(--border)] bg-[var(--panel)] px-4 py-3 shadow-[var(--shadow-sm)]"
            >
              <div className="font-semibold text-[var(--text)]">{c.name}</div>
              <div className={`mt-1 text-xs text-[var(--muted)] ${mono}`}>{c.client_id}</div>
              <div className="mt-1 text-xs text-[var(--muted)]">
                {c.is_active ? 'Active' : 'Inactive'}
                {c.created_at ? ` · ${new Date(c.created_at).toLocaleString()}` : ''}
              </div>
            </li>
          ))}
        </ul>
      )}

      <Modal open={showForm} onClose={() => !busy && setShowForm(false)} title="Create API client">
        <form className="space-y-4" onSubmit={(e) => void onCreate(e)}>
          <p className="m-0 text-sm text-[var(--muted)]">
            Client will be created for <strong className="text-[var(--text)]">{biz}</strong>. Switch business in
            the sidebar if you need a different one.
          </p>
          <Input
            label="Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Production backend"
          />
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" disabled={busy} onClick={() => setShowForm(false)}>
              Cancel
            </Button>
            <Button type="submit" loading={busy}>
              Create
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
