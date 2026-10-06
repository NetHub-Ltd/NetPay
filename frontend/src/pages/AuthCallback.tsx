import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Landmark } from 'lucide-react'
import { useAuth } from '../auth/authState'
import { completeLogin } from '../auth/oidc'
import { Button } from '../components/primitives'

export function AuthCallback() {
  const navigate = useNavigate()
  const { establishSession } = useAuth()
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const params = new URLSearchParams(window.location.search)
        const { tokens, returnTo } = await completeLogin(params)
        await establishSession(tokens.access_token, tokens.id_token)
        if (!cancelled) {
          const dest =
            returnTo && returnTo !== '/dashboard' && returnTo !== '/'
              ? returnTo
              : '/select-business'
          navigate(dest, { replace: true })
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Sign-in failed')
      }
    })()
    return () => {
      cancelled = true
    }
  }, [navigate, establishSession])

  if (error) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center bg-[var(--bg)] px-5 text-[var(--text)]">
        <div className="w-full max-w-md rounded-2xl border border-[var(--border)] bg-[var(--panel)] p-8 text-center shadow-[var(--shadow)]">
          <h1 className="m-0 text-xl font-semibold">Sign-in didn’t complete</h1>
          <p className="mt-3 text-sm leading-6 text-[var(--muted)]">{error}</p>
          <p className="mt-2 text-xs text-[var(--muted)]">
            You can try again. If this keeps happening, check that this app is allowed in your
            organization sign-in settings.
          </p>
          <Link to="/login" className="mt-6 inline-block no-underline">
            <Button>Back to sign in</Button>
          </Link>
        </div>
      </main>
    )
  }

  return (
    <main
      className="flex min-h-screen flex-col items-center justify-center bg-[var(--bg)] px-5 text-[var(--text)]"
      data-testid="auth-callback-page"
    >
      <div className="w-full max-w-sm text-center">
        <div className="mx-auto mb-5 flex size-14 items-center justify-center rounded-2xl bg-gradient-to-br from-[var(--hero-from)] via-[var(--hero-via)] to-[var(--hero-to)] text-[var(--on-hero)] shadow-[var(--shadow)]">
          <Landmark size={26} strokeWidth={1.75} aria-hidden />
        </div>
        <h1 className="m-0 text-lg font-semibold tracking-tight">Signing you in</h1>
        <p className="mb-6 mt-2 text-sm leading-6 text-[var(--muted)]">
          Confirming your account with NetHub. This only takes a moment.
        </p>
        <div
          className="mx-auto h-1.5 w-40 overflow-hidden rounded-full bg-[var(--border)]"
          role="progressbar"
          aria-label="Signing in"
        >
          <div className="h-full w-1/2 animate-pulse rounded-full bg-[var(--accent)]" />
        </div>
      </div>
    </main>
  )
}
