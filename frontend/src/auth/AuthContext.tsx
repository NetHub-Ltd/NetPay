import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { api, getToken, setToken, type User } from '../api/client'
import { logoutAtKeycloak, setRefreshToken } from './oidc'

type AuthState = {
  user: User | null
  loading: boolean
  loginWithToken: (accessToken: string) => Promise<void>
  logout: () => void
  isAdmin: boolean
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const loadMe = useCallback(async () => {
    const token = getToken()
    if (!token) {
      setUser(null)
      setLoading(false)
      return
    }
    try {
      // NetPay GET /auth/me → forwards token to NetHub (sync on first use)
      const me = await api.get<User>('/auth/me')
      setUser(me)
    } catch {
      setToken(null)
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadMe()
  }, [loadMe])

  const loginWithToken = useCallback(async (accessToken: string) => {
    setToken(accessToken)
    const me = await api.get<User>('/auth/me')
    setUser(me)
  }, [])

  const logout = useCallback(() => {
    const idToken = sessionStorage.getItem('nethub_id_token')
    setToken(null)
    setRefreshToken(null)
    sessionStorage.removeItem('nethub_id_token')
    setUser(null)
    logoutAtKeycloak(idToken)
  }, [])

  const value = useMemo(
    () => ({
      user,
      loading,
      loginWithToken,
      logout,
      isAdmin: user?.role === 'admin',
    }),
    [user, loading, loginWithToken, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth outside provider')
  return ctx
}
