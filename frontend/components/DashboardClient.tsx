"use client";

import { useCallback, useEffect, useState } from "react";
import {
  CreditCard,
  LayoutDashboard,
  LogOut,
  Settings,
  Webhook,
} from "lucide-react";
import { Button, Badge, Card } from "./ui";
import {
  AuthApiError,
  fetchAuthMe,
  fetchMemberships,
  fetchMerchantPayments,
  fetchMerchantSummary,
  startLogin,
  clearSession,
} from "../lib/oidc";
import type { AuthMe, HumanPayment, Membership, MerchantSummary } from "../lib/oidc";

const NAV = [
  { label: "Overview", icon: LayoutDashboard, active: true },
  { label: "Payments", icon: CreditCard, active: false },
  { label: "Webhooks", icon: Webhook, active: false },
  { label: "Settings", icon: Settings, active: false },
];

type Status =
  | { kind: "loading" }
  | { kind: "signed_out"; oidcReady: boolean; message?: string }
  | {
      kind: "signed_in";
      me: AuthMe;
      memberships: Membership[];
      selectedMerchantId: string | null;
      merchant: MerchantSummary | null;
      payments: HumanPayment[];
      dataError?: string;
    }
  | { kind: "error"; message: string };

function formatAmount(minor: number, currency: string): string {
  const major = (minor / 100).toFixed(2);
  return `${currency} ${major}`;
}

export function DashboardClient() {
  const [status, setStatus] = useState<Status>({ kind: "loading" });
  const [busy, setBusy] = useState(false);

  const loadMerchantData = useCallback(
    async (merchantId: string) => {
      const merchant = await fetchMerchantSummary(merchantId);
      let payments: HumanPayment[] = [];
      try {
        payments = await fetchMerchantPayments(merchantId, 10);
      } catch (error) {
        if (error instanceof AuthApiError && error.status === 401) throw error;
        payments = [];
      }
      return { merchant, payments };
    },
    [],
  );

  const refresh = useCallback(async () => {
    setStatus({ kind: "loading" });
    try {
      const me = await fetchAuthMe();
      let memberships: Membership[] = [];
      try {
        memberships = await fetchMemberships();
      } catch (error) {
        if (error instanceof AuthApiError && error.status === 401) throw error;
        memberships = [];
      }

      const selectedMerchantId: string | null =
        memberships.length === 1 ? memberships[0].merchant_id : null;
      let merchant: MerchantSummary | null = null;
      let payments: HumanPayment[] = [];
      let dataError: string | undefined;

      if (selectedMerchantId) {
        try {
          const data = await loadMerchantData(selectedMerchantId);
          merchant = data.merchant;
          payments = data.payments;
        } catch (e) {
          dataError = e instanceof Error ? e.message : "Could not load merchant data";
        }
      }

      setStatus({
        kind: "signed_in",
        me,
        memberships,
        selectedMerchantId,
        merchant,
        payments,
        dataError,
      });
    } catch (e) {
      const message = e instanceof Error ? e.message : "Could not load session";
      const is401 =
        (e instanceof AuthApiError && e.status === 401) ||
        /session expired|sign in again/i.test(message);
      if (is401) {
        await clearSession().catch(() => undefined);
        setStatus({ kind: "signed_out", oidcReady: true, message });
        return;
      }
      setStatus({ kind: "error", message });
    }
  }, [loadMerchantData]);

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

  async function onSignOut() {
    try {
      await clearSession();
      setStatus({ kind: "signed_out", oidcReady: true });
    } catch (error) {
      setStatus({
        kind: "error",
        message: error instanceof Error ? error.message : "Could not sign out",
      });
    }
  }

  async function onSelectMerchant(merchantId: string) {
    if (status.kind !== "signed_in") return;
    setStatus({ ...status, selectedMerchantId: merchantId, merchant: null, payments: [], dataError: undefined });
    try {
      const data = await loadMerchantData(merchantId);
      setStatus({
        ...status,
        selectedMerchantId: merchantId,
        merchant: data.merchant,
        payments: data.payments,
        dataError: undefined,
      });
    } catch (e) {
      if (e instanceof AuthApiError && e.status === 401) {
        await clearSession().catch(() => undefined);
        setStatus({ kind: "signed_out", oidcReady: true, message: e.message });
        return;
      }
      setStatus({
        ...status,
        selectedMerchantId: merchantId,
        merchant: null,
        payments: [],
        dataError: e instanceof Error ? e.message : "Could not load merchant data",
      });
    }
  }

  if (status.kind === "loading") {
    return (
      <div className="grid min-h-screen place-items-center bg-[var(--bg)] text-[var(--ink-muted)]">
        <p className="text-sm">Loading dashboard…</p>
      </div>
    );
  }

  if (status.kind === "error") {
    return (
      <div className="mx-auto flex min-h-screen max-w-md flex-col justify-center gap-4 px-6">
        <h1 className="text-xl font-bold text-[var(--ink)]">Could not load dashboard</h1>
        <p className="text-sm text-[var(--ink-muted)]" role="alert">
          {status.message}
        </p>
        <Button type="button" onClick={() => void refresh()}>
          Try again
        </Button>
        <Button type="button" variant="secondary" onClick={onSignOut}>
          Sign out
        </Button>
      </div>
    );
  }

  if (status.kind === "signed_out") {
    return (
      <div className="mx-auto flex min-h-screen max-w-md flex-col justify-center gap-4 px-6">
        <h1 className="text-xl font-bold text-[var(--ink)]">Merchant dashboard</h1>
        <p className="text-sm text-[var(--ink-muted)]">
          Sign in with NetHub identity to manage your workspace.
        </p>
        {status.message && (
          <p className="text-sm text-[var(--ink-muted)]" role="status">
            {status.message}
          </p>
        )}
        <Button type="button" disabled={!status.oidcReady || busy} onClick={() => void onSignIn()}>
          {busy ? "Redirecting…" : "Sign in"}
        </Button>
      </div>
    );
  }

  const { me, memberships, selectedMerchantId, merchant, payments, dataError } = status;

  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--ink)]">
      <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-8 md:flex-row">
        <aside className="w-full shrink-0 md:w-56">
          <div className="mb-6">
            <p className="text-xs font-semibold uppercase tracking-wide text-[var(--ink-muted)]">
              NetPay
            </p>
            <p className="text-sm font-medium">{me.email}</p>
          </div>
          <nav className="flex flex-col gap-1" aria-label="Dashboard">
            {NAV.map((item) => (
              <span
                key={item.label}
                className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm ${
                  item.active
                    ? "bg-[var(--surface)] font-medium"
                    : "text-[var(--ink-muted)]"
                }`}
              >
                <item.icon className="size-4" aria-hidden />
                {item.label}
              </span>
            ))}
          </nav>
          <Button type="button" variant="secondary" className="mt-6 w-full" onClick={onSignOut}>
            <LogOut className="size-4" aria-hidden />
            Sign out
          </Button>
        </aside>

        <main className="flex min-w-0 flex-1 flex-col gap-4">
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
              <ul className="mt-3 space-y-2 text-sm" role="list">
                {memberships.map((m) => {
                  const selected = selectedMerchantId === m.merchant_id;
                  return (
                    <li key={m.merchant_id}>
                      <button
                        type="button"
                        onClick={() => void onSelectMerchant(m.merchant_id)}
                        className={`flex w-full items-center justify-between gap-2 rounded-lg border px-3 py-2 text-left ${
                          selected
                            ? "border-[var(--accent)] bg-[var(--surface)]"
                            : "border-[var(--line)]"
                        }`}
                        aria-pressed={selected}
                      >
                        <span className="font-medium">
                          {m.merchant_name || m.merchant_slug || m.merchant_id}
                        </span>
                        <Badge>{m.role}</Badge>
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
            {memberships.length > 1 && !selectedMerchantId && (
              <p className="mt-3 text-sm text-[var(--ink-muted)]">
                Select a merchant to load summary and recent payments.
              </p>
            )}
          </Card>

          {selectedMerchantId && (
            <>
              <Card>
                <h2 className="text-sm font-semibold">Merchant summary</h2>
                {dataError && (
                  <p className="mt-3 text-sm text-[var(--ink-muted)]" role="alert">
                    {dataError}
                  </p>
                )}
                {!dataError && !merchant && (
                  <p className="mt-3 text-sm text-[var(--ink-muted)]">Loading merchant…</p>
                )}
                {merchant && (
                  <dl className="mt-3 space-y-2 text-sm">
                    <div className="flex justify-between gap-2">
                      <dt className="text-[var(--ink-muted)]">Name</dt>
                      <dd className="font-medium">{merchant.name}</dd>
                    </div>
                    <div className="flex justify-between gap-2">
                      <dt className="text-[var(--ink-muted)]">Slug</dt>
                      <dd className="font-medium">{merchant.slug}</dd>
                    </div>
                    <div className="flex justify-between gap-2">
                      <dt className="text-[var(--ink-muted)]">Status</dt>
                      <dd>
                        <Badge>{merchant.status}</Badge>
                      </dd>
                    </div>
                    <div className="flex justify-between gap-2">
                      <dt className="text-[var(--ink-muted)]">Currency</dt>
                      <dd className="font-medium">{merchant.default_currency}</dd>
                    </div>
                  </dl>
                )}
              </Card>

              <Card>
                <h2 className="text-sm font-semibold">Recent payments</h2>
                {payments.length === 0 ? (
                  <p className="mt-3 text-sm text-[var(--ink-muted)]">
                    No payments yet for this merchant, or none visible with your membership.
                  </p>
                ) : (
                  <ul className="mt-3 divide-y divide-[var(--line)] text-sm">
                    {payments.map((p) => (
                      <li key={p.id} className="flex flex-wrap items-center justify-between gap-2 py-2">
                        <div>
                          <p className="font-medium">{p.merchant_reference}</p>
                          <p className="text-[var(--ink-muted)]">{p.payment_source}</p>
                        </div>
                        <div className="text-right">
                          <p className="font-medium">{formatAmount(p.amount_minor, p.currency)}</p>
                          <Badge>{p.status}</Badge>
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </Card>
            </>
          )}

          {memberships.length === 0 && (
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
          )}
        </main>
      </div>
    </div>
  );
}
