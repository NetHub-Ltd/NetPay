import type { Metadata } from "next";
import Link from "next/link";
import { PublicSiteFrame } from "../../components/PublicSiteFrame";
import { Badge, Button, Card, Section } from "../../components/ui";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "https://pay.nethub.co.ke";
/** Update when a dedicated inbox or form backend is ready */
const ACCESS_MAILTO =
  "mailto:hello@nethub.co.ke?subject=NetPay%20access%20request&body=Company%3A%0AUse%20case%3A%0AApproximate%20volume%3A%0A";

export const metadata: Metadata = {
  title: "Request access",
  description:
    "Request NetPay API access for your business software. Integrate with merchant-owned M-Pesa Daraja credentials via M2M.",
  alternates: { canonical: "/request-access/" },
  openGraph: {
    title: "Request NetPay access",
    description: "Onboard your product to the NetPay M-Pesa payment API.",
    url: `${siteUrl}/request-access/`,
    type: "website",
  },
  robots: { index: true, follow: true },
};

export default function RequestAccessPage() {
  return (
    <PublicSiteFrame>
      <main id="main-content">
        <Section className="bg-[var(--bg)] pt-12 lg:pt-16">
          <Badge>Get started</Badge>
          <h1 className="np-h1 mt-4">
            Request API access
          </h1>
          <p className="np-lead mt-4 max-w-2xl">
            Tell us about your product and volume. We onboard merchants with their own Daraja
            credentials—do not send consumer secrets in the first email.
          </p>

          <Card elevated className="mt-10 max-w-xl">
            <h2 className="text-lg font-bold">What to include</h2>
            <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-6 text-[var(--muted)]">
              <li>Company and product name</li>
              <li>Use case (web, POS, marketplace, etc.)</li>
              <li>Approximate monthly STK volume</li>
              <li>Whether you need STK only or also C2B</li>
            </ul>
            <div className="mt-6 flex flex-wrap gap-3">
              <Button href={ACCESS_MAILTO} variant="primary">
                Email NetHub
              </Button>
              <Button href="/api-overview/" variant="secondary">
                Read API overview first
              </Button>
            </div>
            <p className="mt-4 text-xs leading-5 text-[var(--muted)]">
              Opens your mail client to hello@nethub.co.ke. Replace this path with a hosted form when
              backend intake is ready.
            </p>
          </Card>

          <p className="mt-8 text-sm text-[var(--muted)]">
            <Link href="/faq/" className="font-semibold text-[var(--accent-hover)] hover:underline">
              FAQ
            </Link>
            {" · "}
            <Link href="/" className="font-semibold hover:text-[var(--ink)]">
              Home
            </Link>
          </p>
        </Section>
      </main>
    </PublicSiteFrame>
  );
}
