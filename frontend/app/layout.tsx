import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import { IBM_Plex_Mono, Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";

const jakarta = Plus_Jakarta_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
  variable: "--font-jakarta",
  display: "swap",
});

const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-mono-stack",
  display: "swap",
});

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "https://pay.nethub.co.ke";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: "NetPay | M-Pesa payment API for business software",
    template: "%s | NetPay",
  },
  description:
    "Connect business software to M-Pesa with merchant-owned Daraja integrations, STK Push, and payment events grounded in provider results.",
  applicationName: "NetPay",
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-image-preview": "large",
      "max-snippet": -1,
      "max-video-preview": -1,
    },
  },
  openGraph: {
    type: "website",
    siteName: "NetPay",
    title: "NetPay | M-Pesa payment API for business software",
    description:
      "A consistent M-Pesa payments API for merchants, POS systems, and business applications.",
  },
  twitter: {
    card: "summary_large_image",
    title: "NetPay | M-Pesa payment API for business software",
    description: "Merchant-owned Daraja integrations and payment events for business software.",
  },
};

export const viewport: Viewport = {
  themeColor: "#101b2d",
  colorScheme: "light",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en" className={`${jakarta.variable} ${plexMono.variable}`}>
      <body className={jakarta.className}>{children}</body>
    </html>
  );
}
