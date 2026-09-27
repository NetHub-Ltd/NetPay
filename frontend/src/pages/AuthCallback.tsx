import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { exchangeCode, getReturnTo, setRefreshToken } from '../auth/oidc'
import { setToken } from '../api/client'

/**
 * OIDC redirect target: ?code=&state=
 * Exchange code → store access token → AuthContext loads /auth/me (NetPay→NetHub).
 */
export default function AuthCallback() {
  const navigate = useNavigate()
  const { loginWithToken } = useAuth()
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    async function run() {
      const params = new URLSearchParams(window.location.search)
      const code = params.get('code')
      const state = params.get('state')
      const err = params.get('error')
      const errDesc = params.get('error_description')

      if (err) {
        setError(errDesc || err)
        return
      }
      if (!code || !state) {
        setError('Missing authorization code. Start again from Sign in.')
        return
      }

      try {
        const tokens = await exchangeCode(code, state)
        if (cancelled) return
        setToken(tokens.access_token)
        if (tokens.refresh_token) setRefreshToken(tokens.refresh_token)
        if (tokens.id_token) sessionStorage.setItem('nethub_id_token', tokens.id_token)
        await loginWithToken(tokens.access_token)
        if (cancelled) return
        navigate(getReturnTo(), { replace: true })
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Sign-in failed')
      }
    }
    void run()
    return () => {
      cancelled = true
    }
  }, [loginWithToken, navigate])

  return (
    <div className="login-page" style={{ padding: '3rem 1.5rem', textAlign: 'center' }}>
      {error ? (
        <>
          <div className="alert error" style={{ maxWidth: 480, margin: '0 auto 1rem' }}>
            {error}
          </div>
          <a className="btn primary" href="/login">
            Try again
          </a>
        </>
      ) : (
        <p className="muted">Completing sign-in…</p>
      )}
    </div>
  )
}
