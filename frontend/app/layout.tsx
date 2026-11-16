import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import { siteUrl } from "../lib/site-url";
import { PRODUCT_THEME, THEME_INIT_SCRIPT } from "../lib/theme";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: "NetPay | Payments that work for your business",
    template: "%s | NetPay",
  },
  description:
    "NetPay helps businesses in Kenya accept and manage supported M-Pesa payments, receive clear payment outcomes, and connect those outcomes to how the business works.",
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
    title: "NetPay | Payments that work for your business",
    description: "Accept and manage supported M-Pesa payments with clearer outcomes for businesses in Kenya.",
  },
  twitter: {
    card: "summary_large_image",
    title: "NetPay | Payments that work for your business",
    description: "Accept and manage supported M-Pesa payments with clearer outcomes for businesses in Kenya.",
  },
};

export const viewport: Viewport = {
  themeColor: "#f5f8fa",
  colorScheme: "light dark",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en" data-theme={PRODUCT_THEME} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }} />
      </head>
      <body>{children}</body>
    </html>
  );
}
