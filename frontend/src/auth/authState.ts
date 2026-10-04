import { createContext, useContext } from 'react'
import type { User } from '../api/client'

export type AuthState = {
  user: User | null
  loading: boolean
  /** Start Zitadel browser login (redirect). */
  login: () => Promise<void>
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
