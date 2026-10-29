import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, Boxes, CheckCircle2, GitBranch, ShieldCheck } from "lucide-react";
import { PublicSiteFrame } from "../../components/PublicSiteFrame";
import { Badge, Button, Card, Section } from "../../components/ui";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "https://pay.nethub.co.ke";

export const metadata: Metadata = {
  title: "Why NetPay — M-Pesa infrastructure for software teams",
  description: "See why NetPay focuses on merchant-aware M-Pesa integrations, clear payment-state boundaries, and practical payment events for business software.",
  alternates: { canonical: "/why-netpay/" },
  openGraph: { type: "website", url: siteUrl + "/why-netpay/", title: "Why NetPay", description: "A practical, transparent M-Pesa integration layer for business software." },
  robots: { index: true, follow: true },
};

const principles = [
  { icon: Boxes, title: "Designed for multiple merchants", text: "Connect merchants through their own Daraja shortcode and credentials while your application uses a consistent integration surface." },
  { icon: CheckCircle2, title: "Payment state with explicit evidence", text: "Keep initiation acknowledgements separate from callback-backed outcomes, so downstream order logic can make a more informed decision." },
  { icon: GitBranch, title: "Fits the software you already run", text: "Use NetPay from your own POS, shop system, online store, or business application rather than moving your whole workflow into a new product." },
  { icon: ShieldCheck, title: "Clear limits, not magic promises", text: "Daraja permissions and capabilities vary by merchant configuration. NetPay documents current boundaries instead of promising every payment product works automatically." },
];

export default function WhyNetPayPage() {
  return (
    <PublicSiteFrame>
      <main id="main-content">
        <Section className="bg-[var(--bg)] pt-12 lg:pt-16">
          <Badge>Why NetPay</Badge>
          <h1 className="np-h1 mt-4 max-w-4xl">Payment infrastructure should make the outcome clearer—not hide the complexity.</h1>
          <p className="np-lead mt-5 max-w-3xl">NetPay is built for teams connecting M-Pesa to business software. The focus is practical: merchant-aware integrations, explicit payment states, and records your application can use.</p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Button href="/product/" variant="primary" rightIcon={<ArrowRight size={16} aria-hidden />}>Explore the product</Button>
            <Button href="/api-overview/" variant="secondary">Review the API</Button>
          </div>
          <div className="mt-12 grid gap-5 sm:grid-cols-2">
            {principles.map(({ icon: Icon, title, text }) => (
              <Card key={title} elevated className="h-full">
                <span className="grid size-12 place-items-center rounded-2xl bg-[var(--teal-soft)] text-[var(--teal-dark)]"><Icon size={22} aria-hidden /></span>
                <h2 className="mt-5 text-lg font-bold tracking-tight">{title}</h2>
                <p className="mt-2 text-sm leading-6 text-[var(--muted)]">{text}</p>
              </Card>
            ))}
          </div>
        </Section>
        <Section className="bg-[var(--surface)]">
          <div className="grid gap-8 lg:grid-cols-2">
            <div>
              <Badge>A good fit</Badge>
              <h2 className="np-h2 mt-4">For products that need M-Pesa to be part of the workflow.</h2>
              <p className="mt-4 text-base leading-7 text-[var(--muted)]">NetPay is a fit for software teams integrating merchant M-Pesa collections into POS, commerce, or operational tools—especially when each business needs its own Daraja setup.</p>
            </div>
            <div>
              <Badge>Know before you start</Badge>
              <h2 className="np-h2 mt-4">Not every Daraja capability is automatic.</h2>
              <p className="mt-4 text-base leading-7 text-[var(--muted)]">You may need merchant permissions or extra configuration for specific APIs. C2B registration is optional when needed. NetPay does not treat STK initiation as payment confirmation, and this page does not promise uptime, certification, or transaction-status coverage beyond the documented integration.</p>
              <Link className="mt-4 inline-flex items-center gap-2 font-semibold text-[var(--teal-dark)] hover:underline" href="/faq/">Read common questions <ArrowRight size={16} /></Link>
            </div>
          </div>
        </Section>
      </main>
    </PublicSiteFrame>
  );
}
