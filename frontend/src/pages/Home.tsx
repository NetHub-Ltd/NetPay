import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowRight,
  Bell,
  CreditCard,
  Landmark,
  Sparkles,
} from 'lucide-react'
import { api, ApiError, type Integration, type PaymentIntent, type Webhook } from '../api/client'
import { StatusBadge } from '../components/StatusBadge'
import { useAuth } from '../auth/AuthContext'

function money(minor?: number) {
  if (minor == null) return '—'
  return `KES ${(minor / 100).toFixed(2)}`
}

function greetingName(user: { display_name?: string | null; email?: string } | null) {
  if (!user) return null
  if (user.display_name?.trim()) return user.display_name.trim().split(/\s+/)[0]
  const email = user.email || ''
  return email.split('@')[0] || null
}

export function Home() {
  const { user } = useAuth()
  const [payments, setPayments] = useState<PaymentIntent[]>([])
  const [integrations, setIntegrations] = useState<Integration[]>([])
  const [hooks, setHooks] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      setLoading(true)
      try {
        const [pay, integ] = await Promise.all([
          api.get<PaymentIntent[]>('/v1/payment-intents'),
          api.get<Integration[]>('/v1/integrations'),
        ])
        setPayments((pay || []).slice(0, 5))
        setIntegrations(integ || [])
        const tid = user?.tenant_id
        if (tid) {
          try {
            const w = await api.get<Webhook[]>(`/v1/webhooks?tenant_id=${tid}`)
            setHooks(w.length)
          } catch {
            setHooks(0)
          }
        }
      } catch (e) {
        setError(e instanceof ApiError ? e.detail : 'Could not load dashboard')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [user])

  const first = greetingName(user)
  const hasShortcode = integrations.length > 0
  const nextStep = !hasShortcode
    ? {
        title: 'Add a shortcode',
        body: 'Connect a paybill or till to start requesting payments.',
        to: '/integrations',
        label: 'Paybills & tills',
        Icon: Landmark,
      }
    : hooks === 0
      ? {
          title: 'Optional: app notifications',
          body: 'Forward payment status to your own systems when you’re ready.',
          to: '/webhooks',
          label: 'Notifications',
          Icon: Bell,
        }
      : {
          title: 'Request a payment',
          body: 'Send a prompt to a customer’s phone and track the result here.',
          to: '/intents',
          label: 'Payments',
          Icon: CreditCard,
        }

  const NextIcon = nextStep.Icon

  return (
    <div data-testid="home-page" className="home">
      <div className="home-hero">
        <div>
          <p className="home-eyebrow">Overview</p>
          <h1 className="home-title">{first ? `Hello, ${first}` : 'Hello'}</h1>
          <p className="home-sub muted">
            A quiet view of recent collections and what needs your attention next.
          </p>
        </div>
        <Link className="btn primary" to="/intents">
          <CreditCard size={16} strokeWidth={1.75} />
          New payment
        </Link>
      </div>

      {error && <div className="alert error">{error}</div>}

      <div className="home-stats">
        <div className="stat-card">
          <div className="stat-label">
            <Landmark size={14} strokeWidth={1.75} /> Shortcodes
          </div>
          <div className="stat-value">{loading ? '—' : integrations.length}</div>
          <Link to="/integrations" className="stat-link">
            Manage <ArrowRight size={12} />
          </Link>
        </div>
        <div className="stat-card">
          <div className="stat-label">
            <Bell size={14} strokeWidth={1.75} /> Notifications
          </div>
          <div className="stat-value">{loading ? '—' : hooks}</div>
          <Link to="/webhooks" className="stat-link">
            Configure <ArrowRight size={12} />
          </Link>
        </div>
        <div className="stat-card">
          <div className="stat-label">
            <CreditCard size={14} strokeWidth={1.75} /> Recent
          </div>
          <div className="stat-value">{loading ? '—' : payments.length}</div>
          <Link to="/intents" className="stat-link">
            All payments <ArrowRight size={12} />
          </Link>
        </div>
      </div>

      <div className="home-grid">
        <section className="card home-panel">
          <div className="panel-head">
            <h2>Recent payments</h2>
            <Link to="/intents" className="tiny">
              View all
            </Link>
          </div>
          {loading ? (
            <p className="muted tiny">Loading…</p>
          ) : payments.length === 0 ? (
            <div className="empty-soft">
              <p className="muted">No payments yet.</p>
              <Link className="btn" to="/intents">
                Create one
              </Link>
            </div>
          ) : (
            <table className="home-table">
              <thead>
                <tr>
                  <th>Amount</th>
                  <th>Phone</th>
                  <th>Status</th>
                  <th>When</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {payments.map((p) => (
                  <tr key={p.id}>
                    <td className="mono">{money(p.amount_minor)}</td>
                    <td className="mono tiny">{p.phone}</td>
                    <td>
                      <StatusBadge value={p.status} />
                    </td>
                    <td className="muted tiny">
                      {p.created_at ? new Date(p.created_at).toLocaleString() : '—'}
                    </td>
                    <td>
                      <Link to={`/intents/${p.id}`}>Open</Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>

        <section className="card home-panel home-next">
          <div className="panel-head">
            <h2>
              <Sparkles size={16} strokeWidth={1.75} className="inline-ico" /> Suggested next step
            </h2>
          </div>
          <div className="next-body">
<NextIcon size={20} strokeWidth={1.75} className="next-ico" />
            <div>
              <div className="next-title">{nextStep.title}</div>
              <p className="muted tiny" style={{ margin: '0.35rem 0 0.85rem' }}>
                {nextStep.body}
              </p>
              <Link className="btn" to={nextStep.to}>
                {nextStep.label}
                <ArrowRight size={14} />
              </Link>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
