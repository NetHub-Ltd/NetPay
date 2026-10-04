import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  ArrowRight,
  ArrowUpRight,
  Bell,
  Check,
  CircleAlert,
  Clock3,
  CreditCard,
  Landmark,
  Plus,
  Sparkles,
} from 'lucide-react'
import { api, ApiError, type Integration, type PaymentIntent, type Webhook } from '../api/client'
import { useAuth } from '../auth/authState'
import { DataTable } from '../components/DataTable'
import { StatusBadge } from '../components/StatusBadge'
import { formatKes } from '../components/statusUtils'
import { subscribeLiveMessages } from '../hooks/liveEvents'

function greetingName(user: {
  display_name?: string | null
  full_name?: string | null
  email?: string
} | null) {
  if (!user) return null
  const name = (user.full_name || user.display_name || '').trim()
  if (name) return name.split(/\s+/)[0]
  return user.email?.split('@')[0] || null
}

function greeting() {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 17) return 'Good afternoon'
  return 'Good evening'
}

export function Home() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [payments, setPayments] = useState<PaymentIntent[]>([])
  const [integrations, setIntegrations] = useState<Integration[]>([])
  const [webhookCount, setWebhookCount] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async (quiet = false) => {
    if (!quiet) setLoading(true)
    try {
      const [paymentRows, integrationRows] = await Promise.all([
        api.get<PaymentIntent[]>('/v1/payment-intents'),
        api.get<Integration[]>('/v1/integrations'),
      ])
      setPayments(paymentRows || [])
      setIntegrations(integrationRows || [])
      setError(null)

      if (user?.tenant_id) {
        try {
          const webhooks = await api.get<Webhook[]>(
            `/v1/webhooks?tenant_id=${user.tenant_id}`,
          )
          setWebhookCount(webhooks.length)
        } catch {
          setWebhookCount(0)
        }
      } else {
        setWebhookCount(0)
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Could not load dashboard')
    } finally {
      setLoading(false)
    }
  }, [user])

  useEffect(() => {
    void Promise.resolve().then(() => load())
  }, [load])

  useEffect(
    () =>
      subscribeLiveMessages((message) => {
        if (message.type === 'payment.update' || message.type === 'notification') {
          void load(true)
        }
      }),
    [load],
  )

  const firstName = greetingName(user)
  const waitingCount = payments.filter(
    (payment) => payment.status === 'provider_requested' || payment.status === 'created',
  ).length
  const setupSteps = [
    {
      title: 'Connect a shortcode',
      detail: 'Choose where customers will pay you.',
      complete: integrations.length > 0,
      to: '/integrations',
      icon: Landmark,
    },
    {
      title: 'Add an app endpoint',
      detail: 'Receive payment updates in your system.',
      complete: webhookCount > 0,
      to: '/webhooks',
      icon: Bell,
    },
    {
      title: 'Send your first payment',
      detail: 'Try a phone prompt and follow its status.',
      complete: payments.length > 0,
      to: '/intents',
      icon: CreditCard,
    },
  ]

  return (
    <div className="space-y-6" data-testid="home-page">
      <section className="relative isolate overflow-hidden rounded-3xl bg-gradient-to-br from-[var(--accent)] via-[var(--accent-hover)] to-[#073d2d] px-6 py-7 text-white shadow-[var(--shadow)] sm:px-8 sm:py-9">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -right-20 -top-28 -z-10 size-80 rounded-full border border-white/10"
        />
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -right-8 -top-16 -z-10 size-56 rounded-full border border-white/10"
        />
        <div className="relative flex flex-col justify-between gap-7 lg:flex-row lg:items-end">
          <div className="max-w-2xl">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-medium text-white/90">
              <Sparkles size={14} aria-hidden="true" />
              Your collections, in one place
            </div>
            <h1 className="m-0 text-3xl font-semibold tracking-tight sm:text-4xl">
              {greeting()}{firstName ? `, ${firstName}` : ''}.
            </h1>
            <p className="mb-0 mt-3 max-w-xl text-sm leading-6 text-white/75 sm:text-base">
              See what has come in, what is still moving, and what needs your attention.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-[var(--accent-hover)] shadow-sm transition hover:bg-white/90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
              to="/intents"
            >
              <Plus size={17} aria-hidden="true" />
              New payment
            </Link>
            <Link
              className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/25 bg-white/10 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-white/15 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
              to="/integrations"
            >
              Manage shortcodes
              <ArrowUpRight size={16} aria-hidden="true" />
            </Link>
          </div>
        </div>
      </section>

      {error && (
        <div
          className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-[var(--danger)]/30 bg-[var(--danger)]/10 px-4 py-3 text-sm text-[var(--danger)]"
          role="alert"
        >
          <span>{error}</span>
          <button
            className="font-semibold underline underline-offset-2"
            type="button"
            onClick={() => void load()}
          >
            Try again
          </button>
        </div>
      )}

      <section aria-label="Collection overview" className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <OverviewCard
          icon={CreditCard}
          label="Payments"
          value={loading ? '—' : String(payments.length)}
          detail="All payment activity"
          to="/intents"
          color="text-[var(--accent)] bg-[var(--accent-soft)]"
        />
        <OverviewCard
          icon={Clock3}
          label="In progress"
          value={loading ? '—' : String(waitingCount)}
          detail={waitingCount === 1 ? 'Waiting for a customer' : 'Waiting for customers'}
          to="/intents"
          color="text-[var(--warn)] bg-[var(--warn-soft)]"
        />
        <OverviewCard
          icon={Landmark}
          label="Shortcodes"
          value={loading ? '—' : String(integrations.length)}
          detail="Paybills and tills"
          to="/integrations"
          color="text-[var(--accent)] bg-[var(--accent-soft)]"
        />
        <OverviewCard
          icon={Bell}
          label="App endpoints"
          value={loading ? '—' : String(webhookCount)}
          detail="Payment notification URLs"
          to="/webhooks"
          color="text-[var(--accent)] bg-[var(--accent-soft)]"
        />
      </section>

      <div className="grid items-start gap-5 xl:grid-cols-[minmax(0,1.65fr)_minmax(18rem,0.85fr)]">
        <section className="min-w-0">
          <div className="mb-3 flex items-end justify-between gap-3">
            <div>
              <p className="mb-1 text-xs font-semibold uppercase tracking-[0.12em] text-[var(--accent)]">
                Activity
              </p>
              <h2 className="m-0 text-lg font-semibold tracking-tight">Recent payments</h2>
            </div>
            <Link
              className="inline-flex shrink-0 items-center gap-1 text-sm font-semibold text-[var(--accent)] hover:underline"
              to="/intents"
            >
              View all <ArrowRight size={15} aria-hidden="true" />
            </Link>
          </div>
          {loading ? (
            <div className="space-y-3 rounded-2xl border border-[var(--border)] bg-[var(--panel)] p-5 shadow-[var(--shadow-sm)]" aria-label="Loading payments">
              <div className="h-4 w-1/3 animate-pulse rounded bg-[var(--panel-2)]" />
              <div className="h-10 animate-pulse rounded bg-[var(--panel-2)]" />
              <div className="h-10 animate-pulse rounded bg-[var(--panel-2)]" />
              <div className="h-10 animate-pulse rounded bg-[var(--panel-2)]" />
            </div>
          ) : (
            <DataTable
              rows={payments.slice(0, 5)}
              getRowId={(payment) => payment.id}
              searchPlaceholder="Search recent payments…"
              defaultPageSize={5}
              pageSizeOptions={[5]}
              maxHeight="360px"
              emptyTitle="Your payment activity will appear here"
              emptyHint="Start with a test payment, then follow its progress from request to result."
              onRowClick={(payment) => navigate(`/intents/${payment.id}`)}
              columns={[
                {
                  id: 'amount',
                  header: 'Amount',
                  searchValue: (payment) =>
                    formatKes(payment.amount_minor, payment.amount, payment.currency),
                  cell: (payment) => (
                    <span className="font-mono text-sm font-medium">
                      {formatKes(payment.amount_minor, payment.amount, payment.currency)}
                    </span>
                  ),
                },
                {
                  id: 'phone',
                  header: 'Customer',
                  searchValue: (payment) => payment.phone || '',
                  cell: (payment) => <span className="font-mono text-xs">{payment.phone}</span>,
                },
                {
                  id: 'status',
                  header: 'Status',
                  searchValue: (payment) =>
                    `${payment.status} ${payment.failure_reason || ''}`,
                  cell: (payment) => <StatusBadge value={payment.status} />,
                },
                {
                  id: 'when',
                  header: 'Date',
                  searchValue: (payment) => payment.created_at || '',
                  cell: (payment) => (
                    <span className="text-xs text-[var(--muted)]">
                      {payment.created_at
                        ? new Date(payment.created_at).toLocaleString()
                        : '—'}
                    </span>
                  ),
                },
              ]}
            />
          )}
        </section>

        <aside className="space-y-5">
          <section className="rounded-2xl border border-[var(--border)] bg-[var(--panel)] p-5 shadow-[var(--shadow-sm)]">
            <div className="mb-4 flex items-start gap-3">
              <span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-[var(--accent-soft)] text-[var(--accent)]">
                <Sparkles size={18} aria-hidden="true" />
              </span>
              <div>
                <h2 className="m-0 text-base font-semibold">Getting started</h2>
                <p className="mb-0 mt-1 text-xs leading-5 text-[var(--muted)]">
                  A few essentials to get your collection flow ready.
                </p>
              </div>
            </div>
            <ol className="space-y-1">
              {setupSteps.map(({ title, detail, complete, to, icon: Icon }, index) => (
                <li key={title}>
                  <Link
                    className="group flex items-start gap-3 rounded-xl p-2.5 no-underline transition hover:bg-[var(--panel-2)]"
                    to={to}
                  >
                    <span
                      className={`mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-full ${
                        complete
                          ? 'bg-[var(--accent-soft)] text-[var(--accent)]'
                          : 'bg-[var(--panel-2)] text-[var(--muted)]'
                      }`}
                    >
                      {complete ? (
                        <Check size={15} aria-label="Complete" />
                      ) : (
                        <Icon size={14} aria-hidden="true" />
                      )}
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="flex items-center gap-2 text-sm font-medium text-[var(--text)]">
                        <span className="text-xs text-[var(--muted)]">{index + 1}.</span>
                        {title}
                      </span>
                      <span className="mt-0.5 block text-xs leading-5 text-[var(--muted)]">
                        {detail}
                      </span>
                    </span>
                    <ArrowRight
                      className="mt-1 shrink-0 text-[var(--muted)] transition group-hover:translate-x-0.5 group-hover:text-[var(--accent)]"
                      size={15}
                      aria-hidden="true"
                    />
                  </Link>
                </li>
              ))}
            </ol>
          </section>

          <section className="rounded-2xl border border-[var(--border)] bg-[var(--panel)] p-5 shadow-[var(--shadow-sm)]">
            <div className="flex items-start gap-3">
              <span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-[var(--warn-soft)] text-[var(--warn)]">
                {waitingCount > 0 ? (
                  <CircleAlert size={18} aria-hidden="true" />
                ) : (
                  <Check size={18} aria-hidden="true" />
                )}
              </span>
              <div className="min-w-0">
                <h2 className="m-0 text-base font-semibold">Needs your attention</h2>
                <p className="mb-3 mt-1 text-xs leading-5 text-[var(--muted)]">
                  {loading
                    ? 'Checking payment activity…'
                    : waitingCount > 0
                      ? `${waitingCount} ${waitingCount === 1 ? 'payment is' : 'payments are'} waiting for a customer response.`
                      : 'Nothing is waiting on a customer right now.'}
                </p>
                <Link
                  className="inline-flex items-center gap-1 text-sm font-semibold text-[var(--accent)] hover:underline"
                  to="/intents"
                >
                  Review payments <ArrowRight size={15} aria-hidden="true" />
                </Link>
              </div>
            </div>
          </section>
        </aside>
      </div>
    </div>
  )
}

function OverviewCard({
  icon: Icon,
  label,
  value,
  detail,
  to,
  color,
}: {
  icon: typeof CreditCard
  label: string
  value: string
  detail: string
  to: string
  color: string
}) {
  return (
    <Link
      className="group rounded-2xl border border-[var(--border)] bg-[var(--panel)] p-4 no-underline shadow-[var(--shadow-sm)] transition hover:-translate-y-0.5 hover:border-[var(--accent)]/40 hover:shadow-[var(--shadow)]"
      to={to}
    >
      <div className="flex items-start justify-between gap-3">
        <span className={`flex size-10 items-center justify-center rounded-xl ${color}`}>
          <Icon size={18} aria-hidden="true" />
        </span>
        <ArrowUpRight
          className="text-[var(--muted)] transition group-hover:text-[var(--accent)]"
          size={16}
          aria-hidden="true"
        />
      </div>
      <p className="mb-0 mt-4 text-sm font-medium text-[var(--muted)]">{label}</p>
      <p className="mb-0 mt-1 text-2xl font-semibold tracking-tight text-[var(--text)]">
        {value}
      </p>
      <p className="mb-0 mt-1 text-xs text-[var(--muted)]">{detail}</p>
    </Link>
  )
}
