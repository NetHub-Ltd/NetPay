import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";
import { PublicSiteFrame } from "../../components/PublicSiteFrame";
import { getCurrentSession } from "../../lib/server/session-store";

export const metadata: Metadata = {
  title: "Sign in",
  description: "Sign in securely to your NetPay merchant workspace.",
  alternates: { canonical: "/login/" },
  robots: { index: false, follow: false, noarchive: true, nosnippet: true },
};
type LoginPageProps = { searchParams: Promise<{ error?: string }> };
const ERROR_MESSAGES: Record<string, string> = {
  configuration: "Sign-in is temporarily unavailable. Please contact the NetPay team.",
  provider: "The identity provider could not complete sign-in. Please try again.",
  state: "Your sign-in session expired or could not be validated. Start again.",
  exchange: "We could not complete your secure sign-in. Please try again.",
};
export default async function LoginPage({ searchParams }: LoginPageProps) {
  const params = await searchParams;
  const errorMessage = params.error ? ERROR_MESSAGES[params.error] : undefined;
  const current = await getCurrentSession().catch(() => null);
  if (current) redirect("/dashboard/");
  return (
    <PublicSiteFrame>
      <main id="main-content" className="mx-auto flex min-h-[72vh] max-w-7xl items-center justify-center px-6 py-16">
        <section className="w-full max-w-lg rounded-3xl border border-[var(--line)] bg-[var(--surface)] p-8 shadow-[var(--shadow-sm)] sm:p-10">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--accent)]">NetPay account</p>
          <h1 className="mt-4 text-3xl font-extrabold tracking-tight text-[var(--ink)]">Welcome back.</h1>
          <p className="mt-3 text-sm leading-6 text-[var(--muted)]">
            Sign in with your NetHub identity to access your merchant workspace and payment activity.
          </p>
          {errorMessage ? (
            <p className="mt-6 rounded-xl border border-[var(--danger)] bg-[var(--danger-soft)] px-4 py-3 text-sm text-[var(--danger)]" role="alert">
              {errorMessage}
            </p>
          ) : null}
          <Link
            href="/api/auth/login?returnTo=%2Fdashboard%2F"
            className="mt-8 inline-flex min-h-12 w-full items-center justify-center rounded-xl bg-[var(--accent)] px-5 py-3 text-sm font-semibold text-[var(--on-accent)] transition hover:brightness-95 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--accent)]"
          >
            Continue with NetHub
          </Link>
          <p className="mt-6 text-center text-xs leading-5 text-[var(--muted)]">
            Authentication is handled securely by NetHub. NetPay never receives your password.
          </p>
        </section>
      </main>
    </PublicSiteFrame>
  );
}
