import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import {
  api,
  clearSessionTokens,
  getToken,
  setIdToken,
  setToken,
  type User,
} from '../api/client'
import { beginLogin, beginLogout, getIdTokenFromStorage, isOidcConfigured } from './oidcBridge'

type AuthState = {
  user: User | null
  loading: boolean
  /** Start Zitadel browser login (redirect). */
  login: () => Promise<void>
  logout: () => void
  isAdmin: boolean
  oidcReady: boolean
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const oidcReady = isOidcConfigured()

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
    void refresh()
  }, [refresh])

  const login = useCallback(async () => {
    await beginLogin('/')
  }, [])

  const logout = useCallback(() => {
    const idToken = getIdTokenFromStorage()
    clearSessionTokens()
    setUser(null)
    beginLogout(idToken)
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

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth outside AuthProvider')
  return ctx
}

/** Called from /auth/callback after token exchange. */
export async function applyAccessToken(
  accessToken: string,
  idToken?: string,
): Promise<User> {
  setToken(accessToken)
  if (idToken) setIdToken(idToken)
  return api.get<User>('/auth/me')
}
