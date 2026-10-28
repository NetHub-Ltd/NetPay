"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Check,
  CreditCard,
  Loader2,
  X,
} from "lucide-react";
import { Badge, Button, Card, Container } from "./ui";
import {
  THEME_META,
  THEMES,
  applyTheme,
  getStoredTheme,
  type ThemeId,
} from "../lib/theme";

function Swatch({ token, label }: { token: string; label: string }) {
  return (
    <div className="flex flex-col items-center gap-1.5">
      <span
        className="size-11 rounded-xl border border-[var(--line)] shadow-[var(--shadow-sm)]"
        style={{ background: `var(${token})` }}
        title={label}
      />
      <span className="max-w-[4.5rem] text-center font-mono text-[10px] leading-tight text-[var(--muted)]">
        {label}
      </span>
    </div>
  );
}

function FieldLabel({ children }: { children: React.ReactNode }) {
  return (
    <label className="mb-1.5 block text-xs font-bold uppercase tracking-wider text-[var(--muted)]">
      {children}
    </label>
  );
}

export function ThemeLab() {
  const [theme, setTheme] = useState<ThemeId>("harbor");
  const [ready, setReady] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [toast, setToast] = useState<"success" | "error" | "info" | null>("success");
  const [selectVal, setSelectVal] = useState("stk");

  useEffect(() => {
    const stored = getStoredTheme();
    applyTheme(stored);
    setTheme(stored);
    setReady(true);
  }, []);

  function select(id: ThemeId) {
    applyTheme(id);
    setTheme(id);
  }

  return (
    <div className="min-h-screen bg-[var(--bg)] pb-24 text-[var(--ink)]">
      <header className="sticky top-0 z-30 border-b border-[var(--line)] bg-[var(--panel)]/95 backdrop-blur">
        <Container className="flex flex-wrap items-center justify-between gap-4 py-4">
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="inline-flex items-center gap-2 text-sm font-semibold text-[var(--muted)] hover:text-[var(--ink)]"
            >
              <ArrowLeft size={16} aria-hidden />
              Home
            </Link>
            <span className="text-[var(--line-strong)]" aria-hidden>
              /
            </span>
            <h1 className="m-0 text-lg font-extrabold tracking-tight">Theme lab</h1>
          </div>
          <Badge tone="muted">
            {ready ? `Active: ${THEME_META[theme].name}` : "Loading…"}
          </Badge>
        </Container>
      </header>

      <Container className="mt-8 space-y-12">
        <div>
          <p className="text-sm font-bold uppercase tracking-[0.14em] text-[var(--accent-hover)]">
            Distinct systems
          </p>
          <p className="mt-2 max-w-2xl text-[var(--muted)]">
            Product default is Ledger. Harbor and Shamba remain lab-only for comparison. Choice is stored in{" "}
            <code className="rounded bg-[var(--surface)] px-1.5 py-0.5 text-xs">localStorage</code> and
            applies site-wide on this browser.
          </p>
        </div>

        {/* Picker */}
        <div className="grid gap-4 lg:grid-cols-3">
          {THEMES.map((id) => {
            const meta = THEME_META[id];
            const active = theme === id;
            return (
              <button
                key={id}
                type="button"
                onClick={() => select(id)}
                className={`rounded-[var(--radius-lg)] border p-5 text-left transition ${
                  active
                    ? "border-[var(--accent)] bg-[var(--panel)] shadow-[var(--shadow)] ring-2 ring-[var(--accent)]/35"
                    : "border-[var(--line)] bg-[var(--panel)] shadow-[var(--shadow-sm)] hover:border-[var(--accent)]/40"
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="text-lg font-extrabold tracking-tight">{meta.name}</p>
                    <p className="mt-1 text-sm leading-snug text-[var(--muted)]">{meta.tagline}</p>
                  </div>
                  {active && (
                    <span className="grid size-7 shrink-0 place-items-center rounded-full bg-[var(--accent)] text-[var(--on-accent)]">
                      <Check size={16} aria-hidden />
                    </span>
                  )}
                </div>
                <div className="mt-4 flex gap-2">
                  {meta.swatches.map((c) => (
                    <span
                      key={c}
                      className="size-9 rounded-lg border border-black/5 shadow-sm"
                      style={{ background: c }}
                    />
                  ))}
                </div>
                <p className="mt-3 font-mono text-[11px] text-[var(--muted)]">{id}</p>
              </button>
            );
          })}
        </div>

        {/* —— Full kit —— */}
        <section className="space-y-8">
          <h2 className="m-0 text-xl font-bold tracking-tight">Full UI kit (live tokens)</h2>

          {/* Navy chrome */}
          <div className="overflow-hidden rounded-[var(--radius-xl)] bg-[var(--navy)] text-[var(--on-navy)] shadow-[var(--shadow-lg)]">
            <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
              <div className="flex items-center gap-3">
                <span className="grid size-9 place-items-center rounded-xl bg-[var(--accent)] text-sm font-black text-[var(--on-accent)]">
                  N
                </span>
                <span className="font-bold">NetPay</span>
              </div>
              <span className="text-sm text-[var(--on-navy-muted)]">Header / hero chrome</span>
            </div>
            <div className="grid gap-8 p-6 sm:grid-cols-2 sm:p-8">
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.14em] text-[var(--on-navy-muted)]">
                  On-navy title
                </p>
                <p className="mt-3 text-3xl font-extrabold leading-tight tracking-tight text-[var(--on-navy)]">
                  Collect M-Pesa payments with state you can trust.
                </p>
                <p className="mt-4 text-sm leading-6 text-[var(--on-navy-muted)]">
                  Secondary copy must stay readable — never same value as the navy surface.
                </p>
                <div className="mt-6 flex flex-wrap gap-3">
                  <Button variant="onNavy" size="md">
                    Primary CTA
                  </Button>
                  <Button variant="onNavyOutline" size="md">
                    Secondary
                  </Button>
                </div>
              </div>
              <div className="rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--panel)] p-5 text-[var(--ink)] shadow-[var(--shadow)]">
                <p className="text-xs font-bold uppercase tracking-[0.14em] text-[var(--accent-hover)]">
                  Floating panel
                </p>
                <p className="mt-2 text-lg font-bold">Payment truth</p>
                <ul className="mt-3 space-y-2 text-sm text-[var(--muted)]">
                  <li>Provider-confirmed results</li>
                  <li>Idempotent STK + callback dedupe</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Surfaces */}
          <div className="grid gap-4 sm:grid-cols-3">
            {(
              [
                ["--bg", "Canvas"],
                ["--panel", "Panel"],
                ["--surface", "Surface"],
              ] as const
            ).map(([token, label]) => (
              <div
                key={label}
                className="rounded-[var(--radius-lg)] border border-[var(--line)] p-5 shadow-[var(--shadow-sm)]"
                style={{ background: `var(${token})` }}
              >
                <p className="text-xs font-bold uppercase tracking-wider text-[var(--muted)]">{label}</p>
                <p className="mt-2 font-bold">Ink on {label.toLowerCase()}</p>
                <p className="mt-1 text-sm text-[var(--muted)]">Muted secondary</p>
              </div>
            ))}
          </div>

          {/* Borders */}
          <Card>
            <p className="text-xs font-bold uppercase tracking-wider text-[var(--muted)]">Borders</p>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <div className="rounded-[var(--radius)] border border-[var(--line)] p-4 text-sm">
                Default <code className="text-xs">--line</code>
              </div>
              <div className="rounded-[var(--radius)] border-2 border-[var(--line-strong)] p-4 text-sm">
                Strong <code className="text-xs">--line-strong</code>
              </div>
              <div className="rounded-[var(--radius)] border border-[var(--accent)] p-4 text-sm">
                Accent focus border
              </div>
              <div className="rounded-[var(--radius)] border border-dashed border-[var(--line-strong)] p-4 text-sm text-[var(--muted)]">
                Dashed empty-state border
              </div>
            </div>
          </Card>

          {/* Buttons */}
          <Card>
            <p className="text-xs font-bold uppercase tracking-wider text-[var(--muted)]">buttons</p>
            <div className="mt-4 flex flex-wrap gap-3">
              <Button variant="primary">Primary</Button>
              <Button variant="secondary">Secondary</Button>
              <Button variant="ghost">Ghost</Button>
              <button
                type="button"
                className="inline-flex items-center justify-center rounded-full border border-[var(--danger)] bg-[var(--danger)] px-5 py-2.5 text-sm font-semibold text-white"
              >
                Danger
              </button>
              <Button variant="primary" size="sm">
                Small
              </Button>
              <Button variant="primary" size="lg">
                Large
              </Button>
              <Button variant="primary" disabled>
                Disabled
              </Button>
              <Button variant="primary" leftIcon={<Loader2 size={16} className="np-spinner" aria-hidden />}>
                Loading
              </Button>
            </div>
          </Card>

          {/* Forms */}
          <Card>
            <p className="text-xs font-bold uppercase tracking-wider text-[var(--muted)]">
              inputs · select · checkbox
            </p>
            <div className="mt-4 grid gap-5 sm:grid-cols-2">
              <div>
                <FieldLabel>Text input</FieldLabel>
                <input
                  type="text"
                  defaultValue="254712345678"
                  className="w-full rounded-[var(--radius)] border border-[var(--line)] bg-[var(--panel)] px-3 py-2.5 text-sm text-[var(--ink)] shadow-[var(--shadow-sm)] placeholder:text-[var(--muted)] focus:border-[var(--accent)]"
                  placeholder="Phone"
                />
              </div>
              <div>
                <FieldLabel>Select</FieldLabel>
                <select
                  value={selectVal}
                  onChange={(e) => setSelectVal(e.target.value)}
                  className="w-full rounded-[var(--radius)] border border-[var(--line)] bg-[var(--panel)] px-3 py-2.5 text-sm text-[var(--ink)] shadow-[var(--shadow-sm)] focus:border-[var(--accent)]"
                >
                  <option value="stk">STK Push</option>
                  <option value="c2b">C2B</option>
                  <option value="query">Status query</option>
                </select>
              </div>
              <div>
                <FieldLabel>Invalid</FieldLabel>
                <input
                  type="text"
                  defaultValue="bad"
                  className="w-full rounded-[var(--radius)] border border-[var(--danger)] bg-[var(--danger-soft)] px-3 py-2.5 text-sm text-[var(--danger)]"
                />
                <p className="mt-1 text-xs font-semibold text-[var(--danger)]">Enter a valid amount</p>
              </div>
              <div className="flex items-end gap-4 pb-1">
                <label className="flex items-center gap-2 text-sm font-semibold">
                  <input
                    type="checkbox"
                    defaultChecked
                    className="size-4 rounded border-[var(--line)] accent-[var(--accent)]"
                  />
                  Remember device
                </label>
                <label className="flex items-center gap-2 text-sm font-semibold">
                  <input type="radio" name="env" defaultChecked className="accent-[var(--accent)]" />
                  Sandbox
                </label>
              </div>
            </div>
          </Card>

          {/* Badges + status */}
          <Card>
            <p className="text-xs font-bold uppercase tracking-wider text-[var(--muted)]">
              badges · status pills
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              <Badge tone="teal">Accent</Badge>
              <Badge tone="navy">Navy</Badge>
              <Badge tone="muted">Muted</Badge>
              <span className="inline-flex rounded-full border border-[var(--ok)]/30 bg-[var(--ok-soft)] px-3 py-1 text-xs font-bold text-[var(--ok)]">
                Succeeded
              </span>
              <span className="inline-flex rounded-full border border-[var(--warn)]/30 bg-[var(--warn-soft)] px-3 py-1 text-xs font-bold text-[var(--warn)]">
                Processing
              </span>
              <span className="inline-flex rounded-full border border-[var(--danger)]/30 bg-[var(--danger-soft)] px-3 py-1 text-xs font-bold text-[var(--danger)]">
                Failed
              </span>
              <span className="inline-flex rounded-full border border-[var(--info)]/30 bg-[var(--info-soft)] px-3 py-1 text-xs font-bold text-[var(--info)]">
                Info
              </span>
            </div>
          </Card>

          {/* Spinners / loading */}
          <Card>
            <p className="text-xs font-bold uppercase tracking-wider text-[var(--muted)]">
              spinners · skeleton
            </p>
            <div className="mt-4 flex flex-wrap items-center gap-6">
              <Loader2 className="np-spinner size-8 text-[var(--accent)]" aria-label="Loading" />
              <Loader2 className="np-spinner size-6 text-[var(--ink)]" aria-hidden />
              <div className="flex flex-1 flex-col gap-2 sm:max-w-xs">
                <div className="np-pulse h-3 rounded-full bg-[var(--line)]" />
                <div className="np-pulse h-3 w-4/5 rounded-full bg-[var(--line)]" />
                <div className="np-pulse h-10 rounded-[var(--radius)] bg-[var(--surface)]" />
              </div>
            </div>
          </Card>

          {/* Table */}
          <Card className="overflow-hidden p-0">
            <div className="border-b border-[var(--line)] px-5 py-3">
              <p className="text-xs font-bold uppercase tracking-wider text-[var(--muted)]">table</p>
            </div>
            <table className="w-full text-left text-sm">
              <thead className="bg-[var(--surface)] text-xs uppercase tracking-wider text-[var(--muted)]">
                <tr>
                  <th className="px-5 py-3 font-bold">Reference</th>
                  <th className="px-5 py-3 font-bold">Amount</th>
                  <th className="px-5 py-3 font-bold">Status</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-t border-[var(--line)]">
                  <td className="px-5 py-3 font-semibold">order-123</td>
                  <td className="px-5 py-3 tabular-nums">KES 2,500.00</td>
                  <td className="px-5 py-3">
                    <span className="rounded-full bg-[var(--ok-soft)] px-2 py-0.5 text-xs font-bold text-[var(--ok)]">
                      Paid
                    </span>
                  </td>
                </tr>
                <tr className="border-t border-[var(--line)] hover:bg-[var(--surface)]">
                  <td className="px-5 py-3 font-semibold">order-124</td>
                  <td className="px-5 py-3 tabular-nums">KES 150.00</td>
                  <td className="px-5 py-3">
                    <span className="rounded-full bg-[var(--warn-soft)] px-2 py-0.5 text-xs font-bold text-[var(--warn)]">
                      Processing
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </Card>

          {/* Alerts / banners */}
          <div className="space-y-3">
            <p className="text-xs font-bold uppercase tracking-wider text-[var(--muted)]">
              banners · alerts
            </p>
            {(
              [
                ["--ok-soft", "--ok", "Payment marked successful from provider result."],
                ["--warn-soft", "--warn", "Still processing — waiting on network callback."],
                ["--danger-soft", "--danger", "Path check failed. Retry or use portal URLs."],
                ["--info-soft", "--info", "Dashboard sign-in is not enabled yet."],
              ] as const
            ).map(([bg, fg, text]) => (
              <div
                key={text}
                className="rounded-[var(--radius)] border px-4 py-3 text-sm font-semibold"
                style={{
                  background: `var(${bg})`,
                  color: `var(${fg})`,
                  borderColor: `color-mix(in srgb, var(${fg}) 28%, transparent)`,
                }}
                role="status"
              >
                {text}
              </div>
            ))}
          </div>

          {/* Toasts trigger */}
          <Card>
            <p className="text-xs font-bold uppercase tracking-wider text-[var(--muted)]">toasts</p>
            <div className="mt-3 flex flex-wrap gap-2">
              <Button variant="secondary" size="sm" onClick={() => setToast("success")}>
                Show success
              </Button>
              <Button variant="secondary" size="sm" onClick={() => setToast("error")}>
                Show error
              </Button>
              <Button variant="secondary" size="sm" onClick={() => setToast("info")}>
                Show info
              </Button>
            </div>
          </Card>

          {/* Modal */}
          <Card>
            <p className="text-xs font-bold uppercase tracking-wider text-[var(--muted)]">modal</p>
            <Button variant="primary" className="mt-3" onClick={() => setModalOpen(true)}>
              Open confirm modal
            </Button>
          </Card>

          {/* Links + mono */}
          <Card>
            <p className="text-xs font-bold uppercase tracking-wider text-[var(--muted)]">
              links · mono
            </p>
            <p className="mt-3 text-sm">
              Inline{" "}
              <a href="#kit" className="font-bold text-[var(--accent-hover)] underline">
                accent link
              </a>{" "}
              on body text.
            </p>
            <pre className="mt-4 overflow-x-auto rounded-[var(--radius)] bg-[var(--navy)] p-4 text-sm text-[var(--on-navy-muted)]">
              <code>{`POST /api/v1/payments/stk-push\nAuthorization: Bearer •••••`}</code>
            </pre>
          </Card>

          {/* Token grid */}
          <Card>
            <p className="text-xs font-bold uppercase tracking-wider text-[var(--muted)]">
              token swatches ({THEME_META[theme].name})
            </p>
            <div className="mt-4 flex flex-wrap gap-4">
              {(
                [
                  ["--navy", "navy"],
                  ["--accent", "accent"],
                  ["--bg", "bg"],
                  ["--panel", "panel"],
                  ["--surface", "surface"],
                  ["--ink", "ink"],
                  ["--muted", "muted"],
                  ["--on-navy", "on-navy"],
                  ["--line", "line"],
                  ["--ok", "ok"],
                  ["--warn", "warn"],
                  ["--danger", "danger"],
                  ["--info", "info"],
                ] as const
              ).map(([token, label]) => (
                <Swatch key={token} token={token} label={label} />
              ))}
            </div>
          </Card>

          {/* Nav preview */}
          <div className="flex gap-3 overflow-x-auto rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--panel)] p-2 shadow-[var(--shadow-sm)]">
            {["Overview", "Payments", "Webhooks", "Settings"].map((item, i) => (
              <span
                key={item}
                className={`flex items-center gap-2 whitespace-nowrap rounded-xl px-3 py-2 text-sm font-semibold ${
                  i === 0
                    ? "bg-[var(--accent-soft)] text-[var(--accent-hover)]"
                    : "text-[var(--muted)]"
                }`}
              >
                {i === 0 && <CreditCard size={16} aria-hidden />}
                {item}
              </span>
            ))}
          </div>
        </section>

        <p className="text-sm text-[var(--muted)]">
          Product default is locked to <strong>ledger</strong>. Lab switches still persist in this browser for comparison only.
        </p>
      </Container>

      {/* Toast host */}
      {toast && (
        <div className="fixed bottom-6 right-6 z-50 w-[min(100%-2rem,22rem)]" role="status">
          <div
            className="flex items-start gap-3 rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--panel)] p-4 shadow-[var(--shadow-lg)]"
            style={{
              borderLeftWidth: 4,
              borderLeftColor:
                toast === "success"
                  ? "var(--ok)"
                  : toast === "error"
                    ? "var(--danger)"
                    : "var(--info)",
            }}
          >
            <div className="min-w-0 flex-1">
              <p className="text-sm font-bold">
                {toast === "success" ? "Payment updated" : toast === "error" ? "Request failed" : "Heads up"}
              </p>
              <p className="mt-0.5 text-sm text-[var(--muted)]">
                {toast === "success"
                  ? "Status is now Succeeded from provider evidence."
                  : toast === "error"
                    ? "Could not reach the network. Try again."
                    : "Sign-in is not enabled on this preview."}
              </p>
            </div>
            <button
              type="button"
              className="rounded-lg p-1 text-[var(--muted)] hover:bg-[var(--surface)] hover:text-[var(--ink)]"
              aria-label="Dismiss"
              onClick={() => setToast(null)}
            >
              <X size={16} />
            </button>
          </div>
        </div>
      )}

      {/* Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 grid place-items-center p-4" role="dialog" aria-modal="true">
          <button
            type="button"
            className="absolute inset-0 bg-[var(--navy)]/50"
            aria-label="Close dialog"
            onClick={() => setModalOpen(false)}
          />
          <div className="relative w-full max-w-md rounded-[var(--radius-xl)] border border-[var(--line)] bg-[var(--panel)] p-6 shadow-[var(--shadow-lg)]">
            <h2 className="m-0 text-xl font-bold tracking-tight">Disconnect shortcode?</h2>
            <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
              This stops NetPay from initiating STK for this integration. You can connect again later.
            </p>
            <div className="mt-6 flex flex-wrap justify-end gap-2">
              <Button variant="secondary" onClick={() => setModalOpen(false)}>
                Cancel
              </Button>
              <button
                type="button"
                className="inline-flex items-center justify-center rounded-full bg-[var(--danger)] px-5 py-2.5 text-sm font-semibold text-white"
                onClick={() => setModalOpen(false)}
              >
                Disconnect
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
