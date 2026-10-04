import { useCallback, useEffect, useMemo, useState } from 'react'
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
import { api, ApiError, type Integration, type PaymentIntent, type Webhook } from '../api/client'
import { useAuth } from '../auth/authState'
import { paymentLifecycleBucket } from '../components/statusUtils'
import { subscribeLiveMessages } from '../hooks/liveEvents'
import { Button } from '../components/primitives'

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
  const [payments, setPayments] = useState<PaymentIntent[]>([])
  const [integrations, setIntegrations] = useState<Integration[]>([])
  const [webhookCount, setWebhookCount] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(
    async (quiet = false) => {
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
        setError(e instanceof ApiError ? e.detail : 'Could not load overview')
      } finally {
        setLoading(false)
      }
    },
    [user],
  )

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
  const hasShortcode = integrations.length > 0
  const hasWebhooks = webhookCount > 0
  const firstIntegrationId = integrations[0]?.id

  const setupSteps = useMemo(
    () => [
      {
        id: 'shortcode',
        title: 'Add a shortcode',
        detail: 'Paybill or till so customers know where to pay.',
        complete: hasShortcode,
        to: '/integrations',
        cta: 'Add shortcode',
      },
      {
        id: 'connect',
        title: 'Confirm M-Pesa connection',
        detail: 'Open your shortcode and connect so results reach NetPay.',
        complete: hasShortcode,
        to: firstIntegrationId ? `/integrations/${firstIntegrationId}` : '/integrations',
        cta: 'Open shortcode',
        optional: true,
      },
      {
        id: 'notify',
        title: 'Notify your app',
        detail: 'HTTPS URL for paid / failed updates.',
        complete: hasWebhooks,
        to: '/webhooks',
        cta: 'Add URL',
        optional: true,
      },
    ],
    [hasShortcode, hasWebhooks, firstIntegrationId],
  )

  const setupIncomplete = !hasShortcode
  const nextStep = setupSteps.find((s) => !s.complete)

  const paidCount = payments.filter((p) => paymentLifecycleBucket(p.status) === 'successful').length
  const waitingCount = payments.filter((p) => paymentLifecycleBucket(p.status) === 'processing').length
  const failedCount = payments.filter((p) => paymentLifecycleBucket(p.status) === 'failed').length

  const heroCta = !hasShortcode
    ? { to: '/integrations', label: 'Add shortcode', icon: Landmark }
    : { to: '/intents', label: 'Take a payment', icon: Plus }

  return (
    <div className="space-y-6" data-testid="home-page">
      <section className="relative isolate overflow-hidden rounded-3xl bg-[var(--hero-bg)] px-6 py-7 text-white shadow-[var(--shadow)] sm:px-8 sm:py-9">
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
              {setupIncomplete ? 'Get ready to collect' : 'Your collections, in one place'}
            </div>
            <h1 className="m-0 text-3xl font-semibold tracking-tight sm:text-4xl">
              {greeting()}
              {firstName ? `, ${firstName}` : ''}.
            </h1>
            <p className="mb-0 mt-3 max-w-xl text-sm leading-6 text-white/75 sm:text-base">
              {setupIncomplete
                ? nextStep
                  ? `Next: ${nextStep.title.toLowerCase()}.`
                  : 'Finish setup so payments can flow.'
                : 'See what needs attention and jump into the work that matters.'}
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-[var(--accent-hover)] no-underline shadow-sm transition hover:bg-white/90"
              to={heroCta.to}
            >
              <heroCta.icon size={17} aria-hidden="true" />
              {heroCta.label}
            </Link>
            {hasShortcode && (
              <Link
                className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/40 bg-white/10 px-4 py-2.5 text-sm font-semibold text-white no-underline transition hover:bg-white/15"
                to="/integrations"
              >
                Manage shortcodes
                <ArrowUpRight size={16} aria-hidden="true" />
              </Link>
            )}
          </div>
        </div>
      </section>

      {error && (
        <div
          className="rounded-xl border border-[var(--danger)]/25 bg-[var(--danger-soft)] px-4 py-3 text-sm text-[var(--danger)]"
          role="alert"
        >
          {error}
        </div>
      )}

      {/* Pulse — insight only, links into filtered lists */}
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
            color="text-[var(--accent)] bg-[var(--accent-soft)]"
          />
          <PulseCard
            icon={Clock3}
            label="Waiting"
            value={loading ? '—' : String(waitingCount)}
            detail="Still in progress"
            to="/intents"
            color="text-[var(--warn)] bg-[var(--warn-soft)]"
          />
          <PulseCard
            icon={CircleAlert}
            label="Failed"
            value={loading ? '—' : String(failedCount)}
            detail="Need a new attempt"
            to="/intents"
            color="text-[var(--danger)] bg-[var(--danger-soft)]"
          />
          <PulseCard
            icon={Landmark}
            label="Shortcodes"
            value={loading ? '—' : String(integrations.length)}
            detail={hasShortcode ? 'Ready for collection' : 'Add one to collect'}
            to="/integrations"
            color="text-[var(--accent)] bg-[var(--accent-soft)]"
          />
        </div>
      </section>

      <div className="grid items-start gap-5 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)]">
        {/* Readiness — hide when fully ready (required steps done) */}
        {setupIncomplete ? (
          <section className="rounded-2xl border border-[var(--border)] bg-[var(--panel)] p-5 shadow-[var(--shadow-sm)]">
            <h2 className="m-0 text-base font-semibold tracking-tight">Get ready</h2>
            <p className="mb-4 mt-1 text-sm text-[var(--muted)]">
              Complete these so you can collect with confidence.
            </p>
            <ul className="m-0 flex list-none flex-col gap-3 p-0">
              {setupSteps.map((step) => (
                <li
                  key={step.id}
                  className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[var(--border)] bg-[var(--panel-2)] px-4 py-3"
                >
                  <div className="flex min-w-0 items-start gap-3">
                    <span
                      className={`mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-lg ${
                        step.complete
                          ? 'bg-[var(--accent-soft)] text-[var(--accent)]'
                          : 'bg-[var(--panel)] text-[var(--muted)]'
                      }`}
                    >
                      {step.complete ? (
                        <Check size={16} aria-hidden="true" />
                      ) : (
                        <span className="text-xs font-bold">{step.optional ? '·' : '!'}</span>
                      )}
                    </span>
                    <div className="min-w-0">
                      <p className="m-0 text-sm font-semibold text-[var(--text)]">
                        {step.title}
                        {step.optional && (
                          <span className="ml-2 text-xs font-normal text-[var(--muted)]">
                            Optional
                          </span>
                        )}
                      </p>
                      <p className="mb-0 mt-0.5 text-xs text-[var(--muted)]">{step.detail}</p>
                    </div>
                  </div>
                  {!step.complete && (
                    <Link to={step.to} className="no-underline">
                      <Button size="sm" variant={step.optional ? 'secondary' : 'primary'}>
                        {step.cta}
                      </Button>
                    </Link>
                  )}
                </li>
              ))}
            </ul>
          </section>
        ) : (
          <section className="rounded-2xl border border-[var(--border)] bg-[var(--panel)] p-5 shadow-[var(--shadow-sm)]">
            <div className="flex items-start gap-3">
              <span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-[var(--accent-soft)] text-[var(--accent)]">
                <Check size={18} aria-hidden="true" />
              </span>
              <div>
                <h2 className="m-0 text-base font-semibold">You’re set up</h2>
                <p className="mb-3 mt-1 text-sm text-[var(--muted)]">
                  Shortcode is in place
                  . Take a payment or review
                  activity anytime.
                </p>
                <div className="flex flex-wrap gap-2">
                  <Link to="/intents" className="no-underline">
                    <Button size="sm" leftIcon={<Plus size={16} />}>
                      Take a payment
                    </Button>
                  </Link>
                  <Link to="/integrations" className="no-underline">
                    <Button size="sm" variant="secondary">
                      Shortcodes
                    </Button>
                  </Link>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* Attention — only emphasize when something waits */}
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
                <CircleAlert size={18} aria-hidden="true" />
              ) : (
                <Check size={18} aria-hidden="true" />
              )}
            </span>
            <div className="min-w-0">
              <h2 className="m-0 text-base font-semibold">Needs attention</h2>
              <p className="mb-3 mt-1 text-sm leading-6 text-[var(--muted)]">
                {loading
                  ? 'Checking activity…'
                  : waitingCount > 0 || failedCount > 0
                    ? [
                        waitingCount > 0
                          ? `${waitingCount} waiting on the customer`
                          : null,
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
                <ArrowRight size={15} aria-hidden="true" />
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
      <p className="mb-0 mt-1 text-2xl font-semibold tracking-tight text-[var(--text)]">{value}</p>
      <p className="mb-0 mt-1 text-xs text-[var(--muted)]">{detail}</p>
    </Link>
  )
}
