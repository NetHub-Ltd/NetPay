import type { Metadata } from "next";
import {
  ArrowLeft,
  CreditCard,
  LayoutDashboard,
  LockKeyhole,
  Settings,
  Webhook,
} from "lucide-react";
import { Badge, Button, Card } from "../../components/ui";

export const metadata: Metadata = {
  title: "Merchant dashboard preview",
  description:
    "Preview the NetPay merchant dashboard shell. Merchant sign-in and data views are not enabled yet.",
  alternates: { canonical: "/dashboard/" },
  robots: { index: false, follow: false, noarchive: true, nosnippet: true },
  openGraph: {
    title: "Merchant dashboard preview | NetPay",
    description: "The NetPay merchant dashboard entry point — sign-in not enabled.",
    url: "/dashboard/",
    type: "website",
  },
};

const navItems = [
  { label: "Overview", icon: LayoutDashboard, active: true },
  { label: "Payments", icon: CreditCard, active: false },
  { label: "Webhooks", icon: Webhook, active: false },
  { label: "Settings", icon: Settings, active: false },
];

export default function DashboardPage() {
  return (
    <div className="flex min-h-screen bg-[var(--bg)] text-[var(--ink)]">
      {/* Sidebar chrome */}
      <aside
        className="hidden w-60 shrink-0 flex-col border-r border-[var(--line)] bg-[var(--navy)] text-[var(--on-navy)] md:flex"
        aria-label="Dashboard navigation preview"
      >
        <div className="flex items-center gap-3 border-b border-white/10 px-5 py-5">
          <span className="grid size-9 place-items-center rounded-xl bg-[var(--teal)] text-sm font-black text-[var(--navy)]">
            N
          </span>
          <div>
            <p className="text-sm font-bold tracking-tight">NetPay</p>
            <p className="text-xs text-[var(--on-navy-muted)]">Merchant console</p>
          </div>
        </div>
        <nav className="flex flex-1 flex-col gap-1 p-3">
          {navItems.map(({ label, icon: Icon, active }) => (
            <span
              key={label}
              className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold ${
                active
                  ? "bg-white/10 text-[var(--on-navy)]"
                  : "text-[var(--on-navy-muted)]"
              }`}
              aria-current={active ? "page" : undefined}
            >
              <Icon size={18} aria-hidden />
              {label}
            </span>
          ))}
        </nav>
        <p className="border-t border-white/10 px-5 py-4 text-xs text-[var(--on-navy-muted)]">
          Preview only — navigation is not interactive yet.
        </p>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        {/* Top bar */}
        <header className="flex items-center justify-between gap-4 border-b border-[var(--line)] bg-[var(--panel)] px-4 py-3 sm:px-6">
          <div className="flex items-center gap-3">
            <Button
              href="/"
              variant="ghost"
              size="sm"
              leftIcon={<ArrowLeft size={16} aria-hidden />}
              className="!px-2"
            >
              <span className="hidden sm:inline">Back to NetPay</span>
              <span className="sm:hidden">Home</span>
            </Button>
            <span className="hidden h-5 w-px bg-[var(--line)] sm:block" aria-hidden />
            <p className="hidden text-sm font-semibold text-[var(--muted)] sm:block">
              Dashboard preview
            </p>
          </div>
          <Badge tone="muted">Sign-in not enabled</Badge>
        </header>

        <main className="flex-1 p-4 sm:p-6 lg:p-8">
          <div className="mb-6">
            <h1 className="text-2xl font-extrabold tracking-tight sm:text-3xl">Overview</h1>
            <p className="mt-1 text-sm text-[var(--muted)]">
              Shell only. No merchant data is loaded until NetHub identity is connected.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            {["Payments today", "Succeeded", "Processing"].map((label) => (
              <Card key={label} className="opacity-90">
                <p className="text-xs font-bold uppercase tracking-wider text-[var(--muted)]">
                  {label}
                </p>
                <p className="mt-3 text-2xl font-extrabold tabular-nums text-[var(--line-strong)]">
                  —
                </p>
              </Card>
            ))}
          </div>

          <Card elevated className="mt-6 max-w-xl p-8">
            <span className="grid size-14 place-items-center rounded-2xl bg-[var(--teal-soft)] text-[var(--teal-dark)]">
              <LockKeyhole size={25} aria-hidden />
            </span>
            <h2 className="mt-6 text-xl font-bold tracking-tight">Authentication required</h2>
            <p className="mt-2 leading-7 text-[var(--muted)]">
              The dashboard UI is being connected to NetHub identity. No merchant data is shown here
              until authentication and session handling are wired in.
            </p>
            <div
              role="status"
              className="mt-6 rounded-[var(--radius)] border border-[var(--warn)]/25 bg-[var(--warn-soft)] p-4 text-sm leading-6 text-[var(--warn)]"
            >
              <p className="font-bold">Dashboard sign-in is not enabled yet.</p>
              <p className="mt-1">Use the M2M API during integration testing.</p>
            </div>
          </Card>
        </main>
      </div>
    </div>
  );
}
