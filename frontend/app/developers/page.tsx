import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, Code2, KeyRound, Webhook } from "lucide-react";
import { PublicSiteFrame } from "../../components/PublicSiteFrame";
import { Badge, Button, Card, Section } from "../../components/ui";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "https://pay.nethub.co.ke";

export const metadata: Metadata = {
  title: "Developers — M-Pesa API integration",
  description: "Integrate NetPay with your POS, commerce platform, or business application using merchant-scoped credentials, STK Push, callbacks, and payment events.",
  alternates: { canonical: "/developers/" },
  openGraph: { type: "website", url: siteUrl + "/developers/", title: "NetPay for Developers", description: "API integration guidance for M-Pesa payment workflows." },
  robots: { index: true, follow: true },
};

const steps = [
  { icon: KeyRound, title: "Authenticate server-to-server", text: "Use your integration's client credentials to obtain an access token. Keep secrets on your server; never embed them in browser or mobile application code." },
  { icon: Code2, title: "Create an STK Push request", text: "Send the merchant integration ID, amount, phone number, client reference, and other fields required by the current API contract. Use an idempotency key for mutating requests." },
  { icon: Webhook, title: "Handle the payment outcome", text: "Wait for provider evidence. Make your own order workflow resilient to duplicate callbacks, delays, and non-success outcomes." },
];

export default function DevelopersPage() {
  return (
    <PublicSiteFrame>
      <main id="main-content">
        <Section className="bg-[var(--bg)] pt-12 lg:pt-16">
          <Badge>Developers</Badge>
          <h1 className="np-h1 mt-4 max-w-4xl">Build your M-Pesa integration around clear contracts and payment states.</h1>
          <p className="np-lead mt-5 max-w-3xl">NetPay is designed for server-side integrations from POS systems, commerce platforms, and business applications. Start with the API overview and use its current request and response contract.</p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Button href="/api-overview/" variant="primary" rightIcon={<ArrowRight size={16} aria-hidden />}>Read API overview</Button>
            <Button href="/request-access/" variant="secondary">Request access</Button>
          </div>
          <div className="mt-12 grid gap-5 lg:grid-cols-3">
            {steps.map(({ icon: Icon, title, text }, index) => (
              <Card key={title} elevated className="h-full">
                <span className="text-xs font-bold uppercase tracking-widest text-[var(--teal-dark)]">Step {index + 1}</span>
                <span className="mt-4 grid size-12 place-items-center rounded-2xl bg-[var(--teal-soft)] text-[var(--teal-dark)]"><Icon size={22} aria-hidden /></span>
                <h2 className="mt-5 text-lg font-bold">{title}</h2>
                <p className="mt-2 text-sm leading-6 text-[var(--muted)]">{text}</p>
              </Card>
            ))}
          </div>
        </Section>
        <Section className="bg-[var(--surface)]">
          <div className="grid gap-8 lg:grid-cols-2">
            <div>
              <Badge>Important distinction</Badge>
              <h2 className="np-h2 mt-4">Accepted request ≠ completed payment.</h2>
              <p className="mt-4 text-base leading-7 text-[var(--muted)]">A successful STK initiation response means the prompt request was accepted. It does not establish that the customer paid. Update your order only from a final status backed by provider evidence and design for delayed or repeated event delivery.</p>
            </div>
            <Card elevated>
              <h2 className="text-lg font-bold">Integration checklist</h2>
              <ul className="mt-4 space-y-3 text-sm leading-6 text-[var(--muted)]">
                <li>• Keep consumer secrets and passkeys server-side.</li>
                <li>• Use a stable client reference and idempotency key.</li>
                <li>• Verify payment state from provider-backed results.</li>
                <li>• Handle callbacks as untrusted, repeatable input.</li>
                <li>• Confirm C2B and Transaction Status permissions before relying on them.</li>
              </ul>
            </Card>
          </div>
        </Section>
        <Section className="bg-[var(--bg)]">
          <div className="rounded-3xl border border-[var(--line)] bg-[var(--panel)] p-7 sm:p-10">
            <h2 className="text-2xl font-bold">Need the current API shape?</h2>
            <p className="mt-3 max-w-2xl text-sm leading-7 text-[var(--muted)]">The API overview documents the current M2M authentication flow, STK Push request, callback behavior, and known limits. Use it instead of copying conceptual marketing examples.</p>
            <Link className="mt-5 inline-flex items-center gap-2 font-semibold text-[var(--teal-dark)] hover:underline" href="/api-overview/">Open API overview <ArrowRight size={16} /></Link>
          </div>
        </Section>
      </main>
    </PublicSiteFrame>
  );
}
