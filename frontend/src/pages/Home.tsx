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
import { StatusBadge, formatKes } from '../components/StatusBadge'
import { DataTable } from '../components/DataTable'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { subscribeLiveMessages } from '../hooks/useWebSocket'

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
  const navigate = useNavigate()
  const [payments, setPayments] = useState<PaymentIntent[]>([])
  const [integrations, setIntegrations] = useState<Integration[]>([])
  const [hooks, setHooks] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  async function load(quiet = false) {
    if (!quiet) setLoading(true)
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

  useEffect(() => {
    load()
  }, [user])

  useEffect(() => {
    return subscribeLiveMessages((m) => {
      if (m.type === 'payment.update' || m.type === 'notification') {
        load(true)
      }
    })
  }, [user])

  const first = greetingName(user)
  const hasShortcode = integrations.length > 0
  const waitingCount = payments.filter((p) => p.status === 'provider_requested' || p.status === 'created').length
  const nextStep = !hasShortcode
    ? {
        title: 'Add a shortcode',
        body: 'Connect a paybill or till so you can request payments from customers.',
        to: '/integrations',
        label: 'Add shortcode',
        Icon: Landmark,
      }
    : waitingCount > 0
      ? {
          title: 'Payments waiting on the customer',
          body: 'A phone prompt is open. It usually settles within a minute — open a payment for details.',
          to: '/intents',
          label: 'View payments',
          Icon: CreditCard,
        }
      : {
          title: 'Request a payment',
          body: 'Send a prompt to a customer’s phone and track the result here.',
          to: '/intents',
          label: 'New payment',
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
            A calm view of recent collections and what needs attention next.
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
            <Bell size={14} strokeWidth={1.75} /> App endpoints
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

      <section className="card home-panel home-next home-next-inline">
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

      <section className="card home-panel home-payments-full">
        <div className="panel-head">
          <h2>Recent payments</h2>
          <Link to="/intents" className="tiny">
            View all
          </Link>
        </div>
        {loading ? (
          <p className="muted tiny">Loading…</p>
        ) : (
          <DataTable
            rows={payments}
            getRowId={(p) => p.id}
            searchPlaceholder="Search…"
            defaultPageSize={5}
            pageSizeOptions={[5, 10]}
            maxHeight="320px"
            emptyTitle="No payments yet"
            emptyHint="Create a payment to see it here."
            onRowClick={(p) => navigate(`/intents/${p.id}`)}
            columns={[
              {
                id: 'amount',
                header: 'Amount',
                searchValue: (p) => money(p.amount_minor),
                cell: (p) => <span className="mono">{money(p.amount_minor)}</span>,
              },
              {
                id: 'phone',
                header: 'Phone',
                searchValue: (p) => p.phone || '',
                cell: (p) => <span className="mono tiny">{p.phone}</span>,
              },
              {
                id: 'status',
                header: 'Status',
                searchValue: (p) => p.status,
                cell: (p) => <StatusBadge value={p.status} />,
              },
              {
                id: 'when',
                header: 'When',
                cell: (p) => (
                  <span className="muted tiny">
                    {p.created_at ? new Date(p.created_at).toLocaleString() : '—'}
                  </span>
                ),
              },
            ]}
          />
        )}
      </section>
    </div>
  )
}
