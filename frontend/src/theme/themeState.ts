import { createContext, useContext } from 'react'

/** Light-only for now — dark theme removed from product UI. */
export type ThemeMode = 'light'

type ThemeCtx = {
  theme: ThemeMode
}

export const Ctx = createContext<ThemeCtx | null>(null)

export function useTheme() {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useTheme outside ThemeProvider')
  return ctx
}
