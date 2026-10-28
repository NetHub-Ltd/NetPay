import type { Metadata } from "next";
import { ArrowLeft, LockKeyhole } from "lucide-react";
import { Badge, Button, Card, Container } from "../../components/ui";

export const metadata: Metadata = {
  title: "Merchant dashboard preview",
  description:
    "Preview the NetPay merchant dashboard entry point. Merchant sign-in and data views are not enabled yet.",
  alternates: { canonical: "/dashboard/" },
  robots: { index: false, follow: false, noarchive: true },
  openGraph: {
    title: "Merchant dashboard preview | NetPay",
    description: "The NetPay merchant dashboard entry point.",
    url: "/dashboard/",
    type: "website",
  },
};

export default function DashboardPage() {
  return (
    <main className="grid min-h-screen place-items-center bg-[var(--bg)] px-6 py-12">
      <Container className="flex justify-center">
        <Card elevated className="w-full max-w-lg p-8 sm:p-10">
          <Button
            href="/"
            variant="ghost"
            size="sm"
            leftIcon={<ArrowLeft size={16} aria-hidden />}
            className="!px-0"
          >
            Back to NetPay
          </Button>
          <span className="mt-10 grid size-14 place-items-center rounded-2xl bg-[var(--teal-soft)] text-[var(--teal-dark)]">
            <LockKeyhole size={25} aria-hidden />
          </span>
          <h1 className="mt-6 text-3xl font-extrabold tracking-tight text-[var(--ink)]">
            Merchant dashboard preview
          </h1>
          <p className="mt-3 leading-7 text-[var(--muted)]">
            The dashboard UI is being connected to NetHub identity. No merchant data is shown here until
            authentication and session handling are wired in.
          </p>
          <div
            role="status"
            className="mt-7 rounded-[var(--radius)] border border-[var(--warn)]/25 bg-[var(--warn-soft)] p-4 text-sm leading-6 text-[var(--warn)]"
          >
            <Badge tone="muted" className="mb-2 normal-case tracking-normal">
              Not enabled
            </Badge>
            <p className="font-semibold">Dashboard sign-in is not enabled yet.</p>
            <p className="mt-1">Use the M2M API during integration testing.</p>
          </div>
        </Card>
      </Container>
    </main>
  );
}
