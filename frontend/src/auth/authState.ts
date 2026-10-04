import { createContext, useContext } from 'react'
import type { User } from '../api/client'

export type AuthState = {
  user: User | null
  loading: boolean
  /** Start browser login (redirect). */
  login: () => Promise<void>
  /** Persist tokens, load /auth/me, set user (used by OIDC callback). */
  establishSession: (accessToken: string, idToken?: string) => Promise<User>
  logout: () => void
  isAdmin: boolean
  oidcReady: boolean
}

export const AuthContext = createContext<AuthState | null>(null)

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth outside AuthProvider')
  return ctx
}
