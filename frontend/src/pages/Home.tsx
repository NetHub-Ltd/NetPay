import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, ApiError, type Integration, type PaymentIntent, type Webhook } from '../api/client'
import { StatusBadge } from '../components/StatusBadge'
import { useAuth } from '../auth/AuthContext'

function money(minor?: number) {
  if (minor == null) return '—'
  return `KES ${(minor / 100).toFixed(2)}`
}

export function Home() {
  const { user, isAdmin } = useAuth()
  const [payments, setPayments] = useState<PaymentIntent[]>([])
  const [integrations, setIntegrations] = useState<Integration[]>([])
  const [hooks, setHooks] = useState(0)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function load() {
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
        setError(e instanceof ApiError ? e.detail : 'Could not load home')
      }
    }
    load()
  }, [user])

  const name = user?.display_name || user?.email || 'there'
  const hasShortcode = integrations.length > 0

  return (
    <div data-testid="home-page">
      <div className="page-header">
        <div>
          <h1>Welcome{user ? `, ${name.split('@')[0]}` : ''}</h1>
          <p>Collect payments, track status, and keep your shortcodes healthy.</p>
        </div>
        <Link className="btn primary" to="/intents">
          ＋ New payment
        </Link>
      </div>
      {error && <div className="alert error">{error}</div>}

      <div className="grid-3" style={{ marginBottom: '1rem' }}>
        <div className="card">
          <div className="muted tiny">Shortcodes</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{integrations.length}</div>
          <Link to="/integrations" className="tiny">
            Manage →
          </Link>
        </div>
        <div className="card">
          <div className="muted tiny">App notifications</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{hooks}</div>
          <Link to="/webhooks" className="tiny">
            Configure →
          </Link>
        </div>
        <div className="card">
          <div className="muted tiny">Recent payments shown</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{payments.length}</div>
          <Link to="/intents" className="tiny">
            All payments →
          </Link>
        </div>
      </div>

      {!hasShortcode && (
        <div className="card" style={{ borderColor: 'var(--accent)' }}>
          <h2>Get started</h2>
          <p style={{ marginTop: 0 }}>
            You don’t have a paybill or till yet. Add a shortcode so you can request money from customers.
          </p>
          <Link className="btn primary" to="/integrations">
            ✦ Register your first shortcode
          </Link>
        </div>
      )}

      {hasShortcode && hooks === 0 && (
        <div className="card">
          <h2>Optional: notify your app</h2>
          <p className="muted" style={{ marginTop: 0 }}>
            Add an HTTPS URL so your system is told when a payment is Paid or Failed.
          </p>
          <Link className="btn" to="/webhooks">
            ✉ Payment notifications
          </Link>
        </div>
      )}

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ margin: 0 }}>Latest payments</h2>
          <Link to="/intents">View all</Link>
        </div>
        {payments.length === 0 ? (
          <p className="muted">No payments yet. When you send a payment request, the last five appear here.</p>
        ) : (
          <table>
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
                  <td>{money(p.amount_minor)}</td>
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
      </div>

      <div className="card">
        <h2>What you can do</h2>
        <ul style={{ margin: 0, paddingLeft: '1.1rem' }}>
          <li>
            <Link to="/integrations">Paybills &amp; tills</Link> — add shortcodes and connect payment updates
          </li>
          <li>
            <Link to="/intents">Payments</Link> — send a phone prompt and track Paid / Failed
          </li>
          <li>
            <Link to="/webhooks">Payment notifications</Link> — push status to your own app
          </li>
          <li>
            <Link to="/reconciliation">Needs attention</Link> — exceptions that need a human look
          </li>
          {isAdmin && (
            <li>
              <Link to="/">System status</Link> is under the header · Admin tools in the sidebar
            </li>
          )}
        </ul>
      </div>
    </div>
  )
}
