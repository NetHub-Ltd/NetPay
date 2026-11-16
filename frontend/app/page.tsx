import type { Metadata } from "next";
import Link from "next/link";
import {
  ArrowRight,
  CheckCircle2,
  ShieldCheck,
  Smartphone,
  Store,
  Webhook,
} from "lucide-react";
import { PublicSiteFrame } from "../components/PublicSiteFrame";
import { Button, Card } from "../components/ui";
import { siteUrl } from "../lib/site-url";

export const metadata: Metadata = {
  title: "Payments that work for your business",
  description:
    "NetPay helps businesses in Kenya accept and manage supported M-Pesa payments, receive clear payment outcomes, and connect those outcomes to how the business works.",
  alternates: { canonical: "/" },
  openGraph: {
    type: "website",
    locale: "en_KE",
    url: siteUrl,
    title: "NetPay — Payments that work for your business",
    description:
      "Accept and manage supported M-Pesa payments with clearer outcomes. Built for physical shops, online stores, service businesses, and software teams in Kenya.",
  },
  twitter: {
    card: "summary_large_image",
    title: "NetPay — Payments that work for your business",
    description:
      "Accept and manage supported M-Pesa payments with clearer outcomes for businesses in Kenya.",
  },
  robots: { index: true, follow: true },
};

const structuredData = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": `${siteUrl}/#organization`,
      name: "NetHub",
      url: "https://nethub.co.ke",
    },
    {
      "@type": "WebSite",
      "@id": `${siteUrl}/#website`,
      url: siteUrl,
      name: "NetPay",
      publisher: { "@id": `${siteUrl}/#organization` },
      inLanguage: "en-KE",
    },
    {
      "@type": "SoftwareApplication",
      "@id": `${siteUrl}/#software`,
      name: "NetPay",
      url: siteUrl,
      applicationCategory: "FinanceApplication",
      operatingSystem: "Web",
      description:
        "A business payment solution that helps Kenyan businesses accept and manage supported M-Pesa payments and receive clear payment outcomes.",
      publisher: { "@id": `${siteUrl}/#organization` },
    },
  ],
};

const pillars = [
  {
    icon: Smartphone,
    title: "Make paying easier",
    text: "Give customers a convenient way to pay through supported M-Pesa flows that fit how your business already operates.",
  },
  {
    icon: CheckCircle2,
    title: "Know when you have been paid",
    text: "Receive clear payment outcomes from the provider so your team and systems can act on confirmed results, not screenshots.",
  },
  {
    icon: Webhook,
    title: "Connect payments to how you work",
    text: "When a payment is confirmed, your connected application can move the next step—order, booking, access, or record-keeping.",
  },
  {
    icon: Store,
    title: "Built for real businesses",
    text: "Physical shops, online stores, service businesses, and software teams. NetPay focuses on payment workflows; Tawala covers POS and broader business management.",
  },
];

const flowSteps = [
  {
    step: "1",
    title: "Customer pays",
    description: "Your customer completes a supported M-Pesa payment (for example a payment request sent to their phone).",
  },
  {
    step: "2",
    title: "Outcome is received",
    description: "NetPay receives and records the payment outcome from the provider. Acceptance of a request is not treated as proof that money moved.",
  },
  {
    step: "3",
    title: "Your system can act",
    description: "A connected application can use the confirmed outcome to update an order, booking, or internal record.",
  },
];

export default function HomePage() {
  return (
    <PublicSiteFrame>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
      />

      <section className="bg-[var(--navy)] text-[var(--on-navy)]">
        <div className="np-container grid gap-12 py-14 sm:py-20 lg:grid-cols-[1.05fr_.95fr] lg:items-center lg:gap-16 lg:py-24">
          <div>
            <p className="np-label text-[var(--on-navy-muted)]">NetPay by NetHub</p>
            <h1 className="mt-5 max-w-3xl text-4xl font-extrabold leading-tight tracking-tight text-[var(--on-navy)] sm:text-5xl lg:text-6xl">
              Getting paid should be the easy part of running your business.
            </h1>
            <p className="mt-6 max-w-2xl text-base leading-7 text-[var(--on-navy-muted)] sm:text-lg sm:leading-8">
              NetPay helps businesses accept supported M-Pesa payments, receive clear payment outcomes, and connect those outcomes to the way the business works—whether you serve customers in a shop, online, or through an app.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Button href="/request-access/" variant="onNavy" size="lg">
                Request access
              </Button>
              <Link
                href="/how-it-works/"
                className="inline-flex min-h-12 items-center justify-center gap-2 rounded-full border border-[var(--on-navy-border)] px-5 py-3 text-sm font-semibold text-[var(--on-navy)] transition hover:bg-[var(--on-navy-faint)] focus-visible:outline-[var(--focus-ring)]"
              >
                How it works <ArrowRight size={16} aria-hidden />
              </Link>
            </div>
            <ul className="mt-7 flex flex-wrap gap-x-6 gap-y-3 text-sm text-[var(--on-navy-muted)]">
              <li className="inline-flex items-center gap-2">
                <CheckCircle2 size={16} aria-hidden className="text-[var(--accent)]" />
                Merchant-owned M-Pesa setup
              </li>
              <li className="inline-flex items-center gap-2">
                <CheckCircle2 size={16} aria-hidden className="text-[var(--accent)]" />
                Outcomes from provider evidence
              </li>
            </ul>
          </div>

          <Card className="rounded-3xl border border-[var(--on-navy-border)] bg-[var(--panel)] p-5 text-[var(--ink)] shadow-[var(--shadow-lg)] sm:p-7">
            <div className="flex flex-wrap items-start justify-between gap-3 border-b border-[var(--line)] pb-5">
              <div>
                <p className="np-label">Simple payment journey</p>
                <h2 id="payment-flow-title" className="mt-2 text-xl font-bold sm:text-2xl">
                  From customer pay to business action
                </h2>
              </div>
              <span className="rounded-full bg-[var(--accent-soft)] px-3 py-1.5 text-xs font-semibold text-[var(--teal-dark)]">
                Available now
              </span>
            </div>
            <ol className="mt-5 space-y-5" aria-labelledby="payment-flow-title">
              {flowSteps.map((item) => (
                <li key={item.step} className="flex gap-4">
                  <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-[var(--surface)] text-sm font-bold text-[var(--teal-dark)]">
                    {item.step}
                  </span>
                  <div className="pt-0.5">
                    <h3 className="font-bold">{item.title}</h3>
                    <p className="mt-1 text-sm leading-6 text-[var(--muted)]">{item.description}</p>
                  </div>
                </li>
              ))}
            </ol>
            <p className="mt-6 rounded-xl border border-[var(--line)] bg-[var(--surface)] px-4 py-3 text-sm leading-6 text-[var(--muted)]">
              <ShieldCheck className="mr-2 inline-block align-text-bottom text-[var(--teal-dark)]" size={16} aria-hidden />
              NetPay does not treat a payment request being accepted as proof that money moved. Outcomes follow provider evidence.
            </p>
          </Card>
        </div>
      </section>

      <section className="bg-[var(--bg)]">
        <div className="np-container py-[var(--space-section-y)]">
          <div className="mx-auto max-w-2xl text-center">
            <p className="np-label">Why businesses use NetPay</p>
            <h2 className="mt-3 text-3xl font-extrabold tracking-tight sm:text-4xl">
              Payments that fit the way you work
            </h2>
            <p className="mt-4 text-base leading-7 text-[var(--muted)] sm:text-lg">
              We speak to the person responsible for running the business. Technical detail is available for developers when you are ready to integrate.
            </p>
          </div>
          <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {pillars.map((p) => (
              <Card key={p.title} className="flex flex-col gap-4 p-6">
                <span className="grid size-11 place-items-center rounded-xl bg-[var(--accent-soft)] text-[var(--teal-dark)]">
                  <p.icon size={22} aria-hidden />
                </span>
                <h3 className="text-lg font-bold">{p.title}</h3>
                <p className="text-sm leading-6 text-[var(--muted)]">{p.text}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      <section className="bg-[var(--surface)]">
        <div className="np-container py-[var(--space-section-y)]">
          <div className="grid gap-10 lg:grid-cols-[1fr_1.1fr] lg:items-center">
            <div>
              <p className="np-label">Who NetPay is for</p>
              <h2 className="mt-3 text-3xl font-extrabold tracking-tight sm:text-4xl">
                Physical and digital businesses in Kenya
              </h2>
              <p className="mt-4 text-base leading-7 text-[var(--muted)]">
                NetPay is for businesses that need a reliable way to accept supported M-Pesa payments and know what happened next. It is not a full POS or shop-management system—that is Tawala’s role.
              </p>
              <ul className="mt-6 space-y-3 text-sm leading-6 text-[var(--ink)]">
                <li className="flex gap-3">
                  <CheckCircle2 size={18} className="mt-0.5 shrink-0 text-[var(--accent)]" aria-hidden />
                  Retail and physical locations that want clearer payment confirmation
                </li>
                <li className="flex gap-3">
                  <CheckCircle2 size={18} className="mt-0.5 shrink-0 text-[var(--accent)]" aria-hidden />
                  Online stores and apps that need payment outcomes tied to orders or access
                </li>
                <li className="flex gap-3">
                  <CheckCircle2 size={18} className="mt-0.5 shrink-0 text-[var(--accent)]" aria-hidden />
                  Service and booking businesses that confirm payment before proceeding
                </li>
              </ul>
              <div className="mt-8">
                <Button href="/solutions/" variant="primary" size="md">
                  See business solutions
                </Button>
              </div>
            </div>
            <Card className="p-6 sm:p-8">
              <h3 className="text-lg font-bold">Supported today</h3>
              <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
                NetPay’s current foundation is M-Pesa Daraja. Merchants use their own shortcode and credentials. Core capability is STK Push with provider-informed outcomes; C2B support is available where configured.
              </p>
              <div className="mt-6 flex flex-wrap gap-3">
                <Link href="/mpesa-payments/" className="text-sm font-semibold text-[var(--accent)] hover:underline">
                  M-Pesa payments →
                </Link>
                <Link href="/features/" className="text-sm font-semibold text-[var(--accent)] hover:underline">
                  Features →
                </Link>
                <Link href="/developers/" className="text-sm font-semibold text-[var(--accent)] hover:underline">
                  Developers →
                </Link>
              </div>
            </Card>
          </div>
        </div>
      </section>

      <section className="bg-[var(--bg)]">
        <div className="np-container py-[var(--space-section-y)]">
          <Card className="mx-auto max-w-3xl border-[var(--line)] p-8 text-center sm:p-10">
            <h2 className="text-2xl font-extrabold tracking-tight sm:text-3xl">
              Ready to discuss your payment setup?
            </h2>
            <p className="mt-4 text-base leading-7 text-[var(--muted)]">
              Tell us how your business receives payments today. We will map a practical path using the capabilities that are available now.
            </p>
            <div className="mt-8 flex flex-wrap justify-center gap-3">
              <Button href="/request-access/" variant="primary" size="lg">
                Request access
              </Button>
              <Button href="/how-it-works/" variant="secondary" size="lg">
                How it works
              </Button>
            </div>
          </Card>
        </div>
      </section>
    </PublicSiteFrame>
  );
}
