/** Theme ids. Product default is Ledger — see Theme.md */
export const THEME_STORAGE_KEY = "netpay_theme";
export const PRODUCT_THEME = "ledger" as const;
export const THEMES = ["ledger", "harbor", "shamba"] as const;
export type ThemeId = (typeof THEMES)[number];

export const THEME_META: Record<
  ThemeId,
  { name: string; tagline: string; swatches: string[]; productDefault?: boolean }
> = {
  ledger: {
    name: "Ledger",
    tagline: "Indigo + sky blue — product default",
    swatches: ["#1e1b4b", "#3b82f6", "#f4f2f8", "#1e1b2e", "#f5f3ff"],
    productDefault: true,
  },
  harbor: {
    name: "Harbor",
    tagline: "Navy + teal — lab alternative only",
    swatches: ["#0b1220", "#0d9f86", "#eef1f6", "#0f172a", "#f1f5f9"],
  },
  shamba: {
    name: "Shamba",
    tagline: "Forest + gold — lab alternative only",
    swatches: ["#0c2f24", "#c4a035", "#f3f6f2", "#14241e", "#f3faf6"],
  },
};

export function isThemeId(value: string | null | undefined): value is ThemeId {
  return THEMES.includes(value as ThemeId);
}

export function getStoredTheme(): ThemeId {
  if (typeof window === "undefined") return PRODUCT_THEME;
  try {
    const raw = window.localStorage.getItem(THEME_STORAGE_KEY);
    if (isThemeId(raw)) return raw;
    if (raw === "ink" || raw === "signal") return PRODUCT_THEME;
  } catch {
    /* ignore */
  }
  return PRODUCT_THEME;
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
