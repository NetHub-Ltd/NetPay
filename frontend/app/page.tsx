import type { Metadata } from "next";
import Link from "next/link";
import {
  ArrowDownLeft,
  ArrowRight,
  CheckCircle2,
  ShieldCheck,
  Smartphone,
  Wallet,
  Webhook,
} from "lucide-react";
import { PublicSiteFrame } from "../components/PublicSiteFrame";
import { Button, Card } from "../components/ui";
import { siteUrl } from "../lib/site-url";

export const metadata: Metadata = {
  title: "M-Pesa Daraja API for business software",
  description:
    "Integrate M-Pesa STK Push into POS, commerce, and business apps using each merchant's Daraja setup. Track outcomes from provider evidence.",
  alternates: { canonical: "/" },
  openGraph: {
    type: "website",
    locale: "en_KE",
    url: siteUrl,
    title: "M-Pesa Daraja API for business software | NetPay",
    description:
      "A merchant-aware M-Pesa gateway for POS, commerce, and business applications. Start with STK Push and use provider evidence for payment outcomes.",
  },
  twitter: {
    card: "summary_large_image",
    title: "M-Pesa Daraja API for business software | NetPay",
    description:
      "Integrate STK Push into business software using each merchant's Daraja setup and track provider-informed outcomes.",
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
        "An M-Pesa Daraja gateway for merchant-owned integrations, STK Push, and provider-informed payment outcomes.",
      publisher: { "@id": `${siteUrl}/#organization` },
    },
  ],
};

const capabilities = [
  {
    icon: Smartphone,
    title: "STK Push at the core",
    text: "Initiate customer payment prompts from your application through a connected merchant's Daraja setup.",
  },
  {
    icon: Wallet,
    title: "One setup per merchant",
    text: "Each merchant supplies their own shortcode and credentials; your application uses a consistent integration surface.",
  },
  {
    icon: Webhook,
    title: "Outcomes from provider evidence",
    text: "Use callbacks and payment events to update your own workflow. An accepted request is not proof of payment.",
  },
  {
    icon: ArrowDownLeft,
    title: "C2B when you need it",
    text: "C2B registration is optional. STK-only merchants do not need to register C2B URLs.",
  },
];

const workflow = [
  {
    step: "01",
    title: "Connect a merchant",
    description: "Configure that business's Daraja shortcode and credentials through the supported onboarding flow.",
  },
  {
    step: "02",
    title: "Start an STK Push",
    description: "Your server sends a payment request to NetPay using the merchant integration and your order reference.",
  },
  {
    step: "03",
    title: "Act on the outcome",
    description: "Use provider-backed status and supported payment events to update your application's order flow.",
  },
];

export default function HomePage() {
  return (
    <PublicSiteFrame>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
      />
      <main id="main-content">
        <section className="bg-[var(--navy)] text-[var(--on-navy)]">
          <div className="np-container grid gap-12 py-14 sm:py-20 lg:grid-cols-[1.05fr_.95fr] lg:items-center lg:gap-16 lg:py-24">
            <div>
              <p className="np-label text-[var(--on-navy-muted)]">
                M-Pesa Daraja API for business software
              </p>
              <h1 className="mt-5 max-w-3xl text-4xl font-extrabold leading-tight tracking-tight text-[var(--on-navy)] sm:text-5xl lg:text-6xl">
                Connect your product to M-Pesa, merchant by merchant.
              </h1>
              <p className="mt-6 max-w-2xl text-base leading-7 text-[var(--on-navy-muted)] sm:text-lg sm:leading-8">
                NetPay gives POS, commerce, and business applications a consistent server-side
                integration for merchant-owned Daraja setups. Start with STK Push, then use provider
                evidence to understand the payment outcome.
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <Button
                  href="/request-access/"
                  variant="onNavy"
                  size="lg"
                  rightIcon={<ArrowRight size={17} aria-hidden />}
                >
                  Request API access
                </Button>
                <Link
                  href="/api-overview/"
                  className="inline-flex min-h-12 items-center justify-center gap-2 rounded-full border border-[var(--on-navy-border)] px-5 py-3 text-sm font-semibold text-[var(--on-navy)] transition hover:bg-[var(--on-navy-faint)] focus-visible:outline-[var(--focus-ring)]"
                >
                  Review the API
                </Link>
              </div>
              <ul className="mt-7 flex flex-wrap gap-x-6 gap-y-3 text-sm text-[var(--on-navy-muted)]">
                <li className="inline-flex items-center gap-2">
                  <CheckCircle2 size={16} aria-hidden className="text-[var(--accent)]" />
                  Merchant-owned Daraja credentials
                </li>
                <li className="inline-flex items-center gap-2">
                  <CheckCircle2 size={16} aria-hidden className="text-[var(--accent)]" />
                  C2B registration is optional
                </li>
              </ul>
            </div>

            <aside
              aria-labelledby="payment-flow-title"
              className="rounded-3xl border border-[var(--on-navy-border)] bg-[var(--panel)] p-5 text-[var(--ink)] shadow-[var(--shadow-lg)] sm:p-7"
            >
              <div className="flex flex-wrap items-start justify-between gap-3 border-b border-[var(--line)] pb-5">
                <div>
                  <p className="np-label">Illustrative flow</p>
                  <h2 id="payment-flow-title" className="mt-2 text-xl font-bold sm:text-2xl">
                    From request to outcome
                  </h2>
                </div>
                <span className="rounded-full bg-[var(--accent-soft)] px-3 py-1.5 text-xs font-semibold text-[var(--teal-dark)]">
                  Example only
                </span>
              </div>
              <ol className="mt-5 space-y-5">
                {workflow.map((item, index) => (
                  <li key={item.step} className="flex gap-4">
                    <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-[var(--surface)] text-sm font-bold text-[var(--teal-dark)]">
                      {item.step}
                    </span>
                    <div className="pt-0.5">
                      <h3 className="font-bold">{item.title}</h3>
                      <p className="mt-1 text-sm leading-6 text-[var(--muted)]">{item.description}</p>
                    </div>
                    {index < workflow.length - 1 ? null : (
                      <ShieldCheck className="ml-auto mt-1 shrink-0 text-[var(--teal-dark)]" size={19} aria-hidden />
                    )}
                  </li>
                ))}
              </ol>
              <p className="mt-6 rounded-xl border border-[var(--line)] bg-[var(--surface)] p-4 text-sm leading-6 text-[var(--muted)]">
                An accepted STK Push request only confirms the prompt was accepted. It does not
                confirm that the customer paid.
              </p>
            </aside>
          </div>
        </section>

        <section className="np-section bg-[var(--bg)]">
          <div className="np-container">
            <div className="max-w-3xl">
              <p className="np-label text-[var(--teal-dark)]">Built for software teams</p>
              <h2 className="np-h2 mt-3">
                M-Pesa payment workflows that fit the product you already run.
              </h2>
              <p className="np-lead mt-4">
                Keep checkout, orders, and business rules in your application. NetPay provides an
                integration boundary for merchant collections and payment updates.
              </p>
            </div>
            <div className="mt-9 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {capabilities.map(({ icon: Icon, title, text }) => (
                <Card key={title} className="h-full p-5 sm:p-6">
                  <span className="grid size-11 place-items-center rounded-xl bg-[var(--accent-soft)] text-[var(--teal-dark)]">
                    <Icon size={21} aria-hidden />
                  </span>
                  <h3 className="mt-5 text-lg font-bold">{title}</h3>
                  <p className="mt-2 text-sm leading-6 text-[var(--muted)]">{text}</p>
                </Card>
              ))}
            </div>
          </div>
        </section>

        <section className="bg-[var(--surface)] py-[var(--space-section-y)]">
          <div className="np-container grid gap-10 lg:grid-cols-[.8fr_1.2fr] lg:items-start">
            <div>
              <p className="np-label text-[var(--teal-dark)]">How integration works</p>
              <h2 className="np-h2 mt-3">A clear path from merchant setup to your order flow.</h2>
              <p className="mt-4 text-base leading-7 text-[var(--muted)]">
                Your application remains in control of its checkout and business rules. NetPay does
                not treat initiation acceptance as payment success.
              </p>
              <Link
                href="/developers/"
                className="mt-6 inline-flex min-h-11 items-center gap-2 font-semibold text-[var(--teal-dark)] hover:underline focus-visible:outline-[var(--focus-ring)]"
              >
                Explore developer guidance <ArrowRight size={17} aria-hidden />
              </Link>
            </div>
            <ol className="grid gap-4 md:grid-cols-3">
              {workflow.map((item) => (
                <li key={item.step} className="rounded-2xl border border-[var(--line)] bg-[var(--panel)] p-5">
                  <span className="text-sm font-bold text-[var(--teal-dark)]">{item.step}</span>
                  <h3 className="mt-3 font-bold">{item.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-[var(--muted)]">{item.description}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        <section className="np-section bg-[var(--bg)]">
          <div className="np-container">
            <div className="grid gap-5 md:grid-cols-2">
              <article className="rounded-3xl bg-[var(--navy)] p-6 text-[var(--on-navy)] sm:p-8">
                <h2 className="text-xl font-bold text-[var(--on-navy)] sm:text-2xl">
                  Know what a payment status means.
                </h2>
                <p className="mt-3 text-sm leading-7 text-[var(--on-navy-muted)]">
                  Initiation acceptance is not payment confirmation. Use callback-backed results and
                  documented API behavior when your software updates an order.
                </p>
                <Link
                  href="/api-overview/"
                  className="mt-5 inline-flex items-center gap-2 font-semibold text-[var(--on-navy-accent)] hover:underline focus-visible:outline-[var(--focus-ring)]"
                >
                  Read the API overview <ArrowRight size={16} aria-hidden />
                </Link>
              </article>
              <article className="rounded-3xl border border-[var(--line)] bg-[var(--panel)] p-6 sm:p-8">
                <h2 className="text-xl font-bold sm:text-2xl">Start with the capabilities you need.</h2>
                <p className="mt-3 text-sm leading-7 text-[var(--muted)]">
                  STK Push is central to the integration. C2B is opt-in, and Daraja permissions or
                  extra setup may be needed for some capabilities.
                </p>
                <Link
                  href="/product/"
                  className="mt-5 inline-flex items-center gap-2 font-semibold text-[var(--teal-dark)] hover:underline focus-visible:outline-[var(--focus-ring)]"
                >
                  See product details <ArrowRight size={16} aria-hidden />
                </Link>
              </article>
            </div>
          </div>
        </section>

        <section className="bg-[var(--accent-soft)] py-12 sm:py-16">
          <div className="np-container flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
            <div className="max-w-2xl">
              <p className="np-label text-[var(--teal-dark)]">Your next step</p>
              <h2 className="mt-3 text-2xl font-bold tracking-tight sm:text-3xl">
                Planning an M-Pesa integration for your product?
              </h2>
              <p className="mt-3 text-sm leading-6 text-[var(--muted)] sm:text-base">
                Review the current API contract, then request access with your use case.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Button href="/request-access/" variant="primary" rightIcon={<ArrowRight size={16} aria-hidden />}>
                Request API access
              </Button>
              <Button href="/faq/" variant="secondary">
                Read the FAQ
              </Button>
            </div>
          </div>
        </section>
      </main>
    </PublicSiteFrame>
  );
}
