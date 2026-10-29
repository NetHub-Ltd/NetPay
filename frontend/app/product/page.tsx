import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, CheckCircle2, RefreshCw, ShieldCheck, Smartphone, Webhook } from "lucide-react";
import { PublicSiteFrame } from "../../components/PublicSiteFrame";
import { Badge, Button, Card, Section } from "../../components/ui";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "https://pay.nethub.co.ke";

export const metadata: Metadata = {
  title: "Product — M-Pesa payment workflows",
  description: "Explore NetPay's merchant-aware M-Pesa gateway: STK Push, optional C2B callbacks, callback-backed payment states, and payment events.",
  alternates: { canonical: "/product/" },
  openGraph: { type: "website", url: siteUrl + "/product/", title: "NetPay Product", description: "M-Pesa payment workflows for business software." },
  robots: { index: true, follow: true },
};

const features = [
  { icon: Smartphone, title: "STK Push", description: "Initiate a customer payment prompt using the connected merchant's Daraja integration. Treat the initiation response as an acknowledgement, not proof of payment." },
  { icon: Webhook, title: "Callback-backed outcomes", description: "Receive provider callbacks, correlate them to the payment request, and update payment state from the evidence received." },
  { icon: RefreshCw, title: "Payment events and records", description: "Use durable payment records and supported event delivery to connect payment changes to your own order, POS, or business workflow." },
  { icon: ShieldCheck, title: "Merchant-aware integrations", description: "Connect each merchant with their own shortcode and Daraja credentials rather than mixing merchant configurations." },
];

export default function ProductPage() {
  return (
    <PublicSiteFrame>
      <main id="main-content">
        <Section className="bg-[var(--bg)] pt-12 lg:pt-16">
          <Badge>Product</Badge>
          <h1 className="np-h1 mt-4 max-w-4xl">M-Pesa payment workflows built for business software.</h1>
          <p className="np-lead mt-5 max-w-3xl">NetPay gives your application a consistent way to initiate STK Push, receive provider outcomes, and work with payment records across connected merchants.</p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Button href="/request-access/" variant="primary" rightIcon={<ArrowRight size={16} aria-hidden />}>Request access</Button>
            <Button href="/api-overview/" variant="secondary">Explore the API</Button>
          </div>
          <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {features.map(({ icon: Icon, title, description }) => (
              <Card key={title} elevated className="h-full">
                <span className="grid size-12 place-items-center rounded-2xl bg-[var(--teal-soft)] text-[var(--teal-dark)]"><Icon size={22} aria-hidden /></span>
                <h2 className="mt-5 text-lg font-bold tracking-tight">{title}</h2>
                <p className="mt-2 text-sm leading-6 text-[var(--muted)]">{description}</p>
              </Card>
            ))}
          </div>
        </Section>
        <Section className="bg-[var(--surface)]">
          <div className="grid gap-10 lg:grid-cols-[.9fr_1.1fr] lg:items-start">
            <div>
              <Badge>How it fits</Badge>
              <h2 className="np-h2 mt-4">A payment layer for your existing product.</h2>
              <p className="mt-4 text-base leading-7 text-[var(--muted)]">Keep your checkout, orders, and business rules in your application. NetPay handles the integration boundary and makes payment outcomes available for your software to consume.</p>
            </div>
            <ol className="space-y-4">
              {[
                ["Connect a merchant", "Configure the merchant's shortcode and Daraja credentials securely."],
                ["Initiate the payment", "Your server calls the NetPay API with the merchant integration and client reference."],
                ["Process the outcome", "Use callback-backed status and supported payment events to update your own workflow."],
              ].map(([title, description], index) => (
                <li key={title} className="flex gap-4 rounded-2xl border border-[var(--line)] bg-[var(--panel)] p-5">
                  <span className="grid size-9 shrink-0 place-items-center rounded-full bg-[var(--navy)] text-sm font-bold text-[var(--on-navy)]">{index + 1}</span>
                  <div><h3 className="font-bold">{title}</h3><p className="mt-1 text-sm leading-6 text-[var(--muted)]">{description}</p></div>
                </li>
              ))}
            </ol>
          </div>
        </Section>
        <Section className="bg-[var(--bg)]">
          <div className="rounded-3xl bg-[var(--navy)] p-7 text-[var(--on-navy)] sm:p-10">
            <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">Know the boundaries before you integrate.</h2>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-[var(--on-navy-muted)]">Daraja products can require specific permissions and configuration. C2B is optional for merchants that need it. Transaction-status verification and merchant-specific validation behavior may require additional setup or may not be available for every integration.</p>
            <Link className="mt-5 inline-flex items-center gap-2 font-semibold text-[var(--accent)] hover:underline" href="/api-overview/">Read current capabilities and limits <ArrowRight size={16} /></Link>
          </div>
        </Section>
      </main>
    </PublicSiteFrame>
  );
}
