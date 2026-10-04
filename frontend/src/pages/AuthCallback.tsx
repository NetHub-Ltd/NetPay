import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { applyAccessToken } from '../auth/AuthContext'
import { completeLogin } from '../auth/oidc'

/**
 * OIDC redirect target. Exchanges code+PKCE for tokens, then loads NetHub profile
 * via NetPay /auth/me.
 */
export function AuthCallback() {
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const params = new URLSearchParams(window.location.search)
        const { tokens, returnTo } = await completeLogin(params)
        await applyAccessToken(tokens.access_token, tokens.id_token)
        if (!cancelled) {
          navigate(returnTo || '/', { replace: true })
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
  }, [navigate])

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[var(--bg)]" style={{ padding: '2rem', maxWidth: 480, margin: '0 auto' }}>
        <h1>Sign-in failed</h1>
        <p className="text-[var(--muted)]">{error}</p>
        <a className="inline-flex items-center justify-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--panel)] px-3 py-2 text-sm font-medium text-[var(--text)] no-underline shadow-[var(--shadow)]" href="/login">
          Try again
        </a>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--bg)]">
      <p className="text-[var(--muted)]">Completing sign-in…</p>
    </div>
  )
}
