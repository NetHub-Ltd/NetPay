"use client";

import { useCallback, useEffect, useState } from "react";
import {
  ArrowLeft,
  CreditCard,
  LayoutDashboard,
  LockKeyhole,
  Settings,
  Webhook,
} from "lucide-react";
import { Badge, Button, Card } from "./ui";
import { clearSession, getAccessToken } from "../lib/session";
import {
  fetchAuthMe,
  fetchMemberships,
  startLogin,
  type AuthMe,
  type Membership,
} from "../lib/oidc";
import { loadSpaConfig } from "../lib/config";

const navItems = [
  { label: "Overview", icon: LayoutDashboard, active: true },
  { label: "Payments", icon: CreditCard, active: false },
  { label: "Webhooks", icon: Webhook, active: false },
  { label: "Settings", icon: Settings, active: false },
];

type Status =
  | { kind: "loading" }
  | { kind: "signed_out"; oidcReady: boolean; message?: string }
  | { kind: "signed_in"; me: AuthMe; memberships: Membership[] }
  | { kind: "error"; message: string };

export function DashboardClient() {
  const [status, setStatus] = useState<Status>({ kind: "loading" });
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    setStatus({ kind: "loading" });
    try {
      const cfg = await loadSpaConfig();
      const token = getAccessToken();
      if (!token) {
        setStatus({
          kind: "signed_out",
          oidcReady: cfg.oidc_configured,
          message: cfg.oidc_configured
            ? undefined
            : "OIDC is not configured on this deployment (set OIDC_* env on the API).",
        });
        return;
      }
      const me = await fetchAuthMe(token);
      let memberships: Membership[] = [];
      try {
        memberships = await fetchMemberships(token);
      } catch {
        memberships = [];
      }
      setStatus({ kind: "signed_in", me, memberships });
    } catch (e) {
      clearSession();
      const message = e instanceof Error ? e.message : "Could not load session";
      const is401 =
        (e instanceof Error && e.name === "AuthApiError" && (e as { status?: number }).status === 401) ||
        /session expired|sign in again/i.test(message);
      if (is401) {
        setStatus({
          kind: "signed_out",
          oidcReady: true,
          message,
        });
        return;
      }
      setStatus({
        kind: "error",
        message,
      });
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function onSignIn() {
    setBusy(true);
    try {
      await startLogin();
    } catch (e) {
      setBusy(false);
      setStatus({
        kind: "error",
        message: e instanceof Error ? e.message : "Could not start sign-in",
      });
    }
  }

  function onSignOut() {
    clearSession();
    setStatus({ kind: "signed_out", oidcReady: true });
  }

  if (status.kind === "loading") {
    return (
      <div className="grid min-h-screen place-items-center bg-[var(--bg)] text-[var(--ink-muted)]">
        <p className="text-sm">Loading dashboard…</p>
      </div>
    );
  }

  if (status.kind === "signed_out" || status.kind === "error") {
    return (
      <div className="mx-auto flex min-h-screen max-w-lg flex-col justify-center gap-6 px-6">
        <div>
          <Badge>Merchant console</Badge>
          <h1 className="mt-3 font-display text-2xl font-bold text-[var(--ink)]">Sign in to NetPay</h1>
          <p className="mt-2 text-sm text-[var(--ink-muted)]">
            Use your NetHub identity. NetPay validates access through NetHubKe — it does not store
            passwords.
          </p>
        </div>
        {(status.kind === "error" || (status.kind === "signed_out" && status.message)) && (
          <p className="rounded-xl border border-[var(--line)] bg-[var(--surface)] p-3 text-sm text-[var(--ink)]" role="alert">
            {status.kind === "error" ? status.message : status.message}
          </p>
        )}
        <div className="flex flex-wrap gap-3">
          <Button
            type="button"
            onClick={() => void onSignIn()}
            disabled={busy || (status.kind === "signed_out" && !status.oidcReady)}
          >
            {busy ? "Redirecting…" : "Sign in"}
          </Button>
          <Button href="/" variant="secondary">
            Back to site
          </Button>
        </div>
      </div>
    );
  }

  const { me, memberships } = status;

  return (
    <div className="flex min-h-screen bg-[var(--bg)] text-[var(--ink)]">
      <aside
        className="hidden w-60 shrink-0 flex-col border-r border-[var(--line)] bg-[var(--navy)] text-[var(--on-navy)] md:flex"
        aria-label="Dashboard navigation"
      >
        <div className="flex items-center gap-3 border-b border-[var(--header-border)] px-5 py-5">
          <span className="grid size-9 place-items-center rounded-xl bg-[var(--accent)] text-[length:var(--text-sm)] font-[number:var(--weight-black)] text-[var(--on-accent)]">
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
                  ? "bg-[var(--on-navy-soft-fill)] text-[var(--on-navy)]"
                  : "text-[var(--on-navy-muted)]"
              }`}
            >
              <Icon className="size-4 shrink-0" aria-hidden />
              {label}
            </span>
          ))}
        </nav>
        <div className="border-t border-[var(--header-border)] p-4 text-xs text-[var(--on-navy-muted)]">
          {me.email}
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between gap-3 border-b border-[var(--line)] px-4 py-3 sm:px-6">
          <Button href="/" variant="secondary" size="sm" leftIcon={<ArrowLeft className="size-4" />}>
            Site
          </Button>
          <div className="flex items-center gap-2">
            <span className="hidden text-sm text-[var(--ink-muted)] sm:inline">{me.full_name || me.email}</span>
            <Button type="button" variant="secondary" size="sm" onClick={onSignOut}>
              Sign out
            </Button>
          </div>
        </header>

        <main className="flex-1 space-y-6 p-4 sm:p-6">
          <div>
            <h1 className="text-xl font-bold tracking-tight">Overview</h1>
            <p className="mt-1 text-sm text-[var(--ink-muted)]">
              Signed in via NetHubKe resource server. Payment management UI comes next.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <Card>
              <h2 className="text-sm font-semibold">Identity</h2>
              <dl className="mt-3 space-y-2 text-sm">
                <div className="flex justify-between gap-2">
                  <dt className="text-[var(--ink-muted)]">Email</dt>
                  <dd className="font-medium">{me.email}</dd>
                </div>
                <div className="flex justify-between gap-2">
                  <dt className="text-[var(--ink-muted)]">Name</dt>
                  <dd className="font-medium">{me.full_name || "—"}</dd>
                </div>
                {me.is_admin && (
                  <div className="flex justify-between gap-2">
                    <dt className="text-[var(--ink-muted)]">Role</dt>
                    <dd>
                      <Badge>Platform admin</Badge>
                    </dd>
                  </div>
                )}
              </dl>
            </Card>

            <Card>
              <h2 className="text-sm font-semibold">Merchants</h2>
              {memberships.length === 0 ? (
                <p className="mt-3 text-sm text-[var(--ink-muted)]">
                  No merchant membership yet. A platform admin must grant access before payment data
                  is available.
                </p>
              ) : (
                <ul className="mt-3 space-y-2 text-sm">
                  {memberships.map((m) => (
                    <li
                      key={m.merchant_id}
                      className="flex items-center justify-between gap-2 rounded-lg border border-[var(--line)] px-3 py-2"
                    >
                      <span className="font-medium">{m.merchant_name || m.merchant_slug || m.merchant_id}</span>
                      <Badge>{m.role}</Badge>
                    </li>
                  ))}
                </ul>
              )}
            </Card>
          </div>

          <Card>
            <div className="flex items-start gap-3">
              <LockKeyhole className="mt-0.5 size-5 shrink-0 text-[var(--accent)]" aria-hidden />
              <div>
                <h2 className="text-sm font-semibold">Data access</h2>
                <p className="mt-1 text-sm text-[var(--ink-muted)]">
                  Merchant payment screens stay locked until membership is granted. M2M API keys
                  remain separate from this human session.
                </p>
              </div>
            </div>
          </Card>
        </main>
      </div>
    </div>
  );
}
