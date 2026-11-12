import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { auth } from "../../auth";
import { DashboardClient } from "../../components/DashboardClient";

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
  const session = await auth();
  if (!session?.hasAccessToken) {
    redirect("/login/?returnTo=%2Fdashboard%2F");
  }
  return <DashboardClient />;
}
