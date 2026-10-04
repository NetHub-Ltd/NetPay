import { useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import {
  ArrowRight,
  Check,
  Landmark,
  LockKeyhole,
  Moon,
  Sun,
} from 'lucide-react'
import { useAuth } from '../auth/authState'
import { useTheme } from '../theme/themeState'

const trustPoints = [
  'Sign in with your NetHub account — no NetPay password',
  'Redirected to Zitadel, then returned with a secure token',
  'NetPay never stores or issues passwords for humans',
]

export function Login() {
  const { user, login, loading, oidcReady } = useAuth()
  const { theme, toggle } = useTheme()
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[var(--bg)] text-sm text-[var(--muted)]">
        Loading…
      </div>
    )
  }
  if (user) return <Navigate to="/dashboard" replace />

  async function onSignIn() {
    setBusy(true)
    setError(null)
    try {
      await login()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not start sign-in')
      setBusy(false)
    }
  }

  return (
    <main
      className="flex min-h-screen flex-col bg-[var(--bg)] text-[var(--text)]"
      data-testid="login-page"
    >
      <header className="relative z-10 mx-auto flex w-full max-w-7xl items-center justify-between px-5 py-5 sm:px-8 lg:px-10">
        <Link
          className="flex items-center gap-2.5 no-underline hover:no-underline"
          to="/"
          aria-label="NetPay home"
        >
          <span className="flex size-10 items-center justify-center rounded-xl bg-[var(--accent)] text-white shadow-sm">
            <Landmark size={21} strokeWidth={1.9} aria-hidden="true" />
          </span>
          <span className="text-lg font-bold tracking-tight text-[var(--text)]">
            NetPay
          </span>
        </Link>

        <div className="flex items-center gap-2">
          <button
            className="flex size-10 items-center justify-center rounded-xl border border-[var(--border)] bg-[var(--panel)] text-[var(--muted)] transition hover:bg-[var(--panel-2)] hover:text-[var(--text)]"
            type="button"
            onClick={toggle}
            title={theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}
            aria-label={theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}
          >
            {theme === 'light' ? (
              <Moon size={17} aria-hidden="true" />
            ) : (
              <Sun size={17} aria-hidden="true" />
            )}
          </button>
          <Link
            className="hidden rounded-xl px-4 py-2.5 text-sm font-semibold text-[var(--muted)] transition hover:bg-[var(--panel-2)] hover:text-[var(--text)] sm:inline-flex"
            to="/"
          >
            Home
          </Link>
        </div>
      </header>

      <div className="relative flex flex-1 flex-col items-center justify-center px-5 pb-16 pt-6 sm:px-8">
        {/* Soft brand wash behind the card — same accent language as Landing hero */}
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-x-0 top-0 h-72 bg-[var(--login-hero-bg)] opacity-[0.12] blur-3xl"
        />

        <div className="relative w-full max-w-[420px]">
          <div className="mb-8 text-center">
            <p className="mb-2 text-xs font-bold uppercase tracking-[0.16em] text-[var(--muted)]">
              NetHub identity
            </p>
            <h1 className="m-0 text-2xl font-semibold tracking-tight sm:text-3xl">
              Sign in to NetPay
            </h1>
            <p className="mx-auto mt-3 max-w-sm text-sm leading-6 text-[var(--muted)]">
              Continue with your NetHub account. You will be redirected to the
              secure identity provider, then returned here.
            </p>
          </div>

          <div className="rounded-2xl border border-[var(--border)] bg-[var(--panel)] p-6 shadow-[var(--shadow)] sm:p-7">
            <div className="mb-5 flex items-center gap-3">
              <span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-[var(--accent-soft)] text-[var(--accent)]">
                <LockKeyhole size={18} strokeWidth={1.9} aria-hidden="true" />
              </span>
              <div>
                <div className="text-sm font-semibold">Continue with NetHub</div>
                <div className="text-xs text-[var(--muted)]">
                  Zitadel · no NetPay password
                </div>
              </div>
            </div>

            {error && (
              <div
                className="mb-4 rounded-xl border border-[var(--danger)]/25 bg-[var(--danger-soft)] px-4 py-3 text-sm text-[var(--danger)]"
                role="alert"
              >
                {error}
              </div>
            )}

            {!oidcReady && (
              <div
                className="mb-4 rounded-xl border border-[var(--danger)]/25 bg-[var(--danger-soft)] px-4 py-3 text-sm text-[var(--danger)]"
                role="alert"
              >
                OIDC is not configured. Set{' '}
                <code className="font-mono text-[0.9em]">OIDC_ISSUER</code> and{' '}
                <code className="font-mono text-[0.9em]">OIDC_CLIENT_ID</code> on the
                server (or <code className="font-mono text-[0.9em]">VITE_*</code> for
                local dev).
              </div>
            )}

            <button
              type="button"
              className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-[var(--accent)] px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-[var(--accent-hover)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--accent)] disabled:cursor-not-allowed disabled:opacity-50"
              disabled={busy || !oidcReady}
              onClick={() => void onSignIn()}
            >
              {busy ? 'Redirecting…' : 'Continue with NetHub'}
              {!busy && <ArrowRight size={16} aria-hidden="true" />}
            </button>

            <ul className="mt-6 space-y-2.5 border-t border-[var(--border)] pt-5">
              {trustPoints.map((point) => (
                <li
                  key={point}
                  className="flex items-start gap-2.5 text-xs leading-5 text-[var(--muted)]"
                >
                  <span className="mt-0.5 flex size-4 shrink-0 items-center justify-center rounded-full bg-[var(--accent-soft)] text-[var(--accent)]">
                    <Check size={10} strokeWidth={3} aria-hidden="true" />
                  </span>
                  {point}
                </li>
              ))}
            </ul>
          </div>

          <p className="mt-6 text-center text-xs text-[var(--muted)]">
            New to NetPay?{' '}
            <Link className="font-medium text-[var(--accent)]" to="/">
              Learn what it does
            </Link>
          </p>
        </div>
      </div>

      <footer className="border-t border-[var(--border)] bg-[var(--panel)]">
        <div className="mx-auto flex w-full max-w-7xl flex-col gap-3 px-5 py-5 text-xs text-[var(--muted)] sm:flex-row sm:items-center sm:justify-between sm:px-8 lg:px-10">
          <Link
            className="font-semibold text-[var(--text)] no-underline hover:no-underline"
            to="/"
          >
            NetPay
          </Link>
          <span>Payment collection and visibility for your business.</span>
        </div>
      </footer>
    </main>
  )
}
