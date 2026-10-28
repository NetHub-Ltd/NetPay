import type { Metadata } from "next";
import {
  ArrowRight,
  CheckCircle2,
  Code2,
  ShieldCheck,
  Smartphone,
  Workflow,
} from "lucide-react";
import { SiteHeader } from "../components/SiteHeader";
import { Badge, Button, Card, Container, Section } from "../components/ui";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "https://pay.nethub.co.ke";

export const metadata: Metadata = {
  title: "M-Pesa payment API for business software",
  description:
    "Connect business software to M-Pesa with merchant-owned Daraja integrations, STK Push, and payment events grounded in provider results.",
  alternates: { canonical: "/" },
  openGraph: {
    type: "website",
    locale: "en_KE",
    url: siteUrl,
    title: "NetPay | M-Pesa payment API for business software",
    description:
      "A consistent M-Pesa payments API for merchants, POS systems, and business applications.",
  },
  twitter: {
    card: "summary_large_image",
    title: "NetPay | M-Pesa payment API for business software",
    description: "Merchant-owned Daraja integrations and payment events for business software.",
  },
  robots: {
    index: true,
    follow: true,
  },
};

const structuredData = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": `${siteUrl}/#organization`,
      name: "NetHub",
      url: "https://nethub.co.ke",
      logo: `${siteUrl}/opengraph-image`,
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
        "An M-Pesa payments gateway for merchant-owned Daraja integrations, STK Push, and provider-informed payment status.",
      publisher: { "@id": `${siteUrl}/#organization` },
    },
  ],
};

const capabilities = [
  {
    icon: Smartphone,
    title: "M-Pesa checkout",
    description:
      "Send a payment prompt to a customer’s phone and track the provider-confirmed result.",
  },
  {
    icon: Workflow,
    title: "One API, many merchants",
    description:
      "Keep each merchant’s Daraja integration isolated while your product uses one consistent API.",
  },
  {
    icon: ShieldCheck,
    title: "Built for dependable state",
    description:
      "Idempotency, callback deduplication, and durable payment events help your systems recover safely.",
  },
  {
    icon: Code2,
    title: "Made for software teams",
    description:
      "Integrate from a website, POS, or business application using documented API contracts.",
  },
];

const steps = [
  "Onboard a merchant with their own Daraja credentials",
  "Initiate STK Push from your application via the NetPay API",
  "Receive a durable payment event when provider evidence changes state",
];

export default function HomePage() {
  return (
    <>
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-[var(--panel)] focus:px-4 focus:py-3 focus:font-semibold focus:text-[var(--navy)] focus:shadow-[var(--shadow)]"
      >
        Skip to content
      </a>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
      />

      <SiteHeader />

      <main id="main-content" tabIndex={-1}>
        {/* Hero */}
        <section className="relative overflow-hidden bg-[var(--navy)] text-[var(--on-navy)]">
          <div
            aria-hidden="true"
            className="pointer-events-none absolute -right-24 -top-24 size-[28rem] rounded-full border border-white/5"
          />
          <Container className="relative grid gap-12 py-16 lg:grid-cols-[1.15fr_0.85fr] lg:items-center lg:py-24">
            <div>
              <Badge tone="onNavy">M-Pesa infrastructure for software</Badge>
              <h1 className="mt-6 max-w-3xl text-4xl font-extrabold leading-[1.08] tracking-tight sm:text-5xl lg:text-6xl">
                Collect M-Pesa payments with state you can trust.
              </h1>
              <p className="mt-6 max-w-2xl text-lg leading-8 text-[var(--on-navy-muted)]">
                NetPay connects your product to merchant-owned Daraja integrations. Initiate STK Push,
                host callbacks, and publish durable payment events—without treating initiation as proof
                of payment.
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <Button href="/api-overview/" variant="onNavy" size="lg" rightIcon={<ArrowRight size={17} aria-hidden />}>
                  API overview
                </Button>
                <Button href="/request-access/" variant="onNavyOutline" size="lg">
                  Request access
                </Button>
              </div>
              <p className="mt-4 text-sm text-[var(--on-navy-muted)]">
                <a href="#how-it-works" className="underline-offset-2 hover:underline">How it works</a>
                {" · "}
                <a href="#capabilities" className="underline-offset-2 hover:underline">Capabilities</a>
                {" · "}
                <a href="/faq/" className="underline-offset-2 hover:underline">FAQ</a>
              </p>
            </div>
            <Card
              elevated
              className="border-white/10 bg-[var(--navy-soft)] p-6 text-[var(--on-navy)] sm:p-8"
            >
              <p className="text-sm font-bold uppercase tracking-[0.14em] text-[var(--teal)]">
                Payment truth
              </p>
              <h2 className="mt-2 text-2xl font-bold tracking-tight">One clear source of truth</h2>
              <ul className="mt-6 space-y-4">
                {[
                  "Provider-confirmed results drive status—not guesses",
                  "Idempotent STK initiation and callback deduplication",
                  "Optional signed webhooks when your workflow needs them",
                ].map((item) => (
                  <li key={item} className="flex gap-3 text-sm leading-6 text-[var(--on-navy-muted)]">
                    <CheckCircle2 className="mt-0.5 size-5 shrink-0 text-[var(--teal)]" aria-hidden />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </Card>
          </Container>
        </section>

        <Section id="capabilities" className="bg-[var(--bg)]">
          <Badge>Capabilities</Badge>
          <h2 className="mt-4 text-3xl font-bold tracking-tight sm:text-4xl">
            The payment API is only the beginning.
          </h2>
          <p className="mt-4 max-w-2xl text-lg text-[var(--muted)]">
            A consistent surface for software teams: merchant isolation, reliable state, and contracts
            you can build against.
          </p>
          <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {capabilities.map(({ icon: Icon, title, description }) => (
              <Card key={title} elevated className="h-full">
                <span className="grid size-12 place-items-center rounded-2xl bg-[var(--teal-soft)] text-[var(--teal-dark)]">
                  <Icon size={22} aria-hidden />
                </span>
                <h3 className="mt-5 text-lg font-bold tracking-tight">{title}</h3>
                <p className="mt-2 text-sm leading-6 text-[var(--muted)]">{description}</p>
              </Card>
            ))}
          </div>
        </Section>

        <Section id="how-it-works" className="bg-[var(--surface)]">
          <div className="grid gap-12 lg:grid-cols-2 lg:items-start">
            <div>
              <Badge>How it works</Badge>
              <h2 className="mt-4 text-3xl font-bold tracking-tight sm:text-4xl">
                Connect once. Know what happened.
              </h2>
              <p className="mt-5 text-lg leading-8 text-[var(--muted)]">
                Use the merchant’s Daraja credentials, initiate a payment from your application, and
                listen for a durable event when provider evidence changes its state.
              </p>
              <ol className="mt-8 space-y-5">
                {steps.map((step, index) => (
                  <li key={step} className="flex gap-4">
                    <span className="grid size-8 shrink-0 place-items-center rounded-full bg-[var(--ink)] text-sm font-bold text-[var(--on-navy)]">
                      {index + 1}
                    </span>
                    <p className="pt-1 font-semibold text-[var(--ink)]">{step}</p>
                  </li>
                ))}
              </ol>
            </div>
            <div
              id="developers"
              className="overflow-hidden rounded-[var(--radius-xl)] bg-[var(--navy)] p-6 text-[var(--on-navy)] shadow-[var(--shadow-lg)] sm:p-8"
            >
              <div className="flex items-center justify-between border-b border-white/10 pb-4">
                <p className="font-bold">Example request</p>
                <Badge tone="onNavy">HTTP</Badge>
              </div>
              <pre className="mt-6 overflow-x-auto font-mono text-sm leading-7 text-[var(--on-navy-muted)]">
                <code>{`POST /api/v1/payments/stk-push
Authorization: Bearer <access-token>
Idempotency-Key: order-123-attempt-1
Content-Type: application/json

{
  "integration_id": "<merchant-integration-id>",
  "client_reference": "order-123",
  "amount_minor": 250000,
  "currency": "KES",
  "phone_number": "0712345678",
  "description": "Order payment"
}`}</code>
              </pre>
              <div className="mt-6 rounded-[var(--radius)] border border-[var(--teal)]/30 bg-[var(--teal)]/10 p-4 text-sm leading-6 text-[var(--teal-soft)]">
                NetPay returns a payment resource. It never treats the STK initiation acknowledgement as
                proof of payment.
              </div>
            </div>
          </div>
        </Section>

        <Section className="bg-[var(--bg)] py-16 lg:py-20">
          <div className="flex flex-col gap-8 rounded-[var(--radius-xl)] bg-[var(--ink)] px-7 py-10 text-[var(--on-navy)] sm:px-10 md:flex-row md:items-center md:justify-between lg:px-14 lg:py-12">
            <div className="max-w-2xl">
              <Badge tone="onNavy">For builders and businesses</Badge>
              <h2 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">
                Make payments a reliable part of your product.
              </h2>
              <p className="mt-4 leading-7 text-[var(--on-navy-muted)]">
                Start with the API and add optional event delivery when your workflow needs it.
              </p>
            </div>
            <div className="flex shrink-0 flex-col gap-3 sm:items-end">
              <Button
                href="/api-overview/"
                variant="onNavy"
                size="lg"
                rightIcon={<ArrowRight size={17} aria-hidden />}
              >
                API overview
              </Button>
              <Button href="/request-access/" variant="onNavyOutline" size="md">
                Request access
              </Button>
              <a href="/dashboard/" className="text-center text-sm text-[var(--on-navy-muted)] hover:text-[var(--on-navy)]">
                Dashboard preview
              </a>
            </div>
          </div>
        </Section>
      </main>

      <footer className="border-t border-[var(--line)] bg-[var(--panel)]">
        <Container className="flex flex-col gap-4 py-8 text-sm text-[var(--muted)] sm:flex-row sm:items-center sm:justify-between">
          <p>© {new Date().getFullYear()} NetPay by NetHub.</p>
          <p>Payment state you can build on.</p>
        </Container>
      </footer>
    </>
  );
}
