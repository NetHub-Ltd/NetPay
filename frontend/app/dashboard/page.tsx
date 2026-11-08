import type { Metadata } from "next";
import { DashboardClient } from "../../components/DashboardClient";

export const metadata: Metadata = {
  title: "Merchant dashboard",
  description: "Sign in with NetHub identity to manage your NetPay merchant workspace.",
  alternates: { canonical: "/dashboard/" },
  robots: { index: false, follow: false, noarchive: true, nosnippet: true },
  openGraph: {
    title: "Merchant dashboard | NetPay",
    description: "NetPay merchant console — NetHub identity required.",
    url: "/dashboard/",
    type: "website",
  },
};

export default function DashboardPage() {
  return <DashboardClient />;
}
