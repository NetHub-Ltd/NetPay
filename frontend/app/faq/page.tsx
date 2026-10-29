import type { Metadata } from "next";
import Link from "next/link";
import { PublicSiteFrame } from "../../components/PublicSiteFrame";
import { Badge, Button, Card, Container, Section } from "../../components/ui";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "https://pay.nethub.co.ke";

export const metadata: Metadata = {
  title: "FAQ — M-Pesa API questions",
  description:
    "Answers about NetPay STK Push, merchant-owned Daraja credentials, payment status, webhooks, and what initiation does not prove.",
  alternates: { canonical: "/faq/" },
  openGraph: {
    title: "NetPay FAQ",
    description: "Honest answers about STK Push, Daraja integrations, and payment events.",
    url: `${siteUrl}/faq/`,
    type: "website",
  },
  robots: { index: true, follow: true },
};

const faqs = [
  {
    q: "What is NetPay?",
    a: "NetPay is a multi-merchant M-Pesa Daraja gateway for business software. Each merchant uses their own shortcode and Daraja credentials. Your product calls one consistent API.",
  },
  {
    q: "Does a successful STK Push initiation mean the customer paid?",
    a: "No. Initiation only means Daraja accepted the prompt request. Payment state changes when provider evidence arrives (callback or verified status). NetPay never treats initiation alone as proof of payment.",
  },
  {
    q: "Who owns the Daraja credentials?",
    a: "The merchant. NetPay stores them encrypted and uses them to call Daraja on the merchant’s behalf. A successful OAuth token proves authentication, not every shortcode permission.",
  },
  {
    q: "How do I know a payment succeeded?",
    a: "Use the payment resource status driven by provider results, and optionally subscribe to durable payment events (including signed webhooks when enabled).",
  },
  {
    q: "Is the merchant dashboard available?",
    a: "A dashboard shell is available as a preview. Merchant sign-in and live data are not enabled until NetHub identity is connected. Integrate via the M2M API today.",
  },
  {
    q: "Do I have to register C2B URLs?",
    a: "No. C2B registration is opt-in for merchants that need it. STK-only merchants are not forced to register C2B validation/confirmation URLs.",
  },
  {
    q: "What about sandbox outages or delayed callbacks?",
    a: "Provider sandboxes can be intermittently unreachable. NetPay is designed around idempotent handling and durable events so your system can recover when evidence arrives later.",
  },
  {
    q: "How do I get access?",
    a: "Review the API overview, then request access so NetHub can onboard your integration. Do not send Daraja secrets over unsolicited email threads without a secure channel.",
  },
];

const faqJsonLd = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  mainEntity: faqs.map((item) => ({
    "@type": "Question",
    name: item.q,
    acceptedAnswer: { "@type": "Answer", text: item.a },
  })),
};

export default function FaqPage() {
  return (
    <PublicSiteFrame>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd) }}
      />
      <main id="main-content">
        <Section className="bg-[var(--bg)] pt-12 lg:pt-16">
          <Badge>FAQ</Badge>
          <h1 className="np-h1 mt-4">
            Questions about NetPay
          </h1>
          <p className="np-lead mt-4 max-w-2xl">
            Straight answers aligned with how the product actually works—not marketing shortcuts.
          </p>
          <div className="mt-10 space-y-4">
            {faqs.map((item) => (
              <Card key={item.q} elevated>
                <h2 className="text-lg font-bold tracking-tight">{item.q}</h2>
                <p className="mt-2 text-sm leading-7 text-[var(--muted)]">{item.a}</p>
              </Card>
            ))}
          </div>
          <div className="mt-10 flex flex-wrap gap-3">
            <Button href="/api-overview/" variant="primary">
              API overview
            </Button>
            <Button href="/request-access/" variant="secondary">
              Request access
            </Button>
            <Link href="/" className="self-center text-sm font-semibold text-[var(--muted)] hover:text-[var(--ink)]">
              Back to home
            </Link>
          </div>
        </Section>
      </main>
    </PublicSiteFrame>
  );
}
