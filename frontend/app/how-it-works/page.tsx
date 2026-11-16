import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, CheckCircle2 } from "lucide-react";
import { PublicSiteFrame } from "../../components/PublicSiteFrame";
import { Button, Card } from "../../components/ui";
import { siteUrl } from "../../lib/site-url";

export const metadata: Metadata = {
  title: "How it works",
  description:
    "A plain-language explanation of how NetPay helps businesses accept supported M-Pesa payments and act on confirmed outcomes.",
  alternates: { canonical: "/how-it-works/" },
  openGraph: {
    title: "How NetPay works | NetPay",
    description: "From customer payment to business action — explained for business owners.",
    url: `${siteUrl}/how-it-works/`,
  },
  robots: { index: true, follow: true },
};

const steps = [
  {
    title: "You connect your merchant setup",
    body: "Each business uses its own M-Pesa shortcode and credentials. NetPay does not replace your Safaricom relationship; it works with the setup you already have or are setting up.",
  },
  {
    title: "A customer pays through a supported flow",
    body: "For example, your application can send a payment request to the customer’s phone (STK Push). The customer authorises the payment in the usual M-Pesa way.",
  },
  {
    title: "NetPay records the provider outcome",
    body: "We receive the result from the payment provider and store it against the payment attempt. A request being accepted is not treated as proof that money moved.",
  },
  {
    title: "Your connected system can take the next step",
    body: "When the outcome is confirmed, your website, app, or internal tool can update an order, booking, access, or record. You decide the business rule.",
  },
];

export default function HowItWorksPage() {
  return (
    <PublicSiteFrame>
      <section className="bg-[var(--navy)] text-[var(--on-navy)]">
        <div className="np-container py-14 sm:py-20">
          <p className="np-label text-[var(--on-navy-muted)]">How it works</p>
          <h1 className="mt-4 max-w-3xl text-4xl font-extrabold tracking-tight sm:text-5xl">
            From customer pay to business action
          </h1>
          <p className="mt-5 max-w-2xl text-base leading-7 text-[var(--on-navy-muted)] sm:text-lg">
            NetPay is designed so a non-technical business owner can understand the journey, while developers get the integration detail they need on the developers page.
          </p>
        </div>
      </section>

      <section className="bg-[var(--bg)]">
        <div className="np-container py-[var(--space-section-y)]">
          <ol className="mx-auto max-w-3xl space-y-8">
            {steps.map((s, i) => (
              <li key={s.title} className="flex gap-5">
                <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-[var(--accent-soft)] text-sm font-bold text-[var(--teal-dark)]">
                  {i + 1}
                </span>
                <div>
                  <h2 className="text-xl font-bold">{s.title}</h2>
                  <p className="mt-2 text-base leading-7 text-[var(--muted)]">{s.body}</p>
                </div>
              </li>
            ))}
          </ol>

          <Card className="mx-auto mt-14 max-w-3xl p-6 sm:p-8">
            <h2 className="text-lg font-bold">What this is not</h2>
            <ul className="mt-4 space-y-2 text-sm leading-6 text-[var(--muted)]">
              <li className="flex gap-2">
                <CheckCircle2 size={16} className="mt-0.5 shrink-0 text-[var(--accent)]" aria-hidden />
                NetPay is not a full point-of-sale or inventory system (see Tawala for that).
              </li>
              <li className="flex gap-2">
                <CheckCircle2 size={16} className="mt-0.5 shrink-0 text-[var(--accent)]" aria-hidden />
                We do not claim automatic matching of every walk-in till sale unless that exact workflow is supported and configured.
              </li>
              <li className="flex gap-2">
                <CheckCircle2 size={16} className="mt-0.5 shrink-0 text-[var(--accent)]" aria-hidden />
                Pending or failed outcomes are recorded honestly; we do not invent success.
              </li>
            </ul>
            <div className="mt-6 flex flex-wrap gap-3">
              <Button href="/request-access/" variant="primary" size="md">
                Discuss your setup
              </Button>
              <Link href="/mpesa-payments/" className="inline-flex items-center gap-1 text-sm font-semibold text-[var(--accent)] hover:underline">
                M-Pesa details <ArrowRight size={14} aria-hidden />
              </Link>
            </div>
          </Card>
        </div>
      </section>
    </PublicSiteFrame>
  );
}
