import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft, LockKeyhole } from "lucide-react";

export const metadata: Metadata = {
  title: "Merchant dashboard",
  robots: { index: false, follow: false, noarchive: true },
};

export default function DashboardPage() {
  return (
    <main className="grid min-h-screen place-items-center bg-[#f5f7fa] px-6 py-12">
      <section className="w-full max-w-lg rounded-3xl border border-[#e3e8ef] bg-white p-8 shadow-xl shadow-slate-900/5 sm:p-10">
        <Link href="/" className="inline-flex items-center gap-2 text-sm font-semibold text-[#627087] transition hover:text-[#142033]"><ArrowLeft size={16} aria-hidden="true" /> Back to NetPay</Link>
        <span className="mt-10 grid size-14 place-items-center rounded-2xl bg-[#e6f8f3] text-[#07836f]"><LockKeyhole size={25} aria-hidden="true" /></span>
        <h1 className="mt-6 text-3xl font-semibold tracking-tight">Merchant dashboard</h1>
        <p className="mt-3 leading-7 text-[#627087]">The dashboard UI is being connected to NetHub identity. No merchant data is shown here until authentication and session handling are wired in.</p>
        <div className="mt-7 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-900">Dashboard sign-in is not enabled yet. Use the M2M API during integration testing.</div>
      </section>
    </main>
  );
}
