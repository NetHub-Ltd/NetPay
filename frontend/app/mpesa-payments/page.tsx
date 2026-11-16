import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, ShieldCheck } from "lucide-react";
import { PublicSiteFrame } from "../../components/PublicSiteFrame";
import { Button, Card } from "../../components/ui";
import { siteUrl } from "../../lib/site-url";

export const metadata: Metadata = {
  title: "M-Pesa payments",
  description:
    "How NetPay supports M-Pesa payment flows for businesses in Kenya, including STK Push and optional C2B, with merchant-owned credentials.",
  alternates: { canonical: "/mpesa-payments/" },
  openGraph: {
    title: "M-Pesa payments | NetPay",
    description: "Supported M-Pesa flows, merchant setup, and honest limits.",
    url: `${siteUrl}/mpesa-payments/`,
  },
  robots: { index: true, follow: true },
};

export default function MpesaPaymentsPage() {
  return (
    <PublicSiteFrame>
      <section className="bg-[var(--navy)] text-[var(--on-navy)]">
        <div className="np-container py-14 sm:py-20">
          <p className="np-label text-[var(--on-navy-muted)]">M-Pesa</p>
          <h1 className="mt-4 max-w-3xl text-4xl font-extrabold tracking-tight sm:text-5xl">
            M-Pesa payments for your business
          </h1>
          <p className="mt-5 max-w-2xl text-base leading-7 text-[var(--on-navy-muted)] sm:text-lg">
            NetPay’s current foundation is M-Pesa Daraja. We present it as a supported payment method for businesses, not as the entire identity of the product.
          </p>
        </div>
      </section>

      <section className="bg-[var(--bg)]">
        <div className="np-container py-[var(--space-section-y)] space-y-10">
          <div className="grid gap-6 lg:grid-cols-2">
            <Card className="p-6">
              <h2 className="text-lg font-bold">What businesses can do today</h2>
              <ul className="mt-4 space-y-3 text-sm leading-6 text-[var(--muted)]">
                <li>Initiate supported payment requests to a customer’s phone (STK Push) through the merchant’s own Daraja setup.</li>
                <li>Receive and record payment outcomes from the provider so the business and connected systems can act on confirmed results.</li>
                <li>Use optional C2B registration and confirmation handling where the merchant enables it.</li>
              </ul>
            </Card>
            <Card className="p-6">
              <h2 className="text-lg font-bold">Merchant setup</h2>
              <ul className="mt-4 space-y-3 text-sm leading-6 text-[var(--muted)]">
                <li>Each merchant supplies their own shortcode and credentials.</li>
                <li>NetPay hosts STK callback URLs and correlates outcomes to the original request.</li>
                <li>C2B URL registration is opt-in; STK-only merchants are not forced to register C2B.</li>
              </ul>
            </Card>
          </div>

          <Card className="p-6 sm:p-8">
            <h2 className="text-lg font-bold flex items-center gap-2">
              <ShieldCheck size={20} className="text-[var(--accent)]" aria-hidden />
              Honest limits
            </h2>
            <p className="mt-3 text-sm leading-6 text-[var(--muted)]">
              We do not claim support for every Paybill, Till, or payment scenario. Provider acceptance of a request is not treated as proof that money moved. Feature claims on this site are limited to what is verified in the current product.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Button href="/developers/" variant="primary" size="md">
                Developer details
              </Button>
              <Link href="/features/" className="inline-flex items-center gap-1 text-sm font-semibold text-[var(--accent)] hover:underline">
                Features overview <ArrowRight size={14} aria-hidden />
              </Link>
            </div>
          </Card>
        </div>
      </section>
    </PublicSiteFrame>
  );
}
