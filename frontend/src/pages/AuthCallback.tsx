import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/authState'
import { completeLogin } from '../auth/oidc'

/**
 * OIDC redirect target. Exchanges code+PKCE for tokens, establishes session, then dashboard.
 */
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
          navigate(returnTo || '/dashboard', { replace: true })
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : 'Sign-in failed')
        }
      }
    })()
    return () => {
      cancelled = true
    }
  }, [navigate, establishSession])

  if (error) {
    return (
      <div className="mx-auto flex min-h-screen max-w-[480px] flex-col items-start justify-center gap-3 bg-[var(--bg)] p-8">
        <h1 className="m-0 text-2xl font-semibold">Sign-in failed</h1>
        <p className="m-0 text-sm text-[var(--muted)]">{error}</p>
        <Link
          className="inline-flex items-center justify-center gap-2 rounded-xl border border-[var(--border)] bg-[var(--panel)] px-4 py-2.5 text-sm font-medium text-[var(--text)] no-underline shadow-sm"
          to="/login"
        >
          Try again
        </Link>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--bg)]">
      <p className="text-sm text-[var(--muted)]">Signing you in…</p>
    </div>
  )
}
