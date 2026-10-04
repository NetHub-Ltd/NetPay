import { useState } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { useTheme } from '../theme/ThemeContext'

export function Login() {
  const { user, login, loading, oidcReady } = useAuth()
  const { theme, toggle } = useTheme()
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  if (loading) return <div className="flex min-h-screen items-center justify-center bg-[var(--bg)] text-sm text-[var(--muted)]">Loading…</div>
  if (user) return <Navigate to="/" replace />

  async function onSignIn() {
    setBusy(true); setError(null)
    try { await login() } catch (e) { setError(e instanceof Error ? e.message : 'Could not start sign-in'); setBusy(false) }
  }

  return (
    <div className="grid min-h-screen grid-cols-1 bg-[var(--bg)] text-[var(--text)] lg:grid-cols-[1.1fr_1fr]" data-testid="login-page">
      <section className="flex min-h-[360px] flex-col justify-center gap-6 bg-[var(--login-hero-bg)] px-8 py-12 text-slate-50 sm:px-10 lg:min-h-screen lg:px-16" aria-label="About NetPay">
        <div>
          <div className="mb-2 text-xs opacity-85">NetHub · NetPay</div>
          <h1 className="m-0 max-w-2xl text-3xl font-bold leading-tight tracking-tight sm:text-4xl">Accept M-Pesa payments without the headache</h1>
          <p className="mt-4 max-w-xl text-base leading-7 opacity-92">Sign in with your NetHub account. You will be redirected to the secure NetHub identity provider (Zitadel), then return here with an access token NetPay never issues or stores as a password.</p>
        </div>
        <ul className="m-0 list-disc space-y-2 pl-5 text-sm opacity-95">
          <li>STK Push to any Safaricom number</li>
          <li>See Paid, Waiting, Failed, or Expired in plain language</li>
          <li>Ledger trail for every successful collection</li>
          <li>Secure edge callbacks from M-Pesa into your account</li>
        </ul>
      </section>
      <section className="flex items-center justify-center bg-[var(--bg)] p-6 sm:p-8">
        <div className="w-full max-w-[400px] rounded-[calc(var(--radius)+4px)] border border-[var(--border)] bg-[var(--panel)] p-6 shadow-[var(--shadow)] sm:p-7">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="m-0 text-xl font-semibold">Sign in</h2>
              <p className="mb-4 mt-1 text-xs text-[var(--muted)]">Continue with NetHub (Zitadel). No NetPay password.</p>
            </div>
            <button type="button" className="rounded-lg px-2 py-1 text-xs text-[var(--muted)] hover:bg-[var(--panel-2)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--accent)]" onClick={toggle} title="Toggle appearance">{theme === 'light' ? 'Dark' : 'Light'}</button>
          </div>
          {error && <div className="mb-4 rounded-lg border border-[var(--danger)]/30 bg-[var(--danger)]/10 px-4 py-3 text-sm text-[var(--danger)]">{error}</div>}
          {!oidcReady && <div className="mb-4 rounded-lg border border-[var(--danger)]/30 bg-[var(--danger)]/10 px-4 py-3 text-sm text-[var(--danger)]">OIDC is not configured. Set <code>VITE_OIDC_ISSUER</code> and <code>VITE_OIDC_CLIENT_ID</code> for this build.</div>}
          <button type="button" className="inline-flex w-full items-center justify-center rounded-lg border border-[var(--accent)] bg-[var(--accent)] px-3 py-2.5 text-sm font-medium text-white transition-colors hover:bg-[var(--accent-hover)] disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--accent)]" disabled={busy || !oidcReady} onClick={() => void onSignIn()}>{busy ? 'Redirecting…' : 'Continue with NetHub'}</button>
        </div>
      </section>
    </div>
  )
}
