export const THEME_STORAGE_KEY = "netpay_theme";
export const THEMES = ["harbor", "ink", "signal"] as const;
export type ThemeId = (typeof THEMES)[number];

export const THEME_META: Record<
  ThemeId,
  { name: string; tagline: string; swatches: string[] }
> = {
  harbor: {
    name: "Harbor",
    tagline: "Deep navy chrome, classic teal signal",
    swatches: ["#101b2d", "#20b89a", "#eef2f6", "#0f172a", "#f1f5f9"],
  },
  ink: {
    name: "Ink",
    tagline: "Ink navy + signal teal — higher contrast",
    swatches: ["#0b1220", "#12b89a", "#eef2f6", "#0f172a", "#f1f5f9"],
  },
  signal: {
    name: "Signal",
    tagline: "Teal-forward, softer navy — brighter energy",
    swatches: ["#0f2a32", "#14c4a5", "#eef8f5", "#10242a", "#f0fdfa"],
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
