import { useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { ArrowRight, Landmark, ShieldCheck } from 'lucide-react'
import { useAuth } from '../auth/authState'
import { Button, PageLoader } from '../components/primitives'

export function Login() {
  const { user, login, loading, oidcReady } = useAuth()
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  if (loading) return <PageLoader label="Loading…" />
  if (user) return <Navigate to="/select-business" replace />

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
      <header className="mx-auto flex w-full max-w-7xl items-center justify-between px-5 py-5 sm:px-8 lg:px-10">
        <Link
          className="flex items-center gap-2.5 no-underline hover:no-underline"
          to="/"
          aria-label="NetPay home"
        >
          <span className="flex size-10 items-center justify-center rounded-xl bg-[var(--accent)] text-white shadow-sm">
            <Landmark size={21} strokeWidth={1.9} aria-hidden />
          </span>
          <span className="text-lg font-bold tracking-tight">NetPay</span>
        </Link>
        <Link
          className="rounded-xl px-4 py-2.5 text-sm font-semibold text-[var(--muted)] transition hover:bg-[var(--panel-2)] hover:text-[var(--text)]"
          to="/"
        >
          Home
        </Link>
      </header>

      <div className="relative flex flex-1 flex-col items-center justify-center px-5 pb-16 pt-4 sm:px-8">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-x-0 top-0 h-72 bg-[var(--hero-bg)] opacity-[0.1] blur-3xl"
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
                Sign-in is temporarily unavailable. Please try again later.
              </div>
            )}

            <Button
              className="w-full"
              size="lg"
              loading={busy}
              disabled={!oidcReady}
              onClick={() => void onSignIn()}
              rightIcon={!busy ? <ArrowRight size={16} aria-hidden /> : undefined}
            >
              {busy ? 'Please wait…' : 'Sign in'}
            </Button>

            <div className="mt-6 flex items-start gap-3 rounded-xl bg-[var(--panel-2)] px-4 py-3">
              <span className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-lg bg-[var(--accent-soft)] text-[var(--accent)]">
                <ShieldCheck size={16} strokeWidth={1.9} aria-hidden />
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
          <Link className="font-semibold text-[var(--text)] no-underline hover:no-underline" to="/">
            NetPay
          </Link>
          <span>Payment collection for modern businesses.</span>
        </div>
      </footer>
    </main>
  )
}
