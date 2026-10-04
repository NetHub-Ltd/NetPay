import { useState } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { useTheme } from '../theme/ThemeContext'

/**
 * Browser login via Zitadel (OIDC + PKCE). No password, no token paste.
 */
export function Login() {
  const { user, login, loading, oidcReady } = useAuth()
  const { theme, toggle } = useTheme()
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  if (loading) {
    return (
      <div className="login-page">
        <p className="muted">Loading…</p>
      </div>
    )
  }
  if (user) return <Navigate to="/" replace />

  async function onSignIn() {
    setBusy(true)
    setError(null)
    try {
      await login()
      // redirect happens inside beginLogin
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not start sign-in')
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
            Sign in with your NetHub account. You will be redirected to the secure NetHub
            identity provider (Zitadel), then return here with an access token NetPay never
            issues or stores as a password.
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
              <h2>Sign in</h2>
              <p className="muted tiny" style={{ margin: '0 0 1rem' }}>
                Continue with NetHub (Zitadel). No NetPay password.
              </p>
            </div>
            <button type="button" className="btn ghost" onClick={toggle} title="Toggle appearance">
              {theme === 'light' ? 'Dark' : 'Light'}
            </button>
          </div>
          {error && <div className="alert error">{error}</div>}
          {!oidcReady && (
            <div className="alert error">
              OIDC is not configured. Set <code>VITE_OIDC_ISSUER</code> and{' '}
              <code>VITE_OIDC_CLIENT_ID</code> for this build.
            </div>
          )}
          <button
            type="button"
            className="btn primary"
            disabled={busy || !oidcReady}
            onClick={() => void onSignIn()}
            style={{ width: '100%' }}
          >
            {busy ? 'Redirecting…' : 'Continue with NetHub'}
          </button>
        </div>
      </section>
    </div>
  )
}
