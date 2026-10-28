"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Check } from "lucide-react";
import { Badge, Button, Card, Container } from "./ui";
import {
  THEME_META,
  THEMES,
  applyTheme,
  getStoredTheme,
  type ThemeId,
} from "../lib/theme";

function Swatch({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex flex-col items-center gap-1.5">
      <span
        className="size-10 rounded-xl border border-[var(--line)] shadow-[var(--shadow-sm)]"
        style={{ background: color }}
        title={color}
      />
      <span className="font-mono text-[10px] text-[var(--muted)]">{label}</span>
    </div>
  );
}

export function ThemeLab() {
  const [theme, setTheme] = useState<ThemeId>("harbor");
  const [ready, setReady] = useState(false);

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
    <div className="min-h-screen bg-[var(--bg)] pb-16 text-[var(--ink)]">
      <header className="border-b border-[var(--line)] bg-[var(--panel)]">
        <Container className="flex flex-wrap items-center justify-between gap-4 py-4">
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="inline-flex items-center gap-2 text-sm font-semibold text-[var(--muted)] hover:text-[var(--ink)]"
            >
              <ArrowLeft size={16} aria-hidden />
              Home
            </Link>
            <span className="text-[var(--line-strong)]">/</span>
            <h1 className="m-0 text-lg font-extrabold tracking-tight">Theme lab</h1>
          </div>
          <Badge tone="muted">{ready ? `Active: ${THEME_META[theme].name}` : "Loading…"}</Badge>
        </Container>
      </header>

      <Container className="mt-8 space-y-10">
        <div>
          <p className="text-sm font-bold uppercase tracking-[0.14em] text-[var(--teal-dark)]">
            Choose a system
          </p>
          <p className="mt-2 max-w-2xl text-[var(--muted)]">
            Three full themes (canvas, type, buttons, shadows, navy chrome). Your pick is saved in{" "}
            <code className="rounded bg-[var(--surface)] px-1.5 py-0.5 text-xs">localStorage</code> and
            applies site-wide on this browser.
          </p>
        </div>

        {/* Theme picker cards */}
        <div className="grid gap-4 md:grid-cols-3">
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
                    ? "border-[var(--teal)] bg-[var(--panel)] shadow-[var(--shadow)] ring-2 ring-[var(--teal)]/40"
                    : "border-[var(--line)] bg-[var(--panel)] shadow-[var(--shadow-sm)] hover:border-[var(--teal)]/50"
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="text-lg font-extrabold tracking-tight">{meta.name}</p>
                    <p className="mt-1 text-sm text-[var(--muted)]">{meta.tagline}</p>
                  </div>
                  {active && (
                    <span className="grid size-7 place-items-center rounded-full bg-[var(--teal)] text-[var(--navy)]">
                      <Check size={16} aria-hidden />
                    </span>
                  )}
                </div>
                <div className="mt-4 flex gap-2">
                  {meta.swatches.map((c) => (
                    <span
                      key={c}
                      className="size-8 rounded-lg border border-black/5"
                      style={{ background: c }}
                    />
                  ))}
                </div>
                <p className="mt-3 font-mono text-[11px] text-[var(--muted)]">{id}</p>
              </button>
            );
          })}
        </div>

        {/* Live preview — uses current CSS variables */}
        <section className="space-y-6">
          <h2 className="m-0 text-xl font-bold">Live preview</h2>

          {/* Navy chrome sample */}
          <div className="overflow-hidden rounded-[var(--radius-xl)] bg-[var(--navy)] text-[var(--on-navy)] shadow-[var(--shadow-lg)]">
            <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
              <div className="flex items-center gap-3">
                <span className="grid size-9 place-items-center rounded-xl bg-[var(--teal)] text-sm font-black text-[var(--navy)]">
                  N
                </span>
                <span className="font-bold">NetPay</span>
              </div>
              <span className="text-sm text-[var(--on-navy-muted)]">Header on navy</span>
            </div>
            <div className="grid gap-8 p-6 sm:grid-cols-2 sm:p-8">
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.14em] text-[var(--on-navy-muted)]">
                  Hero title
                </p>
                <p className="mt-3 text-3xl font-extrabold leading-tight tracking-tight text-[var(--on-navy)]">
                  Collect M-Pesa payments with state you can trust.
                </p>
                <p className="mt-4 text-sm leading-6 text-[var(--on-navy-muted)]">
                  Secondary copy on navy uses muted on-navy — never the same as the background.
                </p>
                <div className="mt-6 flex flex-wrap gap-3">
                  <Button variant="onNavy" size="md">
                    Primary on navy
                  </Button>
                  <Button variant="onNavyOutline" size="md">
                    Outline
                  </Button>
                </div>
              </div>
              <Card elevated className="border-[var(--line)] bg-[var(--panel)] text-[var(--ink)]">
                <p className="text-xs font-bold uppercase tracking-[0.14em] text-[var(--teal-dark)]">
                  Panel on hero
                </p>
                <p className="mt-2 text-lg font-bold">One clear source of truth</p>
                <ul className="mt-4 space-y-2 text-sm text-[var(--muted)]">
                  <li>Provider-confirmed results</li>
                  <li>Idempotent STK + callback dedupe</li>
                  <li>Optional signed webhooks</li>
                </ul>
              </Card>
            </div>
          </div>

          {/* Canvas + cards */}
          <div className="grid gap-4 sm:grid-cols-3">
            {["Canvas", "Panel", "Surface"].map((label, i) => (
              <div
                key={label}
                className="rounded-[var(--radius-lg)] border border-[var(--line)] p-5 shadow-[var(--shadow-sm)]"
                style={{
                  background: i === 0 ? "var(--bg)" : i === 1 ? "var(--panel)" : "var(--surface)",
                }}
              >
                <p className="text-xs font-bold uppercase tracking-wider text-[var(--muted)]">{label}</p>
                <p className="mt-2 font-bold text-[var(--ink)]">Ink on {label.toLowerCase()}</p>
                <p className="mt-1 text-sm text-[var(--muted)]">Muted secondary text sample.</p>
              </div>
            ))}
          </div>

          {/* Buttons */}
          <Card>
            <p className="text-xs font-bold uppercase tracking-wider text-[var(--muted)]">Buttons</p>
            <div className="mt-4 flex flex-wrap gap-3">
              <Button variant="primary">Primary</Button>
              <Button variant="secondary">Secondary</Button>
              <Button variant="ghost">Ghost</Button>
              <Button variant="primary" size="sm">
                Small
              </Button>
              <Button variant="primary" size="lg">
                Large
              </Button>
            </div>
          </Card>

          {/* Type scale */}
          <Card>
            <p className="text-xs font-bold uppercase tracking-wider text-[var(--muted)]">Typography</p>
            <p className="mt-4 text-4xl font-extrabold tracking-tight">Heading 800</p>
            <p className="mt-2 text-2xl font-bold tracking-tight">Heading 700</p>
            <p className="mt-2 text-base font-semibold">Body semibold 600</p>
            <p className="mt-1 text-sm font-medium text-[var(--muted)]">Muted medium 500</p>
            <pre className="mt-4 overflow-x-auto rounded-[var(--radius)] bg-[var(--navy)] p-4 text-sm text-[var(--on-navy-muted)]">
              <code>{`// Mono on navy\nPOST /api/v1/payments/stk-push`}</code>
            </pre>
          </Card>

          {/* Shadows + badges */}
          <div className="grid gap-4 sm:grid-cols-2">
            <Card className="shadow-[var(--shadow-sm)]">
              <p className="font-bold">Shadow sm</p>
              <p className="mt-1 text-sm text-[var(--muted)]">Subtle lift</p>
            </Card>
            <Card elevated className="shadow-[var(--shadow)]">
              <p className="font-bold">Shadow default</p>
              <p className="mt-1 text-sm text-[var(--muted)]">Card elevation</p>
            </Card>
          </div>

          <div className="flex flex-wrap gap-2">
            <Badge tone="teal">Teal badge</Badge>
            <Badge tone="navy">Navy badge</Badge>
            <Badge tone="muted">Muted badge</Badge>
          </div>

          {/* Token swatches from computed theme - static labels */}
          <Card>
            <p className="text-xs font-bold uppercase tracking-wider text-[var(--muted)]">
              Token reference ({THEME_META[theme].name})
            </p>
            <div className="mt-4 flex flex-wrap gap-4">
              <Swatch color="var(--navy)" label="navy" />
              <Swatch color="var(--teal)" label="teal" />
              <Swatch color="var(--bg)" label="bg" />
              <Swatch color="var(--panel)" label="panel" />
              <Swatch color="var(--ink)" label="ink" />
              <Swatch color="var(--muted)" label="muted" />
              <Swatch color="var(--on-navy)" label="on-navy" />
              <Swatch color="var(--line)" label="line" />
            </div>
          </Card>
        </section>

        <p className="text-sm text-[var(--muted)]">
          After you pick a favourite, tell us which id to lock as the product default (
          <code className="text-xs">harbor</code>, <code className="text-xs">ink</code>, or{" "}
          <code className="text-xs">signal</code>).
        </p>
      </Container>
    </div>
  );
}
