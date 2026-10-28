export const THEME_STORAGE_KEY = "netpay_theme";
export const THEMES = ["harbor", "shamba", "ledger"] as const;
export type ThemeId = (typeof THEMES)[number];

export const THEME_META: Record<
  ThemeId,
  { name: string; tagline: string; swatches: string[] }
> = {
  harbor: {
    name: "Harbor",
    tagline: "Navy + teal — cool infrastructure",
    swatches: ["#0b1220", "#0d9f86", "#eef1f6", "#0f172a", "#f1f5f9"],
  },
  shamba: {
    name: "Shamba",
    tagline: "Forest + harvest gold — grounded regional",
    swatches: ["#0c2f24", "#c4a035", "#f3f6f2", "#14241e", "#f3faf6"],
  },
  ledger: {
    name: "Ledger",
    tagline: "Indigo + sky blue — modern fintech",
    swatches: ["#1e1b4b", "#3b82f6", "#f4f2f8", "#1e1b2e", "#f5f3ff"],
  },
};

export function isThemeId(value: string | null | undefined): value is ThemeId {
  return THEMES.includes(value as ThemeId);
}

export function getStoredTheme(): ThemeId {
  if (typeof window === "undefined") return "harbor";
  try {
    const raw = window.localStorage.getItem(THEME_STORAGE_KEY);
    if (isThemeId(raw)) return raw;
    // migrate old ids
    if (raw === "ink" || raw === "signal") return "harbor";
  } catch {
    /* ignore */
  }
  return "harbor";
}

export function applyTheme(theme: ThemeId) {
  if (typeof document === "undefined") return;
  document.documentElement.setAttribute("data-theme", theme);
  try {
    window.localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch {
    /* ignore */
  }
}
