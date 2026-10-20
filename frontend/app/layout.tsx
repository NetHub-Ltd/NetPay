import type { Metadata, Viewport } from "next";
import "./globals.css";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "https://pay.nethub.co.ke";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: "NetPay — Payments that fit your business",
    template: "%s | NetPay",
  },
  description:
    "Accept M-Pesa payments through a dependable gateway built for merchants, apps, and business software.",
  applicationName: "NetPay",
  openGraph: {
    type: "website",
    siteName: "NetPay",
    title: "NetPay — Payments that fit your business",
    description:
      "A dependable M-Pesa payment gateway for merchants, apps, and business software.",
    url: "/",
  },
  twitter: {
    card: "summary_large_image",
    title: "NetPay — Payments that fit your business",
    description: "A dependable M-Pesa payment gateway for your business.",
  },
};

export const viewport: Viewport = {
  themeColor: "#101b2d",
  colorScheme: "light",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
