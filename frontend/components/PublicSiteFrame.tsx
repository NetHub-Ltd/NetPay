import type { ReactNode } from "react";
import { SiteHeader } from "./SiteHeader";
import { SiteFooter } from "./SiteFooter";

/** Public marketing frame; scoped tokens intentionally do not restyle the dashboard. */
export function PublicSiteFrame({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <div className="np-public-site min-h-screen bg-[var(--bg)] text-[var(--ink)]">
      <a href="#main-content" className="np-skip-link">Skip to content</a>
      <SiteHeader />
      {children}
      <SiteFooter />
    </div>
  );
}
