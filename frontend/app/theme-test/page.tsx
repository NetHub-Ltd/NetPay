import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, CheckCircle2 } from "lucide-react";
import { PublicSiteFrame } from "../../components/PublicSiteFrame";
import { Badge, Button, Card, Section } from "../../components/ui";

export const metadata: Metadata = {
  title: "Theme preview",
  description: "Private visual preview of NetPay's shared light and dark theme system.",
  robots: { index: false, follow: false, googleBot: { index: false, follow: false } },
};

const tokens = [
  { name: "Primary text", variable: "--ink", className: "text-[var(--ink)]" },
  { name: "Supporting text", variable: "--muted", className: "text-[var(--muted)]" },
  { name: "Action", variable: "--accent", className: "text-[var(--teal-dark)]" },
  { name: "Page surface", variable: "--bg", className: "bg-[var(--bg)]" },
  { name: "Raised surface", variable: "--panel", className: "bg-[var(--panel)]" },
  { name: "Subtle surface", variable: "--surface", className: "bg-[var(--surface)]" },
];

export default function ThemeTestPage() {
  return (
    <PublicSiteFrame>
      <main id="main-content">
        <Section className="bg-[var(--bg)] pt-12 lg:pt-16">
          <div className="max-w-3xl">
            <Badge>Private theme preview</Badge>
            <h1 className="np-h1 mt-4">One theme system. Two comfortable viewing modes.</h1>
            <p className="np-lead mt-5">
              Use the theme control in the site header to switch between light and dark. The same
              global tokens drive this page, public pages, and the dashboard shell.
            </p>
            <p className="mt-4 text-sm leading-6 text-[var(--muted)]">
              Your choice is stored as a non-sensitive preference in this browser. New visitors
              start in light mode.
            </p>
          </div>

          <div className="mt-10 grid gap-5 lg:grid-cols-2">
            <Card elevated>
              <h2 className="text-lg font-bold">Semantic color roles</h2>
              <ul className="mt-5 grid gap-3 sm:grid-cols-2">
                {tokens.map((token) => (
                  <li
                    key={token.variable}
                    className={`flex min-h-14 items-center justify-between gap-3 rounded-xl border border-[var(--line)] p-3 ${token.className}`}
                  >
                    <span className="text-sm font-semibold">{token.name}</span>
                    <code className="text-xs">{token.variable}</code>
                  </li>
                ))}
              </ul>
            </Card>

            <Card elevated>
              <h2 className="text-lg font-bold">Interactive and status states</h2>
              <p className="mt-3 text-sm leading-6 text-[var(--muted)]">
                Check focus rings, link styling, readable status colors, and controls in both
                themes and at narrow widths.
              </p>
              <div className="mt-5 flex flex-wrap gap-3">
                <Button href="/api-overview/" variant="primary">Primary action</Button>
                <Button href="/product/" variant="secondary">Secondary action</Button>
              </div>
              <ul className="mt-6 space-y-3 text-sm">
                <li className="flex items-center gap-2 text-[var(--ok)]">
                  <CheckCircle2 size={17} aria-hidden /> Provider-backed outcome
                </li>
                <li className="rounded-lg border border-[var(--warn)] bg-[var(--warn-soft)] px-3 py-2 text-[var(--warn)]">
                  Initiation acknowledgement is not payment confirmation.
                </li>
              </ul>
            </Card>
          </div>

          <div className="mt-8 flex flex-wrap gap-3">
            <Button href="/" variant="secondary" rightIcon={<ArrowRight size={16} aria-hidden />}>
              Return to NetPay
            </Button>
            <Link href="/request-access/" className="self-center text-sm font-semibold text-[var(--teal-dark)] hover:underline">
              Request access
            </Link>
          </div>
        </Section>
      </main>
    </PublicSiteFrame>
  );
}
