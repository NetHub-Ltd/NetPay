import { type FormEvent, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useWorkspace } from '../workspace/useWorkspace'
import { api, ApiError, type Integration } from '../api/client'
import { PageHeader } from '../components/PageHeader'
import { Button, Input } from '../components/primitives'

const selectClass =
  'w-full rounded-xl border border-[var(--border)] bg-[var(--panel)] px-3.5 py-2.5 text-sm shadow-[var(--shadow-sm)] focus:border-[var(--accent)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/25'

const fieldGrid = 'grid gap-4 sm:grid-cols-2'

export function IntegrationCreate() {
  const navigate = useNavigate()
  const { activeTenantId, activeBusiness } = useWorkspace()
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [form, setForm] = useState({
    shortcode: '',
    type: 'paybill',
    environment: 'sandbox',
    consumer_key: '',
    consumer_secret: '',
    passkey: '',
  })

  const bizName = activeBusiness?.name || 'this business'
  const backTo = '/integrations'

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    if (!activeTenantId) {
      setError('No active business — pick one in the sidebar.')
      setBusy(false)
      return
    }
    try {
      const created = await api.post<Integration>('/v1/integrations', {
        ...form,
        tenant_id: activeTenantId,
      })
      navigate(created?.id ? `/integrations/${created.id}` : '/integrations', { replace: true })
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Could not save shortcode')
      setBusy(false)
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6" data-testid="integration-create-page">
      <p className="mb-0 text-sm text-[var(--muted)]">
        <Link to={backTo}>← Back</Link>
      </p>

      <PageHeader
        title="Add shortcode"
        description={`Paybill or till for ${bizName}. Keys are verified with the network before saving.`}
      />

      {error && (
        <div
          className="rounded-xl border border-[var(--danger)]/25 bg-[var(--danger-soft)] px-4 py-3 text-sm text-[var(--danger)]"
          role="alert"
        >
          {error}
        </div>
      )}

      {!activeTenantId ? (
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--panel)] p-6 shadow-[var(--shadow-sm)]">
          <p className="m-0 text-sm text-[var(--muted)]">Select a business in the sidebar first.</p>
        </div>
      ) : (
        <form
          className="space-y-5 rounded-2xl border border-[var(--border)] bg-[var(--panel)] p-5 shadow-[var(--shadow-sm)] sm:p-6"
          onSubmit={(e) => void onSubmit(e)}
        >
          <div className="rounded-xl border border-[var(--border)] bg-[var(--panel-2)] px-3.5 py-3 text-sm">
            <div className="text-xs font-medium text-[var(--muted)]">Business</div>
            <div className="mt-0.5 font-semibold text-[var(--text)]">{bizName}</div>
            <p className="mb-0 mt-1 text-xs text-[var(--muted)]">
              Switch business from the sidebar if this is the wrong one.
            </p>
          </div>

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
            <span className="text-xs text-[var(--muted)]">Use sandbox keys with Test, live keys with Live.</span>
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
