import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, Building2, Laptop, Smartphone, Store } from "lucide-react";
import { PublicSiteFrame } from "../../components/PublicSiteFrame";
import { Button, Card } from "../../components/ui";
import { siteUrl } from "../../lib/site-url";

export const metadata: Metadata = {
  title: "Business solutions",
  description:
    "How NetPay helps physical shops, online stores, service businesses, and digital products accept and manage supported M-Pesa payments.",
  alternates: { canonical: "/solutions/" },
  openGraph: {
    title: "Business solutions | NetPay",
    description: "Payment workflows for physical and digital businesses in Kenya.",
    url: `${siteUrl}/solutions/`,
  },
  robots: { index: true, follow: true },
};

const scenarios = [
  {
    icon: Store,
    title: "Retail and physical businesses",
    body: "Shops, restaurants, salons, pharmacies, and service locations that need a clearer way to confirm customer payments and reduce manual checking. For full POS, inventory, and staff tools, we point you to Tawala.",
  },
  {
    icon: Laptop,
    title: "Online stores and e-commerce",
    body: "Product stores and order-taking websites that need customers to pay online and the store to know when an order is paid—without relying only on screenshots.",
  },
  {
    icon: Building2,
    title: "Service and booking businesses",
    body: "Appointment, event, training, and consultancy businesses that want payment confirmation before the service proceeds, with a path to notify a connected system.",
  },
  {
    icon: Smartphone,
    title: "Apps, SaaS, and digital products",
    body: "Mobile apps and software services that collect payments and need a reliable signal that payment succeeded before granting access or fulfilling an order.",
  },
];

export default function SolutionsPage() {
  return (
    <PublicSiteFrame>
      <section className="bg-[var(--navy)] text-[var(--on-navy)]">
        <div className="np-container py-14 sm:py-20">
          <p className="np-label text-[var(--on-navy-muted)]">Solutions</p>
          <h1 className="mt-4 max-w-3xl text-4xl font-extrabold tracking-tight sm:text-5xl">
            Built around how your business actually works
          </h1>
          <p className="mt-5 max-w-2xl text-base leading-7 text-[var(--on-navy-muted)] sm:text-lg">
            We target businesses by their payment needs, not by a single industry label. Below are common scenarios NetPay is designed to support with the capabilities available today.
          </p>
        </div>
      </section>

      <section className="bg-[var(--bg)]">
        <div className="np-container py-[var(--space-section-y)]">
          <div className="grid gap-6 sm:grid-cols-2">
            {scenarios.map((s) => (
              <Card key={s.title} className="flex flex-col gap-4 p-6">
                <span className="grid size-11 place-items-center rounded-xl bg-[var(--accent-soft)] text-[var(--teal-dark)]">
                  <s.icon size={22} aria-hidden />
                </span>
                <h2 className="text-lg font-bold">{s.title}</h2>
                <p className="text-sm leading-6 text-[var(--muted)]">{s.body}</p>
              </Card>
            ))}
          </div>

          <Card className="mx-auto mt-14 max-w-3xl p-6 text-center sm:p-8">
            <h2 className="text-xl font-bold">NetPay and Tawala</h2>
            <p className="mt-3 text-sm leading-6 text-[var(--muted)]">
              NetPay focuses on payment acceptance and outcomes. Tawala is NetHub’s POS and business-management product. They are complementary; we do not present Tawala features as NetPay features.
            </p>
            <div className="mt-6 flex flex-wrap justify-center gap-3">
              <Button href="/request-access/" variant="primary" size="md">
                Request access
              </Button>
              <Link href="/how-it-works/" className="inline-flex items-center gap-1 text-sm font-semibold text-[var(--accent)] hover:underline">
                How it works <ArrowRight size={14} aria-hidden />
              </Link>
            </div>
          </Card>
        </div>
      </section>
    </PublicSiteFrame>
  );
}
