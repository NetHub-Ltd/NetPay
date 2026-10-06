import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { api, clearSessionTokens, getToken, type User } from '../api/client'
import { applyAccessToken } from './authToken'
import {
  beginLogin,
  beginLogout,
  ensureOidcConfig,
  getIdTokenFromStorage,
} from './oidcBridge'
import { AuthContext } from './authState'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [oidcReady, setOidcReady] = useState(false)

  useEffect(() => {
    let cancelled = false
    void ensureOidcConfig().then((cfg) => {
      if (!cancelled) setOidcReady(cfg !== null)
    })
    return () => {
      cancelled = true
    }
  }, [])

  const refresh = useCallback(async () => {
    const token = getToken()
    if (!token) {
      setUser(null)
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

  const establishSession = useCallback(
    async (accessToken: string, idToken?: string) => {
      setLoading(true)
      try {
        const me = await applyAccessToken(accessToken, idToken)
        setUser(me)
        return me
      } catch (e) {
        clearSessionTokens()
        setUser(null)
        throw e
      } finally {
        setLoading(false)
      }
    },
    [],
  )

  const login = useCallback(async () => {
    await ensureOidcConfig()
    await beginLogin('/select-business')
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
      loading,
      login,
      establishSession,
      logout,
      isAdmin: user?.role === 'admin',
      oidcReady,
    }),
    [user, loading, login, establishSession, logout, oidcReady],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
