import { createContext, useContext } from 'react'

export type ThemeMode = 'light' | 'dark'

type ThemeCtx = {
  theme: ThemeMode
  setTheme: (t: ThemeMode) => void
  toggle: () => void
}

export const Ctx = createContext<ThemeCtx | null>(null)

export function useTheme() {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useTheme outside ThemeProvider')
  return ctx
}
