"use client";

import { useState } from "react";
import Link from "next/link";
import { Menu, X } from "lucide-react";
import { Button } from "./ui";

const links = [
  { href: "#capabilities", label: "Capabilities" },
  { href: "#how-it-works", label: "How it works" },
  { href: "#developers", label: "Developers" },
];

/** Solid navy public header with mobile menu (P6). */
export function SiteHeader() {
  const [open, setOpen] = useState(false);

  return (
    <header className="border-b border-white/10 bg-[var(--navy)] text-[var(--on-navy)]">
      <nav
        className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5 lg:px-8"
        aria-label="Main navigation"
      >
        <Link href="/" className="flex items-center gap-3" aria-label="NetPay home">
          <span className="grid size-10 place-items-center rounded-xl bg-[var(--teal)] text-lg font-black text-[var(--navy)]">
            N
          </span>
          <span className="text-xl font-bold tracking-tight">NetPay</span>
        </Link>

        <div className="hidden items-center gap-8 text-sm text-[var(--on-navy-muted)] md:flex">
          {links.map((l) => (
            <a key={l.href} href={l.href} className="transition hover:text-[var(--on-navy)]">
              {l.label}
            </a>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <Button href="/dashboard/" variant="onNavyOutline" size="sm" className="hidden sm:inline-flex">
            Dashboard
          </Button>
          <button
            type="button"
            className="inline-flex size-10 items-center justify-center rounded-xl border border-white/20 text-[var(--on-navy)] md:hidden"
            aria-expanded={open}
            aria-controls="mobile-nav"
            aria-label={open ? "Close menu" : "Open menu"}
            onClick={() => setOpen((v) => !v)}
          >
            {open ? <X size={20} aria-hidden /> : <Menu size={20} aria-hidden />}
          </button>
        </div>
      </nav>

      {open && (
        <div
          id="mobile-nav"
          className="border-t border-white/10 px-6 py-4 md:hidden"
        >
          <ul className="flex flex-col gap-1">
            {links.map((l) => (
              <li key={l.href}>
                <a
                  href={l.href}
                  className="block rounded-xl px-3 py-3 text-sm font-semibold text-[var(--on-navy)] hover:bg-white/5"
                  onClick={() => setOpen(false)}
                >
                  {l.label}
                </a>
              </li>
            ))}
            <li className="pt-2">
              <Button href="/dashboard/" variant="onNavy" size="md" className="w-full">
                Dashboard preview
              </Button>
            </li>
          </ul>
        </div>
      )}
    </header>
  );
}
