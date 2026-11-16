import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { PublicSiteFrame } from "../../components/PublicSiteFrame";
import { Button, Card } from "../../components/ui";
import { siteUrl } from "../../lib/site-url";

export const metadata: Metadata = {
  title: "Features",
  description:
    "Available NetPay capabilities for accepting supported M-Pesa payments, receiving outcomes, and connecting them to business systems.",
  alternates: { canonical: "/features/" },
  openGraph: {
    title: "Features | NetPay",
    description: "Factual overview of available payment capabilities.",
    url: `${siteUrl}/features/`,
  },
  robots: { index: true, follow: true },
};

const features = [
  {
    title: "Supported payment requests",
    status: "Available now",
    body: "Initiate STK Push payment requests through each merchant’s own Daraja setup. Amount and shortcode rules follow the configured merchant.",
  },
  {
    title: "Payment outcome recording",
    status: "Available now",
    body: "Receive and store provider-informed outcomes. NetPay does not invent success from request acceptance alone.",
  },
  {
    title: "Merchant-isolated setup",
    status: "Available now",
    body: "Each merchant brings their own credentials and shortcode. Application integrations use a consistent surface across merchants.",
  },
  {
    title: "Optional C2B handling",
    status: "Available with configuration",
    body: "C2B URL registration and confirmation handling are available when explicitly enabled for a merchant. STK-only merchants are not forced into C2B.",
  },
  {
    title: "Callbacks and system updates",
    status: "Available with integration",
    body: "Connected systems can react to confirmed outcomes. Exact behaviour depends on the integration you build or configure.",
  },
];

export default function FeaturesPage() {
  return (
    <PublicSiteFrame>
      <section className="bg-[var(--navy)] text-[var(--on-navy)]">
        <div className="np-container py-14 sm:py-20">
          <p className="np-label text-[var(--on-navy-muted)]">Features</p>
          <h1 className="mt-4 max-w-3xl text-4xl font-extrabold tracking-tight sm:text-5xl">
            Capabilities you can rely on today
          </h1>
          <p className="mt-5 max-w-2xl text-base leading-7 text-[var(--on-navy-muted)] sm:text-lg">
            Organised around business outcomes. Every item states availability and any required configuration. We do not list unimplemented features as available.
          </p>
        </div>
      </section>

      <section className="bg-[var(--bg)]">
        <div className="np-container py-[var(--space-section-y)]">
          <div className="space-y-4">
            {features.map((f) => (
              <Card key={f.title} className="flex flex-col gap-3 p-6 sm:flex-row sm:items-start sm:justify-between">
                <div className="max-w-2xl">
                  <h2 className="text-lg font-bold">{f.title}</h2>
                  <p className="mt-2 text-sm leading-6 text-[var(--muted)]">{f.body}</p>
                </div>
                <span className="shrink-0 rounded-full bg-[var(--accent-soft)] px-3 py-1.5 text-xs font-semibold text-[var(--teal-dark)]">
                  {f.status}
                </span>
              </Card>
            ))}
          </div>

          <Card className="mx-auto mt-12 max-w-3xl p-6 text-center sm:p-8">
            <h2 className="text-xl font-bold">Not claimed on this site</h2>
            <p className="mt-3 text-sm leading-6 text-[var(--muted)]">
              Payment links as a product surface, POS hardware, card payments, other mobile-money rails, or automatic till reconciliation of every walk-in sale are not marketed as NetPay capabilities unless and until they are verified in production.
            </p>
            <div className="mt-6 flex flex-wrap justify-center gap-3">
              <Button href="/request-access/" variant="primary" size="md">
                Request access
              </Button>
              <Link href="/developers/" className="inline-flex items-center gap-1 text-sm font-semibold text-[var(--accent)] hover:underline">
                Developers <ArrowRight size={14} aria-hidden />
              </Link>
            </div>
          </Card>
        </div>
      </section>
    </PublicSiteFrame>
  );
}
