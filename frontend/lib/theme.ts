export const THEME_STORAGE_KEY = "netpay_theme";
export const PRODUCT_THEME = "light" as const;
export const THEMES = ["light", "dark"] as const;
export type ThemeId = (typeof THEMES)[number];

export const THEME_INIT_SCRIPT = `(function(){try{var k=${JSON.stringify(THEME_STORAGE_KEY)};var t=localStorage.getItem(k);if(t==='light'||t==='dark'){document.documentElement.setAttribute('data-theme',t);}else{document.documentElement.setAttribute('data-theme','light');}}catch(e){document.documentElement.setAttribute('data-theme','light');}})();`;

export function isThemeId(value: string | null | undefined): value is ThemeId {
  return value === "light" || value === "dark";
}

export function getStoredTheme(): ThemeId {
  if (typeof window === "undefined") return PRODUCT_THEME;
  try {
    const raw = window.localStorage.getItem(THEME_STORAGE_KEY);
    if (isThemeId(raw)) return raw;
  } catch {
    return PRODUCT_THEME;
  }
  return PRODUCT_THEME;
}

export function applyTheme(theme: ThemeId): void {
  if (typeof document === "undefined") return;
  document.documentElement.setAttribute("data-theme", theme);
  try {
    window.localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch {
    // Theme changes still apply when browser storage is unavailable.
  }
}
