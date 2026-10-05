import { type FormEvent, useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { api, ApiError, type Integration, type Tenant } from '../api/client'
import { PageHeader } from '../components/PageHeader'
import { Button, Input } from '../components/primitives'

const selectClass =
  'w-full rounded-xl border border-[var(--border)] bg-[var(--panel)] px-3.5 py-2.5 text-sm shadow-[var(--shadow-sm)] focus:border-[var(--accent)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/25'

const fieldGrid = 'grid gap-4 sm:grid-cols-2'

export function IntegrationCreate() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const presetTenant = params.get('tenant_id') || ''

  const [businesses, setBusinesses] = useState<Tenant[]>([])
  const [error, setError] = useState<string | null>(null)
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

  const activeBusinesses = useMemo(
    () => businesses.filter((b) => b.status === 'active'),
    [businesses],
  )

  const load = useCallback(async () => {
    try {
      const tenants = await api.get<Tenant[]>('/v1/tenants')
      setBusinesses(tenants)
      setForm((f) => ({
        ...f,
        tenant_id:
          f.tenant_id ||
          presetTenant ||
          tenants.find((t) => t.status === 'active')?.id ||
          '',
      }))
      setError(null)
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Could not load businesses')
    }
  }, [presetTenant])

  useEffect(() => {
    void Promise.resolve().then(load)
  }, [load])

  const selectedName = businesses.find((b) => b.id === form.tenant_id)?.name

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    if (!form.tenant_id) {
      setError('Choose a business for this shortcode.')
      setBusy(false)
      return
    }
    try {
      const created = await api.post<Integration>('/v1/integrations', { ...form })
      navigate(created?.id ? `/integrations/${created.id}` : '/integrations', {
        replace: true,
      })
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Could not save shortcode')
      setBusy(false)
    }
  }

  const backTo = presetTenant
    ? `/tenants/${presetTenant}`
    : form.tenant_id
      ? `/integrations?tenant_id=${form.tenant_id}`
      : '/integrations'

  return (
    <div className="mx-auto max-w-2xl space-y-6" data-testid="integration-create-page">
      <p className="mb-0 text-sm text-[var(--muted)]">
        <Link to={backTo}>← Back</Link>
      </p>

      <PageHeader
        title="Add shortcode"
        description={
          selectedName
            ? `Paybill or till for ${selectedName}. Keys are verified with Safaricom before saving.`
            : 'Choose a business, then enter Daraja credentials. Keys are verified before saving.'
        }
      />

      {error && (
        <div
          className="rounded-xl border border-[var(--danger)]/25 bg-[var(--danger-soft)] px-4 py-3 text-sm text-[var(--danger)]"
          role="alert"
        >
          {error}
        </div>
      )}

      {activeBusinesses.length === 0 ? (
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--panel)] p-6 shadow-[var(--shadow-sm)]">
          <p className="m-0 text-sm text-[var(--muted)]">
            You need an active business before adding a shortcode.
          </p>
          <Link to="/tenants" className="mt-4 inline-block no-underline">
            <Button>Go to businesses</Button>
          </Link>
        </div>
      ) : (
        <form
          className="space-y-5 rounded-2xl border border-[var(--border)] bg-[var(--panel)] p-5 shadow-[var(--shadow-sm)] sm:p-6"
          onSubmit={(e) => void onSubmit(e)}
        >
          <label className="flex flex-col gap-1.5 text-sm">
            <span className="font-medium">Business</span>
            <select
              className={selectClass}
              required
              value={form.tenant_id}
              onChange={(e) => setForm({ ...form, tenant_id: e.target.value })}
              disabled={Boolean(presetTenant)}
            >
              <option value="">Select…</option>
              {activeBusinesses.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name}
                </option>
              ))}
            </select>
            {presetTenant && (
              <span className="text-xs text-[var(--muted)]">
                Pinned from the business you opened.
              </span>
            )}
          </label>

          <div className={fieldGrid}>
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
                className={selectClass}
                value={form.type}
                onChange={(e) => setForm({ ...form, type: e.target.value })}
              >
                <option value="paybill">Paybill</option>
                <option value="till">Till number</option>
              </select>
            </label>
          </div>

          <label className="flex flex-col gap-1.5 text-sm">
            <span className="font-medium">Environment</span>
            <select
              className={selectClass}
              value={form.environment}
              onChange={(e) => setForm({ ...form, environment: e.target.value })}
            >
              <option value="sandbox">Test (sandbox)</option>
              <option value="production">Live</option>
            </select>
            <span className="text-xs text-[var(--muted)]">
              Use sandbox keys with Test, live keys with Live.
            </span>
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

          <div className="flex flex-wrap gap-3 border-t border-[var(--border)] pt-5">
            <Button type="submit" loading={busy}>
              {busy ? 'Verifying & saving…' : 'Save shortcode'}
            </Button>
            <Link to={backTo} className="no-underline">
              <Button type="button" variant="secondary" disabled={busy}>
                Cancel
              </Button>
            </Link>
          </div>
        </form>
      )}
    </div>
  )
}
