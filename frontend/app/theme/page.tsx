import type { Metadata } from "next";
import { ThemeLab } from "../../components/ThemeLab";

export const metadata: Metadata = {
  title: "Theme lab",
  description: "Compare NetPay theme systems. Selection persists in this browser.",
  robots: { index: false, follow: false, noarchive: true },
  alternates: { canonical: "/theme/" },
};

export default function ThemePage() {
  return <ThemeLab />;
}
