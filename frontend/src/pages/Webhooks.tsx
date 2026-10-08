import { type FormEvent, useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Bell, Plus } from 'lucide-react'
import { api, ApiError, type Webhook } from '../api/client'
import { EmptyState } from '../components/EmptyState'
import { PageHeader } from '../components/PageHeader'
import { useWorkspace } from '../workspace/useWorkspace'
import { Button, ConfirmModal, Input, Modal } from '../components/primitives'
import { mono, table, tableWrap } from '../components/ui'
import { DismissibleBanner } from '../components/DismissibleBanner'

export function Webhooks() {
  const { activeTenantId, activeBusiness } = useWorkspace()
  const [items, setItems] = useState<Webhook[]>([])
  const tenantId = activeTenantId || ''
  const [url, setUrl] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [msg, setMsg] = useState<string | null>(null)
  const [secretOnce, setSecretOnce] = useState<string | null>(null)
  const [secretAck, setSecretAck] = useState(false)
  const [busy, setBusy] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)

  const load = useCallback(async () => {
    if (!tenantId) return
    try {
      setItems(await api.get<Webhook[]>(`/v1/webhooks?tenant_id=${tenantId}`))
      setError(null)
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Could not load notification URLs')
    }
  }, [tenantId])


  useEffect(() => {
    void Promise.resolve().then(load)
  }, [load])

  async function onCreate(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    setMsg(null)
    setSecretOnce(null)
    setSecretAck(false)
    try {
      const res = await api.post<{ id: string; secret?: string }>('/v1/webhooks', {
        tenant_id: tenantId,
        url,
      })
      if (res.secret) setSecretOnce(res.secret)
      setUrl('')
      setShowForm(false)
      setMsg('Notification URL saved. NetPay will POST payment updates here.')
      await load()
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.detail
          : 'Could not save (use HTTPS and ensure the URL responds)',
      )
    } finally {
      setBusy(false)
    }
  }

  async function onDelete(id: string) {
    setDeleteTarget(null)
    setBusy(true)
    try {
      await api.delete(`/v1/webhooks/${id}`)
      setMsg('Notification URL removed.')
      await load()
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Could not remove URL')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <PageHeader
        title="After payment"
        description={`Where should we notify when a payment for ${activeBusiness?.name || "this business"} succeeds or fails? Add HTTPS endpoints your system owns.`}
        actions={
          <Button
            leftIcon={<Plus size={16} />}
            disabled={!tenantId}
            onClick={() => {
              setError(null)
              setShowForm(true)
            }}
          >
            Add URL
          </Button>
        }
      />

      {error && (
        <DismissibleBanner tone="error" onDismiss={() => setError(null)}>
          {error}
        </DismissibleBanner>
      )}
      {msg && (
        <div className="mb-4 rounded-xl border border-[var(--accent)]/25 bg-[var(--accent-soft)] px-4 py-3 text-sm">
          {msg}
        </div>
      )}
      {secretOnce && (
        <div className="mb-4 rounded-xl border border-[var(--warn)]/30 bg-[var(--warn-soft)] px-4 py-3 text-sm">
          <p className="m-0 font-semibold">Copy this signing secret now — it is shown only once.</p>
          <code className={`${mono} mt-2 block break-all`}>{secretOnce}</code>
          <label className="mt-3 flex items-center gap-2 text-xs">
            <input type="checkbox" checked={secretAck} onChange={(e) => setSecretAck(e.target.checked)} />
            I have saved this secret
          </label>
          {secretAck && (
            <Button size="sm" className="mt-2" variant="secondary" onClick={() => setSecretOnce(null)}>
              Dismiss
            </Button>
          )}
        </div>
      )}

      {!tenantId ? (
        <EmptyState
          icon={<Bell size={22} />}
          title="No business selected"
          hint="Pick a business in the sidebar, then add payment alert URLs."
        />
      ) : items.length === 0 ? (
        <EmptyState
          icon={<Bell size={22} />}
          title="No notification URLs yet"
          hint="Add an HTTPS endpoint on your app. We verify it responds before saving."
          action={
            <Button leftIcon={<Plus size={16} />} onClick={() => setShowForm(true)}>
              Add URL
            </Button>
          }
        />
      ) : (
        <div className={tableWrap}>
          <table className={table}>
            <thead>
              <tr>
                <th>URL</th>
                <th>Last checked</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items.map((w) => (
                <tr key={w.id}>
                  <td className={`${mono} max-w-64 break-all`}>{w.url}</td>
                  <td className="text-xs text-[var(--muted)]">
                    {w.last_live_at ? new Date(w.last_live_at).toLocaleString() : '—'}
                  </td>
                  <td>
                    <Button size="sm" variant="danger" disabled={busy} onClick={() => setDeleteTarget(w.id)}>
                      Remove
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <p className="mt-4 text-xs text-[var(--muted)]">
        Still setting up collection?{' '}
        <Link to="/integrations">Shortcodes</Link> must be connected before live payments flow.
      </p>

      <Modal
        open={showForm}
        title="Add notification URL"
        onClose={() => !busy && setShowForm(false)}
        footer={
          <>
            <Button variant="secondary" disabled={busy} onClick={() => setShowForm(false)}>
              Cancel
            </Button>
            <Button form="np-webhook-form" type="submit" loading={busy} disabled={!tenantId}>
              {busy ? 'Checking…' : 'Save URL'}
            </Button>
          </>
        }
      >
        <form id="np-webhook-form" className="flex flex-col gap-3" onSubmit={(e) => void onCreate(e)}>
          <Input
            label="HTTPS address"
            type="url"
            required
            pattern="https://.*"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://your-app.com/hooks/payments"
            hint="Must be HTTPS and reachable from the internet."
          />
        </form>
      </Modal>

      <ConfirmModal
        open={!!deleteTarget}
        title="Remove notification URL?"
        body="Your app will no longer receive automatic payment updates at this address."
        confirmLabel="Remove"
        danger
        busy={busy}
        onCancel={() => !busy && setDeleteTarget(null)}
        onConfirm={() => deleteTarget && void onDelete(deleteTarget)}
      />
    </div>
  )
}
