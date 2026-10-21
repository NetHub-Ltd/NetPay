import type { Metadata } from "next";
import Link from "next/link";
import { ArrowDownRight, ArrowRight, CheckCircle2, Code2, ShieldCheck, Smartphone, Workflow } from "lucide-react";


const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "https://pay.nethub.co.ke";

export const metadata: Metadata = {
  title: "M-Pesa payment API for business software",
  description:
    "Connect business software to M-Pesa with merchant-owned Daraja integrations, STK Push, and payment events grounded in provider results.",
  alternates: { canonical: "/" },
  openGraph: {
    type: "website",
    locale: "en_KE",
    url: "/",
    title: "NetPay | M-Pesa payment API for business software",
    description:
      "A consistent M-Pesa payments API for merchants, POS systems, and business applications.",
    images: [{ url: "/opengraph-image.png", width: 1200, height: 630, alt: "NetPay payment infrastructure" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "NetPay | M-Pesa payment API for business software",
    description: "Merchant-owned Daraja integrations and payment events for business software.",
    images: ["/opengraph-image.png"],
  },
};

const structuredData = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": `${siteUrl}/#organization`,
      name: "NetHub",
    },
    {
      "@type": "WebSite",
      "@id": `${siteUrl}/#website`,
      url: siteUrl,
      name: "NetPay",
      publisher: { "@id": `${siteUrl}/#organization` },
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
    description: "Send a payment prompt to a customer’s phone and track the provider-confirmed result.",
  },
  {
    icon: Workflow,
    title: "One API, many merchants",
    description: "Keep each merchant’s Daraja integration isolated while your product uses one consistent API.",
  },
  {
    icon: ShieldCheck,
    title: "Built for dependable state",
    description: "Idempotency, callback deduplication, and durable payment events help your systems recover safely.",
  },
  {
    icon: Code2,
    title: "Made for software teams",
    description: "Integrate from a website, POS, or business application using documented API contracts.",
  },
];

export default function HomePage() {
  return (
    <main id="main-content">
      <a href="#main-content" className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-white focus:px-4 focus:py-3 focus:font-semibold focus:text-[#101b2d] focus:shadow-lg">Skip to content</a>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }} />
      <header className="border-b border-white/10 bg-[#101b2d] text-white">
        <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5 lg:px-8" aria-label="Main navigation">
          <Link href="/" className="flex items-center gap-3" aria-label="NetPay home">
            <span className="grid size-10 place-items-center rounded-xl bg-[#20b89a] text-lg font-black text-[#101b2d]">N</span>
            <span className="text-xl font-semibold tracking-tight">NetPay</span>
          </Link>
          <div className="hidden items-center gap-8 text-sm text-slate-300 md:flex">
            <a href="#capabilities" className="transition hover:text-white">Capabilities</a>
            <a href="#how-it-works" className="transition hover:text-white">How it works</a>
            <a href="#developers" className="transition hover:text-white">Developers</a>
          </div>
          <Link href="/dashboard" className="inline-flex items-center gap-2 rounded-full border border-white/20 px-5 py-2.5 text-sm font-semibold transition hover:border-white/50 hover:bg-white/5">
            Dashboard preview <ArrowRight size={16} aria-hidden="true" />
          </Link>
        </nav>
        <section className="relative overflow-hidden">
          <div className="pointer-events-none absolute -right-24 top-8 size-96 rounded-full bg-[#20b89a]/15 blur-3xl" />
          <div className="mx-auto grid max-w-7xl gap-14 px-6 pb-24 pt-20 md:grid-cols-[1.05fr_0.95fr] md:items-center md:pb-32 md:pt-28 lg:px-8">
            <div className="relative z-10">
              <p className="mb-6 inline-flex items-center gap-2 rounded-full border border-[#20b89a]/35 bg-[#20b89a]/10 px-3.5 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-[#70e0c7]">
                <span className="size-1.5 rounded-full bg-[#20b89a]" /> Payments infrastructure for business
              </p>
              <h1 className="max-w-3xl text-5xl font-semibold leading-[1.06] tracking-[-0.045em] sm:text-6xl lg:text-7xl">
                Move from payment prompt to <span className="text-[#55d6b9]">payment clarity.</span>
              </h1>
              <p className="mt-7 max-w-xl text-lg leading-8 text-slate-300">
                NetPay connects your business software to M-Pesa with a consistent API, merchant-owned integrations, and payment events your systems can rely on.
              </p>
              <div className="mt-9 flex flex-col gap-3 sm:flex-row">
                <Link href="#how-it-works" className="inline-flex items-center justify-center gap-2 rounded-full bg-[#20b89a] px-6 py-3.5 font-semibold text-[#101b2d] transition hover:bg-[#42d0b0]">
                  See how it works <ArrowRight size={17} aria-hidden="true" />
                </Link>
                <a href="#capabilities" className="inline-flex items-center justify-center gap-2 rounded-full border border-white/20 px-6 py-3.5 font-semibold text-white transition hover:bg-white/5">
                  Explore capabilities <ArrowDownRight size={17} aria-hidden="true" />
                </a>
              </div>
              <div className="mt-10 flex flex-wrap gap-x-6 gap-y-3 text-sm text-slate-400">
                <span className="inline-flex items-center gap-2"><CheckCircle2 size={16} className="text-[#55d6b9]" /> Merchant-scoped access</span>
                <span className="inline-flex items-center gap-2"><CheckCircle2 size={16} className="text-[#55d6b9]" /> Durable payment state</span>
              </div>
            </div>
            <div className="relative z-10 mx-auto w-full max-w-lg">
              <div className="rounded-[2rem] border border-white/10 bg-white/[0.06] p-4 shadow-2xl shadow-black/20 backdrop-blur">
                <div className="rounded-[1.5rem] bg-white p-6 text-[#142033] sm:p-8">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="text-sm font-medium text-[#627087]">Payment lifecycle</p>
                      <h2 className="mt-1 text-2xl font-semibold tracking-tight">One clear source of truth</h2>
                    </div>
                    <span className="rounded-full bg-[#e6f8f3] px-3 py-1.5 text-xs font-semibold text-[#07836f]">Event-driven</span>
                  </div>
                  <div className="mt-8 space-y-3">
                    <div className="flex items-center gap-4 rounded-2xl border border-[#e3e8ef] p-4">
                      <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-[#edf2f8] text-sm font-bold">01</span>
                      <div className="min-w-0 flex-1"><p className="font-semibold">Request accepted</p><p className="mt-1 text-sm text-[#627087]">Prompt submitted to Daraja</p></div>
                      <span className="rounded-full bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-700">Pending</span>
                    </div>
                    <div className="ml-9 h-4 border-l-2 border-dashed border-[#cdd6e1]" />
                    <div className="flex items-center gap-4 rounded-2xl border border-[#20b89a]/40 bg-[#f1fbf8] p-4">
                      <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-[#d8f5ed] text-sm font-bold text-[#07836f]">02</span>
                      <div className="min-w-0 flex-1"><p className="font-semibold">Provider result received</p><p className="mt-1 text-sm text-[#627087]">Correlated, checked, and deduplicated</p></div>
                      <span className="rounded-full bg-[#d8f5ed] px-2.5 py-1 text-xs font-semibold text-[#07836f]">Confirmed</span>
                    </div>
                    <div className="ml-9 h-4 border-l-2 border-dashed border-[#cdd6e1]" />
                    <div className="flex items-center gap-4 rounded-2xl border border-[#e3e8ef] p-4">
                      <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-[#edf2f8] text-sm font-bold">03</span>
                      <div className="min-w-0 flex-1"><p className="font-semibold">Durable event published</p><p className="mt-1 text-sm text-[#627087]">Your application can reconcile safely</p></div>
                      <span className="rounded-full bg-[#edf2f8] px-2.5 py-1 text-xs font-semibold text-[#45536a]">Delivered</span>
                    </div>
                  </div>
                  <p className="mt-5 text-xs leading-5 text-[#627087]">Illustrative flow. A successful initiation response is not proof that a customer paid.</p>
                </div>
              </div>
              <div className="absolute -bottom-5 -left-5 hidden rounded-2xl border border-white/10 bg-[#172740] px-4 py-3 text-sm text-white shadow-xl sm:block">
                <p className="font-semibold">PostgreSQL-backed</p><p className="mt-1 text-xs text-slate-400">Payment state survives restarts</p>
              </div>
            </div>
          </div>
        </section>
      </header>

      <section id="capabilities" className="mx-auto max-w-7xl px-6 py-20 lg:px-8 lg:py-28">
        <div className="max-w-2xl">
          <p className="text-sm font-bold uppercase tracking-[0.16em] text-[#07836f]">Built around the real workflow</p>
          <h2 className="mt-4 text-3xl font-semibold tracking-tight sm:text-4xl">The payment API is only the beginning.</h2>
          <p className="mt-5 text-lg leading-8 text-[#627087]">A useful gateway has to handle what happens before, during, and after the customer sees the prompt.</p>
        </div>
        <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {capabilities.map((item) => {
            const Icon = item.icon;
            return (
              <article key={item.title} className="rounded-3xl border border-[#e3e8ef] bg-white p-6 transition hover:-translate-y-1 hover:shadow-lg hover:shadow-slate-900/5">
                <span className="grid size-12 place-items-center rounded-2xl bg-[#e6f8f3] text-[#07836f]"><Icon size={22} aria-hidden="true" /></span>
                <h3 className="mt-6 text-lg font-semibold">{item.title}</h3>
                <p className="mt-3 text-sm leading-6 text-[#627087]">{item.description}</p>
              </article>
            );
          })}
        </div>
      </section>

      <section id="how-it-works" className="bg-[#f5f7fa] py-20 lg:py-24">
        <div className="mx-auto grid max-w-7xl gap-12 px-6 md:grid-cols-2 md:items-center lg:px-8">
          <div>
            <p className="text-sm font-bold uppercase tracking-[0.16em] text-[#07836f]">Simple integration path</p>
            <h2 className="mt-4 text-3xl font-semibold tracking-tight sm:text-4xl">Connect once. Know what happened.</h2>
            <p className="mt-5 text-lg leading-8 text-[#627087]">Use your merchant’s Daraja credentials, initiate a payment from your application, and listen for a durable event when provider evidence changes its state.</p>
            <div className="mt-8 space-y-5">
              {["Create a merchant-scoped API client", "Connect a Daraja shortcode and credentials", "Initiate STK Push with an idempotency key", "Consume payment events and reconcile exceptions"].map((step, index) => (
                <div key={step} className="flex gap-4"><span className="grid size-8 shrink-0 place-items-center rounded-full bg-[#142033] text-sm font-semibold text-white">{index + 1}</span><p className="pt-1 font-medium">{step}</p></div>
              ))}
            </div>
          </div>
          <div id="developers" className="overflow-hidden rounded-3xl bg-[#101b2d] p-6 text-white shadow-xl sm:p-8">
            <div className="flex items-center justify-between border-b border-white/10 pb-4"><p className="font-semibold">Example request</p><span className="rounded-full bg-white/10 px-3 py-1 text-xs text-slate-300">HTTP</span></div>
            <pre className="mt-6 overflow-x-auto text-sm leading-7 text-[#d9e5f2]"><code>{`POST /api/v1/payments/stk-push
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
}`}</code></pre>
            <div className="mt-6 rounded-2xl border border-[#20b89a]/30 bg-[#20b89a]/10 p-4 text-sm leading-6 text-[#c7f7eb]">NetPay returns a payment resource. It never treats the STK initiation acknowledgement as proof of payment.</div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-6 py-20 lg:px-8 lg:py-24">
        <div className="flex flex-col gap-8 rounded-[2rem] bg-[#142033] px-7 py-10 text-white sm:px-10 md:flex-row md:items-center md:justify-between lg:px-14 lg:py-12">
          <div className="max-w-2xl"><p className="text-sm font-bold uppercase tracking-[0.16em] text-[#55d6b9]">For builders and businesses</p><h2 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">Make payments a reliable part of your product.</h2><p className="mt-4 leading-7 text-slate-300">Start with the API and add optional event delivery when your workflow needs it.</p></div>
          <Link href="/dashboard" className="inline-flex shrink-0 items-center justify-center gap-2 rounded-full bg-[#20b89a] px-6 py-3.5 font-semibold text-[#101b2d] transition hover:bg-[#42d0b0]">View dashboard preview <ArrowRight size={17} aria-hidden="true" /></Link>
        </div>
      </section>

      <footer className="border-t border-[#e3e8ef]">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-6 py-8 text-sm text-[#627087] sm:flex-row sm:items-center sm:justify-between lg:px-8">
          <p>© {new Date().getFullYear()} NetPay by NetHub.</p>
          <p>Payment state you can build on.</p>
        </div>
      </footer>
    </main>
  );
}
