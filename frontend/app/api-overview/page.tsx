import type { Metadata } from "next";
import Link from "next/link";
import { SiteHeader } from "../../components/SiteHeader";
import { Badge, Button, Card, Container, Section } from "../../components/ui";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "https://pay.nethub.co.ke";

export const metadata: Metadata = {
  title: "API overview — STK Push and payment events",
  description:
    "How NetPay’s M2M API works: merchant integrations, STK Push, callbacks, payment status, and optional webhooks—without treating initiation as payment.",
  alternates: { canonical: "/api-overview/" },
  openGraph: {
    title: "NetPay API overview",
    description: "STK Push, merchant-owned Daraja credentials, and durable payment events.",
    url: `${siteUrl}/api-overview/`,
    type: "website",
  },
  robots: { index: true, follow: true },
};

export default function ApiOverviewPage() {
  return (
    <>
      <SiteHeader />
      <main id="main-content">
        <Section className="bg-[var(--bg)] pt-12 lg:pt-16">
          <Badge>For integrators</Badge>
          <h1 className="np-h1 mt-4 max-w-3xl">
            API overview
          </h1>
          <p className="np-lead mt-4 max-w-2xl">
            NetPay exposes a merchant-scoped M2M API. Authenticate with client credentials, initiate
            STK Push, and consume payment state from provider-backed evidence.
          </p>

          <div className="mt-12 grid gap-5 lg:grid-cols-2">
            <Card elevated>
              <h2 className="text-lg font-bold">1. Authenticate (M2M)</h2>
              <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
                Exchange client id and secret for a short-lived bearer token. Tokens are scoped to a
                merchant. Never embed secrets in public apps.
              </p>
            </Card>
            <Card elevated>
              <h2 className="text-lg font-bold">2. Merchant integration</h2>
              <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
                Onboard each merchant with their Daraja consumer key/secret, passkey, and shortcode.
                Credentials are encrypted at rest. OAuth success proves authentication capability, not
                every Daraja product permission.
              </p>
            </Card>
            <Card elevated>
              <h2 className="text-lg font-bold">3. STK Push</h2>
              <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
                Initiate a prompt with amount (KES), phone, and client reference. Use an idempotency key
                on mutating calls. Acceptance of initiation is not confirmation of payment.
              </p>
            </Card>
            <Card elevated>
              <h2 className="text-lg font-bold">4. Callbacks and events</h2>
              <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
                NetPay hosts STK callback URLs per integration. Results are correlated and deduplicated.
                Optional signed webhooks deliver durable payment events to your systems.
              </p>
            </Card>
          </div>

          <Card className="mt-10 overflow-hidden bg-[var(--navy)] p-6 text-[var(--on-navy)] sm:p-8">
            <p className="text-sm font-bold text-[var(--on-navy-muted)]">Example</p>
            <pre className="mt-4 overflow-x-auto font-mono text-sm leading-7 text-[var(--on-navy-muted)]">
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
            <p className="mt-4 text-sm leading-6 text-[var(--on-navy-muted)]">
              Response is a payment resource. Final success/failure follows provider evidence—not this
              HTTP acknowledgement alone.
            </p>
          </Card>

          <div className="mt-10 rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--panel)] p-6">
            <h2 className="text-lg font-bold">Limits to plan around</h2>
            <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-6 text-[var(--muted)]">
              <li>Transaction Status and some Daraja products need extra initiator configuration.</li>
              <li>C2B external validation rules are basic unless you enable and configure C2B.</li>
              <li>Dashboard sign-in is not the integration path until NetHub identity ships.</li>
            </ul>
          </div>

          <div className="mt-10 flex flex-wrap gap-3">
            <Button href="/request-access/" variant="primary">
              Request access
            </Button>
            <Button href="/faq/" variant="secondary">
              FAQ
            </Button>
            <Link href="/" className="self-center text-sm font-semibold text-[var(--muted)] hover:text-[var(--ink)]">
              Home
            </Link>
          </div>
        </Section>
      </main>
      <footer className="border-t border-[var(--line)] bg-[var(--panel)]">
        <Container className="py-8 text-sm text-[var(--muted)]">
          © {new Date().getFullYear()} NetPay by NetHub.
        </Container>
      </footer>
    </>
  );
}
