import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowRight,
  ArrowUpRight,
  Check,
  CircleAlert,
  Clock3,
  CreditCard,
  Landmark,
  Plus,
  Sparkles,
} from 'lucide-react'
import {
  api,
  ApiError,
  type PaymentIntent,
  type Readiness,
} from '../api/client'
import { useAuth } from '../auth/authState'
import { useWorkspace } from '../workspace/useWorkspace'
import { paymentLifecycleBucket } from '../components/statusUtils'
import { subscribeLiveMessages } from '../hooks/liveEvents'
import { Button } from '../components/primitives'
import { DismissibleBanner } from '../components/DismissibleBanner'

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

const NEXT_COPY: Record<
  Readiness['next_step'],
  { title: string; detail: string; cta: string; to: string }
> = {
  create_business: {
    title: 'Create your business',
    detail: 'Free tier includes one business workspace.',
    cta: 'Create business',
    to: '/select-business',
  },
  add_shortcode: {
    title: 'Add a shortcode',
    detail: 'Paybill or till so customers know where to pay.',
    cta: 'Add shortcode',
    to: '/integrations/new',
  },
  connect_mpesa: {
    title: 'Connect M-Pesa',
    detail: 'So payment results reach NetPay automatically.',
    cta: 'Continue setup',
    to: '/integrations',
  },
  add_notification: {
    title: 'Set after-payment notifications',
    detail: 'Tell your system when a payment succeeds or fails.',
    cta: 'Add notification URL',
    to: '/webhooks',
  },
  connect_system: {
    title: 'Connect your system',
    detail: 'Create API credentials so your backend can start payments.',
    cta: 'Create API client',
    to: '/oauth-clients',
  },
  take_payment: {
    title: 'Take a payment',
    detail: 'You’re ready to collect — from the app or via your backend.',
    cta: 'Take a payment',
    to: '/intents',
  },
  done: {
    title: 'You’re set up',
    detail: 'Shortcode, notifications, and API access are in place. Collect anytime.',
    cta: 'Take a payment',
    to: '/intents',
  },
}

export function Home() {
  const { user, establishSession } = useAuth()
  const { activeTenantId, activeBusiness } = useWorkspace()
  const [readiness, setReadiness] = useState<Readiness | null>(null)
  const [payments, setPayments] = useState<PaymentIntent[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async (quiet = false) => {
    if (!quiet) setLoading(true)
    try {
      const [ready, paymentRows] = await Promise.all([
        api.get<Readiness>(
          activeTenantId ? `/v1/readiness?tenant_id=${activeTenantId}` : '/v1/readiness',
        ),
        api.get<PaymentIntent[]>(
          activeTenantId
            ? `/v1/payment-intents?tenant_id=${activeTenantId}`
            : '/v1/payment-intents',
        ),
      ])
      setReadiness(ready)
      setPayments(paymentRows || [])
      setError(null)
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Could not load overview')
    } finally {
      setLoading(false)
    }
  }, [activeTenantId])

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

  // Refresh session user when readiness gains a tenant (self-serve business)
  useEffect(() => {
    if (readiness?.tenant_id && !user?.tenant_id) {
      const token = sessionStorage.getItem('nethub_token')
      if (token) void establishSession(token).catch(() => {})
    }
  }, [readiness?.tenant_id, user?.tenant_id, establishSession])

  const firstName = greetingName(user)
  const step = readiness?.next_step || 'add_shortcode'
  const copy = NEXT_COPY[step]
  const connectTo =
    step === 'connect_mpesa' && readiness?.primary_integration_id
      ? `/integrations/${readiness.primary_integration_id}`
      : copy.to

  const paidCount = payments.filter((p) => paymentLifecycleBucket(p.status) === 'successful').length
  const waitingCount = payments.filter((p) => paymentLifecycleBucket(p.status) === 'processing').length
  const failedCount = payments.filter((p) => paymentLifecycleBucket(p.status) === 'failed').length

  const heroCta =
    step === 'create_business'
      ? { to: '/select-business', label: 'Create business', icon: Landmark }
      : step === 'add_shortcode'
        ? { to: '/integrations', label: 'Add shortcode', icon: Landmark }
        : step === 'connect_mpesa'
          ? { to: connectTo, label: 'Connect M-Pesa', icon: Landmark }
          : { to: '/intents', label: 'Take a payment', icon: Plus }

  const ready = readiness?.ready_to_collect === true

  return (
    <div className="space-y-6" data-testid="home-page">
      <section className="relative isolate overflow-hidden rounded-3xl bg-gradient-to-br from-[var(--hero-from)] via-[var(--hero-via)] to-[var(--hero-to)] px-6 py-7 text-[var(--on-hero)] shadow-[var(--shadow)] sm:px-8 sm:py-9">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -right-20 -top-28 -z-10 size-80 rounded-full border border-[var(--on-hero)]/10"
        />
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -right-8 -top-16 -z-10 size-56 rounded-full border border-[var(--on-hero)]/10"
        />
        <div className="relative flex flex-col justify-between gap-7 lg:flex-row lg:items-end">
          <div className="max-w-2xl">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-[var(--on-hero)]/20 bg-[var(--on-hero)]/10 px-3 py-1 text-xs font-medium text-[var(--on-hero)]/90">
              <Sparkles size={14} aria-hidden="true" />
              {ready ? 'Ready to collect' : 'Get ready to collect'}
            </div>
            <h1 className="m-0 text-3xl font-semibold tracking-tight sm:text-4xl">
              {greeting()}
              {firstName ? `, ${firstName}` : ''}.
            </h1>
            <p className="mb-0 mt-3 max-w-xl text-sm leading-6 text-[var(--on-hero-muted)] sm:text-base">
              {loading
                ? 'Checking your workspace…'
                : ready
                  ? 'See what needs attention and jump into the work that matters.'
                  : copy.detail}
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-[var(--on-hero)] px-4 py-2.5 text-sm font-semibold text-[var(--accent-hover)] no-underline shadow-sm transition hover:opacity-95"
              to={heroCta.to}
            >
              <heroCta.icon size={17} aria-hidden="true" />
              {heroCta.label}
            </Link>
            {readiness?.has_shortcode && (
              <Link
                className="inline-flex items-center justify-center gap-2 rounded-xl border border-[var(--on-hero)]/40 bg-[var(--on-hero)]/10 px-4 py-2.5 text-sm font-semibold text-[var(--on-hero)] no-underline transition hover:bg-[var(--on-hero)]/15"
                to="/integrations"
              >
                Manage shortcodes
                <ArrowUpRight size={16} aria-hidden="true" />
              </Link>
            )}
          </div>
        </div>
      </section>


      {/* Goal checklist */}
      {readiness && (
        <section className="rounded-2xl border border-[var(--border)] bg-[var(--panel)] p-5 shadow-[var(--shadow-sm)]">
          <h2 className="m-0 text-base font-bold text-[var(--text)]">
            Setup for {activeBusiness?.name || 'this business'}
          </h2>
          <p className="mb-4 mt-1 text-sm text-[var(--muted)]">
            Complete these so you can collect in the app and from your own systems.
          </p>
          <ul className="m-0 list-none space-y-3 p-0">
            {[
              {
                ok: readiness.has_shortcode,
                label: 'Shortcode added',
                hint: 'Paybill or till for this business',
                to: '/integrations/new',
                cta: 'Add shortcode',
              },
              {
                ok: readiness.has_connected_shortcode,
                label: 'M-Pesa connected',
                hint: 'Results can reach NetPay automatically',
                to: '/integrations',
                cta: 'Connect',
              },
              {
                ok: readiness.has_notifications,
                label: 'After-payment notification',
                hint: 'Your app is told when money moves',
                to: '/webhooks',
                cta: 'Add URL',
              },
              {
                ok: readiness.has_api_client,
                label: 'System connected (API client)',
                hint: 'Your backend can start payments',
                to: '/oauth-clients',
                cta: 'Create client',
              },
            ].map((row) => (
              <li
                key={row.label}
                className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[var(--border)] bg-[var(--panel-2)] px-4 py-3"
              >
                <div className="min-w-0">
                  <div className="text-sm font-semibold text-[var(--text)]">
                    <span className={row.ok ? 'text-[var(--accent)]' : 'text-[var(--muted)]'}>
                      {row.ok ? '✓' : '○'}
                    </span>{' '}
                    {row.label}
                  </div>
                  <div className="text-xs text-[var(--muted)]">{row.hint}</div>
                </div>
                {!row.ok && (
                  <Link
                    to={row.to}
                    className="shrink-0 text-sm font-semibold text-[var(--accent)] no-underline hover:underline"
                  >
                    {row.cta} →
                  </Link>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}

      {error && (
        <DismissibleBanner tone="error" onDismiss={() => setError(null)}>
          {error}
        </DismissibleBanner>
      )}

      <section aria-label="Payment pulse">
        <p className="mb-3 text-xs font-semibold uppercase tracking-[0.12em] text-[var(--accent)]">
          Pulse
        </p>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <PulseCard
            icon={CreditCard}
            label="Paid"
            value={loading ? '—' : String(paidCount)}
            detail="Successful payments"
            to="/intents"
            tone="accent"
          />
          <PulseCard
            icon={Clock3}
            label="Waiting"
            value={loading ? '—' : String(waitingCount)}
            detail="Still in progress"
            to="/intents"
            tone="warn"
          />
          <PulseCard
            icon={CircleAlert}
            label="Failed"
            value={loading ? '—' : String(failedCount)}
            detail="Need a new attempt"
            to="/intents"
            tone="danger"
          />
          <PulseCard
            icon={Landmark}
            label="Shortcodes"
            value={loading ? '—' : String(readiness?.shortcode_count ?? 0)}
            detail={
              readiness?.has_connected_shortcode
                ? 'Connected for results'
                : readiness?.has_shortcode
                  ? 'Connect M-Pesa next'
                  : 'Add one to collect'
            }
            to="/integrations"
            tone="accent"
          />
        </div>
      </section>

      <div className="grid items-start gap-5 lg:grid-cols-2">
        <section className="rounded-2xl border border-[var(--border)] bg-[var(--panel)] p-5 shadow-[var(--shadow-sm)]">
          <div className="flex items-start gap-3">
            <span
              className={`flex size-10 shrink-0 items-center justify-center rounded-xl ${
                ready
                  ? 'bg-[var(--accent-soft)] text-[var(--accent)]'
                  : 'bg-[var(--warn-soft)] text-[var(--warn)]'
              }`}
            >
              {ready ? <Check size={18} aria-hidden /> : <CircleAlert size={18} aria-hidden />}
            </span>
            <div className="min-w-0 flex-1">
              <h2 className="m-0 text-base font-bold">{copy.title}</h2>
              <p className="mb-3 mt-1 text-sm text-[var(--muted)]">{copy.detail}</p>
              <div className="flex flex-wrap gap-2">
                <Link to={connectTo} className="no-underline">
                  <Button size="sm">{copy.cta}</Button>
                </Link>
                {readiness?.has_shortcode && step !== 'add_shortcode' && (
                  <Link to="/integrations" className="no-underline">
                    <Button size="sm" variant="secondary">
                      Shortcodes
                    </Button>
                  </Link>
                )}
              </div>
            </div>
          </div>
        </section>

        <section className="rounded-2xl border border-[var(--border)] bg-[var(--panel)] p-5 shadow-[var(--shadow-sm)]">
          <div className="flex items-start gap-3">
            <span
              className={`flex size-10 shrink-0 items-center justify-center rounded-xl ${
                waitingCount > 0 || failedCount > 0
                  ? 'bg-[var(--warn-soft)] text-[var(--warn)]'
                  : 'bg-[var(--accent-soft)] text-[var(--accent)]'
              }`}
            >
              {waitingCount > 0 || failedCount > 0 ? (
                <CircleAlert size={18} aria-hidden />
              ) : (
                <Check size={18} aria-hidden />
              )}
            </span>
            <div className="min-w-0">
              <h2 className="m-0 text-base font-bold">Needs attention</h2>
              <p className="mb-3 mt-1 text-sm leading-6 text-[var(--muted)]">
                {loading
                  ? 'Checking activity…'
                  : waitingCount > 0 || failedCount > 0
                    ? [
                        waitingCount > 0 ? `${waitingCount} waiting on the customer` : null,
                        failedCount > 0 ? `${failedCount} failed` : null,
                      ]
                        .filter(Boolean)
                        .join(' · ') + '.'
                    : 'Nothing urgent right now.'}
              </p>
              <Link
                className="inline-flex items-center gap-1 text-sm font-semibold text-[var(--accent)] hover:underline"
                to={waitingCount > 0 || failedCount > 0 ? '/intents' : '/reconciliation'}
              >
                {waitingCount > 0 || failedCount > 0 ? 'Review payments' : 'Needs attention board'}
                <ArrowRight size={15} aria-hidden />
              </Link>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}

function PulseCard({
  icon: Icon,
  label,
  value,
  detail,
  to,
  tone,
}: {
  icon: typeof CreditCard
  label: string
  value: string
  detail: string
  to: string
  tone: 'accent' | 'warn' | 'danger'
}) {
  const toneClass =
    tone === 'warn'
      ? 'text-[var(--warn)] bg-[var(--warn-soft)]'
      : tone === 'danger'
        ? 'text-[var(--danger)] bg-[var(--danger-soft)]'
        : 'text-[var(--accent)] bg-[var(--accent-soft)]'

  return (
    <Link
      className="group rounded-2xl border border-[var(--border)] bg-[var(--panel)] p-4 no-underline shadow-[var(--shadow-sm)] transition hover:-translate-y-0.5 hover:border-[var(--accent)]/40 hover:shadow-[var(--shadow)]"
      to={to}
    >
      <div className="flex items-start justify-between gap-3">
        <span className={`flex size-10 items-center justify-center rounded-xl ${toneClass}`}>
          <Icon size={18} aria-hidden />
        </span>
        <ArrowUpRight
          className="text-[var(--muted)] transition group-hover:text-[var(--accent)]"
          size={16}
          aria-hidden
        />
      </div>
      <p className="mb-0 mt-4 text-sm font-medium text-[var(--muted)]">{label}</p>
      <p className="mb-0 mt-1 text-2xl font-semibold tracking-tight text-[var(--text)]">{value}</p>
      <p className="mb-0 mt-1 text-xs text-[var(--muted)]">{detail}</p>
    </Link>
  )
}
