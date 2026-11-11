import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import "./globals.css";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "https://pay.nethub.co.ke";

/** Runs before paint to restore data-theme and avoid flash. */
const themeInitScript = `(function(){try{var k='netpay_theme';var t=localStorage.getItem(k);if(t==='harbor'||t==='shamba'||t==='ledger'){document.documentElement.setAttribute('data-theme',t);}else{document.documentElement.setAttribute('data-theme','ledger');}}catch(e){document.documentElement.setAttribute('data-theme','ledger');}})();`;

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: "NetPay | M-Pesa payments without the integration headache",
    template: "%s | NetPay",
  },
  description:
    "A practical M-Pesa payment gateway for collecting payments, tracking outcomes, and keeping transaction records in order.",
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
    title: "NetPay | M-Pesa payments without the integration headache",
    description:
      "Merchant-aware M-Pesa integrations and callback-backed payment outcomes for business software.",
  },
  twitter: {
    card: "summary_large_image",
    title: "NetPay | M-Pesa payment API for business software",
    description: "Merchant-owned Daraja integrations and payment events for business software.",
  },
};

export const viewport: Viewport = {
  themeColor: "#071e32",
  colorScheme: "light",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en" data-theme="ledger" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
      </head>
      <body>{children}</body>
    </html>
  );
}
