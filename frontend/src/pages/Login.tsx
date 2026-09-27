import { useState, type FormEvent } from 'react'
import { useAuth } from '../auth/AuthContext'
import { useTheme } from '../theme/ThemeContext'

/**
 * Password login removed (P2 #25).
 * Production path: obtain a Keycloak access token (aud=nethub-backend) via NetHub SSO,
 * then store it. For local/dev we accept a pasted Bearer token.
 */
export default function Login() {
  const { loginWithToken } = useAuth()
  const { theme, toggle } = useTheme()
  const [token, setToken] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setBusy(true)
    try {
      const cleaned = token.replace(/^Bearer\s+/i, '').trim()
      if (!cleaned) {
        setError('Paste a Keycloak access token (audience nethub-backend).')
        return
      }
      await loginWithToken(cleaned)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sign-in failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="login-layout">
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
              <h2>Sign in with NetHub</h2>
              <p className="muted tiny" style={{ margin: '0 0 1rem' }}>
                Password login has been removed. Authenticate via Keycloak / NetHub SSO
                (audience <code>nethub-backend</code>), then paste the access token below for local use.
                Production will redirect to NetHub SSO automatically.
              </p>
            </div>
            <button type="button" className="btn ghost" onClick={toggle} title="Toggle appearance">
              {theme === 'light' ? 'Dark' : 'Light'}
            </button>
          </div>
          {error && <div className="alert error">{error}</div>}
          <form onSubmit={onSubmit}>
            <label htmlFor="token">Access token</label>
            <textarea
              id="token"
              rows={4}
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
              required
              style={{ width: '100%', fontFamily: 'monospace', fontSize: '0.85rem' }}
            />
            <div style={{ marginTop: '1rem' }}>
              <button className="btn primary full" type="submit" disabled={busy}>
                {busy ? 'Signing in…' : 'Continue'}
              </button>
            </div>
          </form>
        </div>
      </section>
    </div>
  )
}
