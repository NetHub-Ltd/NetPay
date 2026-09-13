import { type FormEvent, useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { ApiError } from '../api/client'
import { useTheme } from '../theme/ThemeContext'

export function Login() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const { theme, toggle } = useTheme()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  if (user) return <Navigate to="/" replace />

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await login(email, password)
      navigate('/', { replace: true })
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Could not sign in')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="login-shell" data-testid="login-page">
      <section className="login-hero" aria-label="About NetPay">
        <div>
          <div className="tiny" style={{ opacity: 0.85, marginBottom: '0.5rem' }}>
            NetHub · NetPay
          </div>
          <h1>Accept M-Pesa payments without the headache</h1>
          <p>
            Send a payment request to your customer’s phone, track whether they paid, and keep a clear record —
            built for Kenyan paybills and tills.
          </p>
        </div>
        <ul>
          <li>STK Push to any Safaricom number</li>
          <li>See Paid, Waiting, Failed, or Expired in plain language</li>
          <li>Ledger trail for every successful collection</li>
          <li>Secure edge callbacks from M-Pesa into your account</li>
        </ul>
        <div className="feature-pills">
          <span>Paybill</span>
          <span>Till</span>
          <span>Shortcode</span>
          <span>Real-time status</span>
        </div>
      </section>

      <section className="login-panel">
        <div className="login-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <h2>Sign in</h2>
              <p className="muted tiny" style={{ margin: '0 0 1rem' }}>
                Use your NetPay account to manage payments.
              </p>
            </div>
            <button type="button" className="btn ghost" onClick={toggle} title="Toggle appearance">
              {theme === 'light' ? 'Dark' : 'Light'}
            </button>
          </div>
          {error && <div className="alert error">{error}</div>}
          <form onSubmit={onSubmit}>
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            <div style={{ marginTop: '1rem' }}>
              <button className="btn primary full" type="submit" disabled={busy}>
                {busy ? 'Signing in…' : 'Sign in'}
              </button>
            </div>
          </form>
        </div>
      </section>
    </div>
  )
}
