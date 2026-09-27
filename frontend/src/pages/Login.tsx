import { useState } from 'react'
import { Link } from 'react-router-dom'
import { beginLogin } from '../auth/oidc'
import { useTheme } from '../theme/ThemeContext'

export default function Login() {
  const { theme, toggle } = useTheme()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function onSignIn() {
    setError(null)
    setBusy(true)
    try {
      await beginLogin('/home')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not start sign-in')
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
          <h1>Collect M-Pesa payments with clarity</h1>
          <p>
            STK Push, status tracking, and a ledger trail — secured by NetHub sign-in. No separate
            NetPay password.
          </p>
        </div>
        <ul>
          <li>Sign in once with your NetHub account</li>
          <li>Paybill and till collections</li>
          <li>Live status and reconciliation</li>
        </ul>
      </section>

      <section className="login-panel">
        <div className="login-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <h2>Sign in</h2>
              <p className="muted tiny" style={{ margin: '0 0 1rem' }}>
                You will be redirected to NetHub authentication (Keycloak). After success you return
                here to the dashboard.
              </p>
            </div>
            <button type="button" className="btn ghost" onClick={toggle} title="Toggle appearance">
              {theme === 'light' ? 'Dark' : 'Light'}
            </button>
          </div>
          {error && <div className="alert error">{error}</div>}
          <button className="btn primary full" type="button" disabled={busy} onClick={onSignIn}>
            {busy ? 'Redirecting…' : 'Sign in with NetHub'}
          </button>
          <p className="muted tiny" style={{ marginTop: '1rem', textAlign: 'center' }}>
            <Link to="/">Back to home</Link>
          </p>
        </div>
      </section>
    </div>
  )
}
