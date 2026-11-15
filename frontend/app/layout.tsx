import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import { siteUrl } from "../lib/site-url";
import { PRODUCT_THEME, THEME_INIT_SCRIPT } from "../lib/theme";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: "NetPay | M-Pesa Daraja API for business software",
    template: "%s | NetPay",
  },
  description:
    "Integrate M-Pesa STK Push into POS, commerce, and business apps using each merchant's Daraja setup. Track payment outcomes from provider evidence.",
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
    title: "NetPay | M-Pesa Daraja API for business software",
    description: "Merchant-owned Daraja integrations, STK Push, and provider-informed payment outcomes for business software.",
  },
  twitter: {
    card: "summary_large_image",
    title: "NetPay | M-Pesa Daraja API for business software",
    description: "Integrate M-Pesa STK Push using each merchant's Daraja setup and track provider-informed outcomes.",
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
