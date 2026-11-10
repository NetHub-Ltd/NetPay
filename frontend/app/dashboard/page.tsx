import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { DashboardClient } from "../../components/DashboardClient";
import { getCurrentSession } from "../../lib/server/session-store";

export const dynamic = "force-dynamic";
export const metadata: Metadata = {
  title: "Merchant dashboard",
  description: "Manage your NetPay merchant workspace.",
  alternates: { canonical: "/dashboard/" },
  robots: { index: false, follow: false, noarchive: true, nosnippet: true },
  openGraph: {
    title: "Merchant dashboard | NetPay",
    description: "NetPay merchant console — NetHub identity required.",
    url: "/dashboard/",
    type: "website",
  },
};

export default async function DashboardPage() {
  const current = await getCurrentSession();
  if (!current) redirect("/login/?returnTo=%2Fdashboard%2F");
  return <DashboardClient />;
}
