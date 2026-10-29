"use client";

import { useState } from "react";
import Link from "next/link";
import { Menu, X } from "lucide-react";
import { Button } from "./ui";

const links = [
  { href: "/product/", label: "Product" },
  { href: "/developers/", label: "Developers" },
  { href: "/why-netpay/", label: "Why NetPay" },
  { href: "/api-overview/", label: "Resources" },
];

/** Solid navy public header with mobile menu. */
export function SiteHeader() {
  const [open, setOpen] = useState(false);

  return (
    <header className="border-b border-[var(--header-border)] bg-[var(--navy)] text-[var(--on-navy)]">
      <nav
        className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5 lg:px-8"
        aria-label="Main navigation"
      >
        <Link href="/" className="flex items-center gap-3" aria-label="NetPay home">
          <span className="grid size-10 place-items-center rounded-xl bg-[var(--accent)] text-[length:var(--text-lg)] font-[number:var(--weight-black)] text-[var(--on-accent)]">
            N
          </span>
          <span className="text-[length:var(--text-xl)] font-[number:var(--weight-bold)] tracking-[var(--tracking-tight)]">NetPay</span>
        </Link>

        <div className="hidden items-center gap-8 text-[length:var(--text-sm)] text-[var(--on-navy-muted)] md:flex">
          {links.map((l) => (
            <Link key={l.href} href={l.href} className="transition hover:text-[var(--on-navy)]">
              {l.label}
            </Link>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <Button href="/request-access/" variant="onNavy" size="sm" className="hidden sm:inline-flex">
            Get started
          </Button>
          <button
            type="button"
            className="inline-flex size-10 items-center justify-center rounded-xl border border-[var(--on-navy-border)] text-[var(--on-navy)] md:hidden"
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
        <div id="mobile-nav" className="border-t border-[var(--header-border)] px-6 py-4 md:hidden">
          <ul className="flex flex-col gap-1">
            {links.map((l) => (
              <li key={l.href}>
                <Link
                  href={l.href}
                  className="block rounded-xl px-3 py-3 text-[length:var(--text-sm)] font-[number:var(--weight-semibold)] text-[var(--on-navy)] hover:bg-[var(--on-navy-faint)]"
                  onClick={() => setOpen(false)}
                >
                  {l.label}
                </Link>
              </li>
            ))}
            <li className="pt-2">
              <Button href="/request-access/" variant="onNavy" size="md" className="w-full">
                Request access
              </Button>
            </li>
          </ul>
        </div>
      )}
    </header>
  );
}
