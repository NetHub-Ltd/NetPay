import { useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { ArrowRight, Landmark, Moon, ShieldCheck, Sun } from 'lucide-react'
import { useAuth } from '../auth/authState'
import { useTheme } from '../theme/themeState'

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

      <div className="relative flex flex-1 flex-col items-center justify-center px-5 pb-16 pt-4 sm:px-8">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-x-0 top-0 h-72 bg-[var(--login-hero-bg)] opacity-[0.1] blur-3xl"
        />

        <div className="relative w-full max-w-[400px]">
          <div className="mb-8 text-center">
            <h1 className="m-0 text-2xl font-semibold tracking-tight sm:text-3xl">
              Sign in to NetPay
            </h1>
            <p className="mx-auto mt-3 max-w-sm text-sm leading-6 text-[var(--muted)]">
              Access your payments, shortcodes, and settlement activity in one
              place.
            </p>
          </div>

          <div className="rounded-2xl border border-[var(--border)] bg-[var(--panel)] p-6 shadow-[var(--shadow)] sm:p-8">
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
                Sign-in is temporarily unavailable. Please try again later or
                contact support.
              </div>
            )}

            <button
              type="button"
              className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-[var(--accent)] px-5 py-3.5 text-sm font-semibold text-white shadow-sm transition hover:bg-[var(--accent-hover)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--accent)] disabled:cursor-not-allowed disabled:opacity-50"
              disabled={busy || !oidcReady}
              onClick={() => void onSignIn()}
            >
              {busy ? 'Please wait…' : 'Sign in'}
              {!busy && <ArrowRight size={16} aria-hidden="true" />}
            </button>

            <div className="mt-6 flex items-start gap-3 rounded-xl bg-[var(--panel-2)] px-4 py-3">
              <span className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-lg bg-[var(--accent-soft)] text-[var(--accent)]">
                <ShieldCheck size={16} strokeWidth={1.9} aria-hidden="true" />
              </span>
              <p className="m-0 text-xs leading-5 text-[var(--muted)]">
                Your account is protected with secure sign-in. NetPay never asks
                for your password on this page.
              </p>
            </div>
          </div>

          <p className="mt-8 text-center text-xs text-[var(--muted)]">
            New here?{' '}
            <Link className="font-medium text-[var(--accent)]" to="/">
              Learn about NetPay
            </Link>
          </p>
        </div>
      </div>

      <footer className="border-t border-[var(--border)] bg-[var(--panel)]">
        <div className="mx-auto flex w-full max-w-7xl flex-col gap-2 px-5 py-5 text-xs text-[var(--muted)] sm:flex-row sm:items-center sm:justify-between sm:px-8 lg:px-10">
          <Link
            className="font-semibold text-[var(--text)] no-underline hover:no-underline"
            to="/"
          >
            NetPay
          </Link>
          <span>Payment collection for modern businesses.</span>
        </div>
      </footer>
    </main>
  )
}
