import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { api, clearSessionTokens, getToken, type User } from '../api/client'
import {
  beginLogin,
  beginLogout,
  ensureOidcConfig,
  getIdTokenFromStorage,
} from './oidcBridge'
import { AuthContext } from './authState'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(() => Boolean(getToken()))
  const [oidcReady, setOidcReady] = useState(false)
  const [oidcChecked, setOidcChecked] = useState(false)

  useEffect(() => {
    let cancelled = false
    void ensureOidcConfig().then((cfg) => {
      if (!cancelled) {
        setOidcReady(cfg !== null)
        setOidcChecked(true)
      }
    })
    return () => {
      cancelled = true
    }
  }, [])

  const refresh = useCallback(async () => {
    const token = getToken()
    if (!token) {
      setLoading(false)
      return
    }
    try {
      const me = await api.get<User>('/auth/me')
      setUser(me)
    } catch {
      clearSessionTokens()
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void Promise.resolve().then(refresh)
  }, [refresh])

  const login = useCallback(async () => {
    await ensureOidcConfig()
    await beginLogin('/dashboard')
  }, [])

  const logout = useCallback(() => {
    const idToken = getIdTokenFromStorage()
    clearSessionTokens()
    setUser(null)
    void beginLogout(idToken)
  }, [])

  const value = useMemo(
    () => ({
      user,
      loading: loading || !oidcChecked,
      login,
      logout,
      isAdmin: user?.role === 'admin',
      oidcReady,
    }),
    [user, loading, login, logout, oidcReady, oidcChecked],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
