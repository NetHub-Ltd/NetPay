import { type FormEvent, useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { ApiError } from '../api/client'
import { useTheme } from '../theme/ThemeContext'

/**
 * NetPay does not issue passwords. Paste an IdP (Zitadel) access token;
 * NetPay resolves the user via NetHub GET /users/me.
 */
export default function Login() {
  const { user, setAccessToken } = useAuth()
  const { theme, toggle } = useTheme()
  const navigate = useNavigate()
  const [token, setToken] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  if (user) return <Navigate to="/" replace />

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await setAccessToken(token)
      navigate('/', { replace: true })
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Could not verify session with NetHub')
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
            Sign in with your NetHub identity (Zitadel). NetPay never stores passwords — it asks
            NetHub who you are using your access token.
          </p>
        </div>
        <ul>
          <li>STK Push to any Safaricom number</li>
          <li>See Paid, Waiting, Failed, or Expired in plain language</li>
          <li>Ledger trail for every successful collection</li>
          <li>Secure edge callbacks from M-Pesa into your account</li>
        </ul>
      </section>

      <section className="login-panel">
        <div className="login-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <h2>Continue with NetHub</h2>
              <p className="muted tiny" style={{ margin: '0 0 1rem' }}>
                Paste an access token from the IdP (or NetHub session). Production UX will use a
                redirect login — token paste is for ops and early cutover.
              </p>
            </div>
            <button type="button" className="btn ghost" onClick={toggle} title="Toggle appearance">
              {theme === 'light' ? 'Dark' : 'Light'}
            </button>
          </div>
          {error && <div className="alert error">{error}</div>}
          <form onSubmit={onSubmit}>
            <label htmlFor="access_token">Access token</label>
            <textarea
              id="access_token"
              rows={4}
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="Bearer token value (without the word Bearer)"
              required
              style={{ width: '100%', fontFamily: 'monospace', fontSize: 12 }}
            />
            <button type="submit" className="btn primary" disabled={busy || !token.trim()}>
              {busy ? 'Verifying…' : 'Continue'}
            </button>
          </form>
        </div>
      </section>
    </div>
  )
}
