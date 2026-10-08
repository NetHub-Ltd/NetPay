import { useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { ArrowRight, Landmark, ShieldCheck } from 'lucide-react'
import { useAuth } from '../auth/authState'
import { Button } from '../components/primitives'
import { DismissibleBanner } from '../components/DismissibleBanner'

export function Login() {
  const { user, login, loading, oidcReady } = useAuth()
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  if (loading) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center bg-[var(--bg)] px-5">
        <div className="text-center">
          <div className="mx-auto mb-4 flex size-12 items-center justify-center rounded-2xl bg-gradient-to-br from-[var(--hero-from)] via-[var(--hero-via)] to-[var(--hero-to)] text-[var(--on-hero)]">
            <Landmark size={22} aria-hidden />
          </div>
          <p className="m-0 text-sm text-[var(--muted)]">Loading NetPay…</p>
        </div>
      </main>
    )
  }
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
      <header className="mx-auto flex w-full max-w-7xl items-center justify-between px-5 py-5 sm:px-8">
        <Link className="flex items-center gap-2.5 no-underline hover:no-underline" to="/">
          <span className="flex size-9 items-center justify-center rounded-xl bg-gradient-to-br from-[var(--hero-from)] via-[var(--hero-via)] to-[var(--hero-to)] text-[var(--on-hero)] shadow-sm">
            <Landmark size={18} strokeWidth={1.9} aria-hidden />
          </span>
          <span className="text-base font-bold tracking-tight">NetPay</span>
        </Link>
        <Link className="text-sm font-medium text-[var(--muted)] no-underline hover:text-[var(--text)]" to="/">
          Home
        </Link>
      </header>

      <div className="mx-auto flex w-full max-w-7xl flex-1 flex-col justify-center px-5 pb-16 pt-6 sm:px-8 lg:flex-row lg:items-center lg:gap-16">
        <div className="mb-10 max-w-md lg:mb-0 lg:flex-1">
          <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-[var(--accent)]">
            Secure sign-in
          </p>
          <h1 className="m-0 text-3xl font-semibold tracking-tight sm:text-4xl">
            Continue to your payments workspace
          </h1>
          <p className="mt-4 text-sm leading-6 text-[var(--muted)] sm:text-base">
            Sign in with your NetHub account to collect payments, connect shortcodes, and manage
            what happens after money moves.
          </p>
        </div>

        <div className="w-full max-w-md lg:flex-1">
          <div className="rounded-2xl border border-[var(--border)] bg-[var(--panel)] p-6 shadow-[var(--shadow)] sm:p-8">
            <h2 className="m-0 text-lg font-bold">Sign in to NetPay</h2>
            <p className="mb-6 mt-1 text-sm text-[var(--muted)]">
              You’ll be taken to NetHub to verify it’s you — we never ask for your password here.
            </p>

            {error && (
              <DismissibleBanner tone="error" onDismiss={() => setError(null)}>
                {error}
              </DismissibleBanner>
            )}
            {!oidcReady && (
              <DismissibleBanner tone="error">
                Sign-in is temporarily unavailable. Please try again in a moment.
              </DismissibleBanner>
            )}

            <Button
              className="w-full"
              size="lg"
              loading={busy}
              disabled={!oidcReady}
              onClick={() => void onSignIn()}
              rightIcon={!busy ? <ArrowRight size={16} aria-hidden /> : undefined}
            >
              {busy ? 'Redirecting…' : 'Continue with NetHub'}
            </Button>

            <div className="mt-6 flex items-start gap-3 rounded-xl bg-[var(--panel-2)] px-4 py-3">
              <span className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-lg bg-[var(--accent-soft)] text-[var(--accent)]">
                <ShieldCheck size={16} strokeWidth={1.9} aria-hidden />
              </span>
              <p className="m-0 text-xs leading-5 text-[var(--muted)]">
                Protected by organization sign-in. After you sign out, you’ll return to NetPay
                ready to sign in again.
              </p>
            </div>
          </div>

          <p className="mt-6 text-center text-xs text-[var(--muted)]">
            New here?{' '}
            <Link className="font-medium text-[var(--accent)]" to="/">
              Learn about NetPay
            </Link>
          </p>
        </div>
      </div>

      <footer className="border-t border-[var(--border)] bg-[var(--panel)]">
        <div className="mx-auto flex w-full max-w-7xl flex-col gap-2 px-5 py-5 text-xs text-[var(--muted)] sm:flex-row sm:items-center sm:justify-between sm:px-8">
          <Link className="font-semibold text-[var(--text)] no-underline" to="/">
            NetPay
          </Link>
          <span>Payment collection for modern businesses.</span>
        </div>
      </footer>
    </main>
  )
}
