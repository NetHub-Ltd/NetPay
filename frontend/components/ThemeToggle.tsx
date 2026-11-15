"use client";

import { isThemeId, applyTheme, getStoredTheme } from "../lib/theme";
import { Moon, Sun } from "lucide-react";

export function ThemeToggle() {
  function toggleTheme() {
    const storedTheme = document.documentElement.dataset.theme;
    const currentTheme = isThemeId(storedTheme) ? storedTheme : getStoredTheme();
    applyTheme(currentTheme === "light" ? "dark" : "light");
  }

  return (
    <button
      type="button"
      className="inline-flex size-10 shrink-0 items-center justify-center rounded-xl border border-[var(--on-navy-border)] text-[var(--on-navy)] transition hover:bg-[var(--on-navy-faint)] focus-visible:outline-[var(--focus-ring)]"
      aria-label="Switch between light and dark themes"
      title="Switch between light and dark themes"
      onClick={toggleTheme}
    >
      <span className="np-theme-icon-dark" aria-hidden="true"><Moon size={18} /></span>
      <span className="np-theme-icon-light" aria-hidden="true"><Sun size={18} /></span>
    </button>
  );
}
