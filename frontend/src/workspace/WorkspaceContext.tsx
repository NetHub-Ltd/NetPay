/* oxlint-disable react/only-export-components -- context module */
import {
  createContext,
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { api, type Tenant } from '../api/client'
import { useAuth } from '../auth/authState'

/** Set only when the user explicitly chooses a business (or resumes a stored choice). */
const STORAGE_KEY = 'netpay_active_tenant_id'

type WorkspaceCtx = {
  businesses: Tenant[]
  loading: boolean
  activeTenantId: string | null
  activeBusiness: Tenant | null
  setActiveTenantId: (id: string | null) => void
  clearActiveTenant: () => void
  refreshBusinesses: () => Promise<Tenant[]>
  needsSelection: boolean
}

export const WorkspaceContext = createContext<WorkspaceCtx | null>(null)

function readStored(): string | null {
  try {
    return sessionStorage.getItem(STORAGE_KEY)
  } catch {
    return null
  }
}

function writeStored(id: string | null) {
  try {
    if (id) sessionStorage.setItem(STORAGE_KEY, id)
    else sessionStorage.removeItem(STORAGE_KEY)
  } catch {
    /* ignore */
  }
}

/** Export for logout — clear workspace with auth tokens. */
export function clearStoredWorkspace() {
  writeStored(null)
}

/**
 * Only keep a previously explicit selection if it still exists.
 * Do NOT auto-pick single business or NetHub primary tenant on login.
 */
function restoreIfValid(list: Tenant[], prev: string | null): string | null {
  const stored = prev || readStored()
  if (stored && list.some((b) => b.id === stored)) {
    writeStored(stored)
    return stored
  }
  writeStored(null)
  return null
}

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const { user, loading: authLoading } = useAuth()
  const [businesses, setBusinesses] = useState<Tenant[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTenantId, setActiveId] = useState<string | null>(() => readStored())

  const refreshBusinesses = useCallback(async () => {
    if (!user) {
      setBusinesses([])
      setLoading(false)
      return []
    }
    try {
      const list = await api.get<Tenant[]>('/v1/tenants')
      setBusinesses(list)
      setActiveId((prev) => restoreIfValid(list, prev))
      return list
    } catch {
      setBusinesses([])
      return []
    } finally {
      setLoading(false)
    }
  }, [user])

  useEffect(() => {
    if (authLoading) return
    let cancelled = false
    void (async () => {
      if (!user) {
        if (!cancelled) {
          setBusinesses([])
          setActiveId(null)
          writeStored(null)
          setLoading(false)
        }
        return
      }
      if (!cancelled) await refreshBusinesses()
    })()
    return () => {
      cancelled = true
    }
  }, [user, authLoading, refreshBusinesses])

  const setActiveTenantId = useCallback((id: string | null) => {
    writeStored(id)
    setActiveId(id)
  }, [])

  const clearActiveTenant = useCallback(() => {
    writeStored(null)
    setActiveId(null)
  }, [])

  const activeBusiness = useMemo(
    () => businesses.find((b) => b.id === activeTenantId) || null,
    [businesses, activeTenantId],
  )

  const needsSelection = Boolean(user) && !loading && !activeTenantId

  const value = useMemo(
    () => ({
      businesses,
      loading: authLoading || loading,
      activeTenantId,
      activeBusiness,
      setActiveTenantId,
      clearActiveTenant,
      refreshBusinesses,
      needsSelection,
    }),
    [
      businesses,
      authLoading,
      loading,
      activeTenantId,
      activeBusiness,
      setActiveTenantId,
      clearActiveTenant,
      refreshBusinesses,
      needsSelection,
    ],
  )

  return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>
}
