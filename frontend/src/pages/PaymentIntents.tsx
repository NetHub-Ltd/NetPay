import { type FormEvent, useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { CreditCard, Plus } from 'lucide-react'
import { subscribeLiveMessages } from '../hooks/liveEvents'
import { api, ApiError, type Integration, type PaymentIntent } from '../api/client'
import { DataTable } from '../components/DataTable'
import { EmptyState } from '../components/EmptyState'
import { PageHeader } from '../components/PageHeader'
import { StatusBadge } from '../components/StatusBadge'
import { formatKes, paymentLifecycleBucket, statusHint } from '../components/statusUtils'
import { Button, Input, Modal } from '../components/primitives'
import { mono } from '../components/ui'

export function PaymentIntents() {
  const navigate = useNavigate()
  const [items, setItems] = useState<PaymentIntent[]>([])
  const [integrations, setIntegrations] = useState<Integration[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [busy, setBusy] = useState(false)
  const [lastCreatedId, setLastCreatedId] = useState<string | null>(null)
  const [form, setForm] = useState({
    integration_public_id: '',
    phone: '',
    amount: '1',
    account_reference: 'PAY',
    description: 'Payment',
  })
  const [showAdvanced, setShowAdvanced] = useState(false)

  const load = useCallback(async () => {
    try {
      const [payments, integ] = await Promise.all([
        api.get<PaymentIntent[]>('/v1/payment-intents'),
        api.get<Integration[]>('/v1/integrations'),
      ])
      setItems(payments)
      setIntegrations(integ)
      setForm((f) =>
        !f.integration_public_id && integ[0]?.public_id
          ? { ...f, integration_public_id: integ[0].public_id }
          : f,
      )
      setError(null)
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Could not load payments')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void Promise.resolve().then(load)
  }, [load])

  useEffect(() => {
    return subscribeLiveMessages((m) => {
      if (m.type === 'payment.update' || m.type === 'notification') void load()
    })
  }, [load])

  async function onCreate(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    setSuccess(null)
    try {
      const amountMajor = Number(form.amount)
      if (!amountMajor || amountMajor < 1) {
        setError('Enter an amount of at least 1 KES')
        return
      }
      if (!form.integration_public_id) {
        setError('Choose which shortcode should receive this payment')
        return
      }
      if (!form.phone.trim()) {
        setError('Enter the customer’s phone number')
        return
      }
      const amount_minor = Math.round(amountMajor * 100)
      const idempotencyKey =
        typeof crypto !== 'undefined' && 'randomUUID' in crypto
          ? crypto.randomUUID()
          : `pay-${Date.now()}`
      const created = await api.post<PaymentIntent>(
        '/v1/payment-intents',
        {
          integration_public_id: form.integration_public_id,
          phone: form.phone.trim(),
          amount_minor,
          account_reference: form.account_reference || 'PAY',
          description: form.description || 'Payment',
        },
        {
          headers: {
            'Content-Type': 'application/json',
            'Idempotency-Key': idempotencyKey,
          },
        },
      )
      setShowForm(false)
      setLastCreatedId(created.id)
      setSuccess('Payment prompt sent. Watch the list for the result.')
      setForm((f) => ({ ...f, phone: '', amount: '1' }))
      await load()
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Could not send payment prompt')
    } finally {
      setBusy(false)
    }
  }

  const noShortcodes = !loading && integrations.length === 0
  const noPayments = !loading && items.length === 0

  return (
    <div>
      <PageHeader
        title="Payments"
        description="Send a phone prompt and follow each payment until it settles or fails."
        actions={
          <Button
            leftIcon={<Plus size={16} aria-hidden />}
            disabled={noShortcodes}
            onClick={() => {
              setError(null)
              setSuccess(null)
              setShowForm(true)
            }}
            title={noShortcodes ? 'Add a shortcode first' : undefined}
          >
            Take a payment
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
      {success && (
        <div className="mb-4 rounded-xl border border-[var(--accent)]/25 bg-[var(--accent-soft)] px-4 py-3 text-sm text-[var(--text)]">
          {success}
          {lastCreatedId && (
            <>
              {' '}
              <Link className="font-semibold" to={`/intents/${lastCreatedId}`}>
                Open payment
              </Link>
            </>
          )}
        </div>
      )}

      {noShortcodes ? (
        <EmptyState
          icon={<CreditCard size={22} aria-hidden />}
          title="Add a shortcode before taking payments"
          hint="NetPay needs a paybill or till so Safaricom knows where the money should land."
          action={
            <Link to="/integrations" className="no-underline">
              <Button>Add shortcode</Button>
            </Link>
          }
        />
      ) : noPayments ? (
        <EmptyState
          icon={<CreditCard size={22} aria-hidden />}
          title="No payments yet"
          hint="Send a prompt to a customer’s phone. You’ll see Paid, Waiting, or Failed here as soon as there’s news."
          action={
            <Button leftIcon={<Plus size={16} />} onClick={() => setShowForm(true)}>
              Take a payment
            </Button>
          }
        />
      ) : (
        <DataTable
          rows={items}
          getRowId={(p) => p.id}
          searchPlaceholder="Search phone, amount…"
          defaultPageSize={10}
          maxHeight="min(440px, 55vh)"
          emptyTitle="No matching payments"
          emptyHint="Try clearing filters or search."
          filters={[
            { id: 'processing', label: 'Processing' },
            { id: 'successful', label: 'Successful' },
            { id: 'failed', label: 'Failed' },
          ]}
          filterFn={(p, id) => paymentLifecycleBucket(p.status) === id}
          onRowClick={(p) => navigate(`/intents/${p.id}`)}
          columns={[
            {
              id: 'status',
              header: 'Status',
              searchValue: (p) => `${p.status} ${p.failure_reason || ''}`,
              cell: (p) => (
                <>
                  <StatusBadge value={p.status} />
                  {p.failure_reason && (
                    <div className="max-w-[220px] text-xs text-[var(--muted)]">
                      {p.failure_reason}
                    </div>
                  )}
                  {!p.failure_reason && p.status === 'provider_requested' && (
                    <div className="text-xs text-[var(--muted)]">{statusHint(p.status)}</div>
                  )}
                </>
              ),
            },
            {
              id: 'amount',
              header: 'Amount',
              searchValue: (p) => formatKes(p.amount_minor, p.amount, p.currency),
              cell: (p) => formatKes(p.amount_minor, p.amount, p.currency),
            },
            {
              id: 'phone',
              header: 'Phone',
              searchValue: (p) => p.phone || '',
              cell: (p) => <span className={mono}>{p.phone}</span>,
            },
            {
              id: 'when',
              header: 'When',
              searchValue: (p) => p.created_at || '',
              cell: (p) => (
                <span className="text-[var(--muted)]">
                  {p.created_at ? new Date(p.created_at).toLocaleString() : '—'}
                </span>
              ),
            },
            {
              id: 'open',
              header: '',
              cell: (p) => (
                <Link to={`/intents/${p.id}`} onClick={(e) => e.stopPropagation()}>
                  Open
                </Link>
              ),
            },
          ]}
        />
      )}

      <Modal
        open={showForm}
        title="Take a payment"
        onClose={() => !busy && setShowForm(false)}
        footer={
          <>
            <Button variant="secondary" disabled={busy} onClick={() => setShowForm(false)}>
              Cancel
            </Button>
            <Button form="np-take-payment" type="submit" loading={busy}>
              {busy ? 'Sending…' : 'Send phone prompt'}
            </Button>
          </>
        }
      >
        <form id="np-take-payment" className="flex flex-col gap-3" onSubmit={(e) => void onCreate(e)}>
          <label className="flex flex-col gap-1.5 text-sm">
            <span className="font-medium">Shortcode</span>
            <select
              className="w-full rounded-xl border border-[var(--border)] bg-[var(--panel)] px-3.5 py-2.5 text-sm shadow-[var(--shadow-sm)] focus:border-[var(--accent)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/25"
              value={form.integration_public_id}
              onChange={(e) => setForm({ ...form, integration_public_id: e.target.value })}
              required
            >
              {integrations.map((i) => (
                <option key={i.id} value={i.public_id}>
                  {i.shortcode} ({i.type})
                </option>
              ))}
            </select>
          </label>
          <Input
            label="Customer phone"
            placeholder="2547…"
            value={form.phone}
            onChange={(e) => setForm({ ...form, phone: e.target.value })}
            required
            autoComplete="tel"
          />
          <Input
            label="Amount (KES)"
            type="number"
            min={1}
            step="1"
            value={form.amount}
            onChange={(e) => setForm({ ...form, amount: e.target.value })}
            required
          />
          <button
            type="button"
            className="self-start text-xs font-medium text-[var(--accent)]"
            onClick={() => setShowAdvanced((v) => !v)}
          >
            {showAdvanced ? 'Hide optional details' : 'Optional details'}
          </button>
          {showAdvanced && (
            <>
              <Input
                label="Reference"
                value={form.account_reference}
                onChange={(e) => setForm({ ...form, account_reference: e.target.value })}
              />
              <Input
                label="Description"
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
              />
            </>
          )}
        </form>
      </Modal>
    </div>
  )
}
