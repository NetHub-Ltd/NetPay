import { useEffect, useMemo, type ReactNode } from 'react'
import { Ctx } from './themeState'

export function ThemeProvider({ children }: { children: ReactNode }) {
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', 'light')
    document.documentElement.classList.remove('dark')
    try {
      localStorage.removeItem('nethub_theme')
    } catch {
      /* ignore */
    }
  }, [])

  const value = useMemo(() => ({ theme: 'light' as const }), [])

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}
