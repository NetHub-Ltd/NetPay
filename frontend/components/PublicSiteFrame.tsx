import type { ReactNode } from "react";
import { SiteHeader } from "./SiteHeader";
import { SiteFooter } from "./SiteFooter";

/** Shared site frame; theme tokens apply consistently to public and authenticated pages. */
export function PublicSiteFrame({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--ink)]">
      <a href="#main-content" className="np-skip-link">Skip to content</a>
      <SiteHeader />
      {children}
      <SiteFooter />
    </div>
  );
}
