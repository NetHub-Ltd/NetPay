import { type FormEvent, useCallback, useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { Landmark, Plus } from 'lucide-react'
import { api, ApiError, type Integration, type Tenant, type Webhook } from '../api/client'
import { EmptyState } from '../components/EmptyState'
import { PageHeader } from '../components/PageHeader'
import { StatusBadge } from '../components/StatusBadge'
import { useAuth } from '../auth/authState'
import { Button, Input, Modal } from '../components/primitives'
import { mono, table, tableWrap } from '../components/ui'

export function Integrations() {
  const { isAdmin, user } = useAuth()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const presetTenant = params.get('tenant_id') || user?.tenant_id || ''
  const [items, setItems] = useState<Integration[]>([])
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [webhookCount, setWebhookCount] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [msg, setMsg] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [busy, setBusy] = useState(false)
  const [form, setForm] = useState({
    tenant_id: presetTenant,
    shortcode: '',
    type: 'paybill',
    environment: 'sandbox',
    consumer_key: '',
    consumer_secret: '',
    passkey: '',
  })

  const load = useCallback(async () => {
    try {
      const integ = await api.get<Integration[]>('/v1/integrations')
      setItems(integ)
      if (isAdmin) {
        try {
          setTenants(await api.get<Tenant[]>('/v1/tenants'))
        } catch {
          /* ignore */
        }
      }
      const tid = user?.tenant_id || form.tenant_id
      if (tid) {
        try {
          const hooks = await api.get<Webhook[]>(`/v1/webhooks?tenant_id=${tid}`)
          setWebhookCount(hooks.length)
        } catch {
          setWebhookCount(0)
        }
      }
      setError(null)
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Could not load shortcodes')
    }
  }, [form.tenant_id, isAdmin, user])

  useEffect(() => {
    void Promise.resolve().then(load)
  }, [load])

  async function onCreate(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    setMsg(null)
    const tenant_id = isAdmin ? form.tenant_id : user?.tenant_id || ''
    if (!tenant_id) {
      setError(
        isAdmin
          ? 'Choose a business before saving.'
          : "Your account isn't linked to a business. Ask an admin to link you, then try again.",
      )
      setBusy(false)
      return
    }
    try {
      const created = await api.post<Integration>('/v1/integrations', { ...form, tenant_id })
      setShowForm(false)
      setMsg('Shortcode saved. Next: open it and connect M-Pesa so results reach NetPay.')
      setForm((f) => ({
        ...f,
        shortcode: '',
        consumer_key: '',
        consumer_secret: '',
        passkey: '',
      }))
      await load()
      if (created?.id) navigate(`/integrations/${created.id}`)
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Could not save shortcode')
    } finally {
      setBusy(false)
    }
  }

  async function onRetire(id: string, shortcode: string) {
    const confirmed = window.confirm(
      `Retire shortcode ${shortcode}? It will stop accepting new payments. You can add it again later if needed.`,
    )
    if (!confirmed) return
    setBusy(true)
    setError(null)
    try {
      await api.delete(`/v1/integrations/${id}`)
      setMsg(`Shortcode ${shortcode} was retired.`)
      await load()
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Could not retire this shortcode')
    } finally {
      setBusy(false)
    }
  }

  const canAdd = isAdmin ? Boolean(form.tenant_id || tenants.length) : Boolean(user?.tenant_id)

  return (
    <div>
      <PageHeader
        title="Shortcodes"
        description="Paybills and tills that collect money into your business."
        actions={
          <Button
            leftIcon={<Plus size={16} aria-hidden />}
            onClick={() => {
              setError(null)
              setShowForm(true)
            }}
          >
            Add shortcode
          </Button>
        }
      />

      <div className="mb-5 rounded-2xl border border-[var(--border)] bg-[var(--panel)] p-4 shadow-[var(--shadow-sm)]">
        <p className="m-0 mb-2 text-xs font-bold uppercase tracking-wider text-[var(--muted)]">
          Setup path
        </p>
        <ol className="m-0 list-decimal space-y-1.5 pl-5 text-sm text-[var(--text)]">
          <li>
            <strong>Add a shortcode</strong>
            {items.length > 0 ? ' — done' : ' — start here'}
          </li>
          <li>
            <strong>Connect M-Pesa</strong>
            {items.length > 0 ? (
              <>
                {' '}
                —{' '}
                <Link to={`/integrations/${items[0].id}`}>continue setup</Link>
              </>
            ) : (
              ' — after the shortcode is saved'
            )}
          </li>
          <li>
            <strong>Notify your app</strong> —{' '}
            <Link to="/webhooks">notification endpoints</Link>
            {webhookCount > 0 ? ' — at least one saved' : ' — add an HTTPS URL when ready'}
          </li>
        </ol>
      </div>

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
          icon={<Landmark size={22} aria-hidden />}
          title="No shortcodes yet"
          hint="Add a paybill or till from Safaricom. Then connect it so payment results arrive in NetPay."
          action={
            <Button leftIcon={<Plus size={16} />} onClick={() => setShowForm(true)}>
              Add shortcode
            </Button>
          }
        />
      ) : (
        <div className={tableWrap}>
          <table className={table}>
            <thead>
              <tr>
                <th>Shortcode</th>
                <th>Type</th>
                <th>Environment</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items.map((i) => (
                <tr key={i.id}>
                  <td>
                    <strong>{i.shortcode}</strong>
                    <div className={`${mono} text-xs text-[var(--muted)]`}>{i.public_id}</div>
                  </td>
                  <td>{i.type === 'till' ? 'Till' : 'Paybill'}</td>
                  <td>{i.environment === 'production' ? 'Live' : 'Test'}</td>
                  <td>
                    <StatusBadge value={i.status} />
                  </td>
                  <td>
                    <div className="flex flex-wrap justify-end gap-2">
                      <Link to={`/integrations/${i.id}`}>
                        <Button size="sm" variant="primary">
                          Continue setup
                        </Button>
                      </Link>
                      <Button
                        size="sm"
                        variant="secondary"
                        disabled={busy}
                        onClick={() => void onRetire(i.id, i.shortcode)}
                      >
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

      <Modal
        open={showForm}
        title="Add a shortcode"
        onClose={() => !busy && setShowForm(false)}
        footer={
          <>
            <Button variant="secondary" disabled={busy} onClick={() => setShowForm(false)}>
              Cancel
            </Button>
            <Button
              form="np-add-shortcode"
              type="submit"
              loading={busy}
              disabled={!canAdd && !isAdmin}
            >
              {busy ? 'Saving…' : 'Save shortcode'}
            </Button>
          </>
        }
      >
        <p className="mb-4 mt-0 text-xs leading-5 text-[var(--muted)]">
          Use the shortcode and API keys from the Safaricom Daraja portal (test or live).
        </p>
        <form
          id="np-add-shortcode"
          className="flex flex-col gap-3"
          onSubmit={(e) => void onCreate(e)}
        >
          {isAdmin && (
            <label className="flex flex-col gap-1.5 text-sm">
              <span className="font-medium">Business</span>
              <select
                className="w-full rounded-xl border border-[var(--border)] bg-[var(--panel)] px-3.5 py-2.5 text-sm"
                required
                value={form.tenant_id}
                onChange={(e) => setForm({ ...form, tenant_id: e.target.value })}
              >
                <option value="">Select…</option>
                {tenants.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </select>
            </label>
          )}
          {!isAdmin && !user?.tenant_id && (
            <div className="rounded-xl border border-[var(--danger)]/25 bg-[var(--danger-soft)] px-4 py-3 text-sm text-[var(--danger)]">
              Your account isn&apos;t linked to a business. Ask an admin to link you before adding a
              shortcode.
            </div>
          )}
          <Input
            label="Shortcode"
            required
            value={form.shortcode}
            onChange={(e) => setForm({ ...form, shortcode: e.target.value })}
            placeholder="e.g. 174379"
          />
          <label className="flex flex-col gap-1.5 text-sm">
            <span className="font-medium">Type</span>
            <select
              className="w-full rounded-xl border border-[var(--border)] bg-[var(--panel)] px-3.5 py-2.5 text-sm"
              value={form.type}
              onChange={(e) => setForm({ ...form, type: e.target.value })}
            >
              <option value="paybill">Paybill</option>
              <option value="till">Till number</option>
            </select>
          </label>
          <label className="flex flex-col gap-1.5 text-sm">
            <span className="font-medium">Environment</span>
            <select
              className="w-full rounded-xl border border-[var(--border)] bg-[var(--panel)] px-3.5 py-2.5 text-sm"
              value={form.environment}
              onChange={(e) => setForm({ ...form, environment: e.target.value })}
            >
              <option value="sandbox">Test (sandbox)</option>
              <option value="production">Live</option>
            </select>
          </label>
          <Input
            label="Consumer key"
            required
            value={form.consumer_key}
            onChange={(e) => setForm({ ...form, consumer_key: e.target.value })}
            autoComplete="off"
          />
          <Input
            label="Consumer secret"
            required
            type="password"
            value={form.consumer_secret}
            onChange={(e) => setForm({ ...form, consumer_secret: e.target.value })}
            autoComplete="off"
          />
          <Input
            label="Passkey (Lipa Na M-Pesa)"
            required
            type="password"
            value={form.passkey}
            onChange={(e) => setForm({ ...form, passkey: e.target.value })}
            autoComplete="off"
          />
        </form>
      </Modal>
    </div>
  )
}
