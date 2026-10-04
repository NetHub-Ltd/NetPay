import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/authState'
import { completeLogin } from '../auth/oidc'
import { Button, PageLoader } from '../components/primitives'

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
        if (!cancelled) navigate(returnTo || '/dashboard', { replace: true })
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
      <div className="mx-auto flex min-h-screen max-w-[480px] flex-col items-start justify-center gap-4 bg-[var(--bg)] p-8">
        <h1 className="m-0 text-2xl font-semibold">Sign-in failed</h1>
        <p className="m-0 text-sm text-[var(--muted)]">{error}</p>
        <Link to="/login" className="no-underline">
          <Button variant="secondary">Try again</Button>
        </Link>
      </div>
    )
  }

  return <PageLoader label="Signing you in…" />
}
