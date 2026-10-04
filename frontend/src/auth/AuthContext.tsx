import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { api, clearSessionTokens, getToken, type User } from '../api/client'
import { beginLogin, beginLogout, getIdTokenFromStorage, isOidcConfigured } from './oidcBridge'
import { AuthContext } from './authState'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(() => Boolean(getToken()))
  const oidcReady = isOidcConfigured()

  const refresh = useCallback(async () => {
    const token = getToken()
    if (!token) return
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
    await beginLogin('/')
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
      logout,
      isAdmin: user?.role === 'admin',
      oidcReady,
    }),
    [user, loading, login, logout, oidcReady],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
