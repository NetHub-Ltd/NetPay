import Link from "next/link";
import { ArrowUpRight, Code2, Mail, ShieldCheck } from "lucide-react";

const productLinks = [
  { href: "/how-it-works/", label: "How it works" },
  { href: "/solutions/", label: "Solutions" },
  { href: "/mpesa-payments/", label: "M-Pesa payments" },
  { href: "/features/", label: "Features" },
];
const resourceLinks = [
  { href: "/developers/", label: "Developers" },
  { href: "/faq/", label: "FAQ" },
  { href: "/api-overview/", label: "API overview" },
  { href: "/request-access/", label: "Request access" },
];

/** Shared public marketing footer. Every destination is an existing public route. */
export function SiteFooter() {
  return (
    <footer className="border-t border-[var(--on-navy-border)] bg-[var(--navy)] text-[var(--on-navy)]">
      <div className="mx-auto grid max-w-7xl gap-10 px-5 py-12 sm:px-8 lg:grid-cols-[1.3fr_1fr_1fr_1fr] lg:gap-12 lg:py-14">
        <div className="max-w-sm">
          <Link href="/" className="inline-flex items-center gap-3">
            <span aria-hidden="true" className="grid size-9 place-items-center rounded-xl bg-[var(--accent)] font-extrabold text-[var(--on-accent)]">N</span>
            <span className="text-xl font-extrabold tracking-tight">NetPay</span>
          </Link>
          <p className="mt-4 text-sm leading-6 text-[var(--on-navy-muted)]">
            Payments that work for your business. Accept and manage supported M-Pesa payments with clearer outcomes.
          </p>
          <a className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-[var(--on-navy-accent)] hover:underline" href="mailto:hello@nethub.co.ke">
            <Mail size={15} aria-hidden /> Contact NetHub <ArrowUpRight size={14} aria-hidden />
          </a>
        </div>
        <div>
          <h2 className="text-sm font-bold text-[var(--on-navy)]">Explore NetPay</h2>
          <ul className="mt-4 space-y-3 text-sm text-[var(--on-navy-muted)]">
            {productLinks.map((link) => <li key={link.href}><Link className="hover:text-[var(--on-navy)]" href={link.href}>{link.label}</Link></li>)}
          </ul>
        </div>
        <div>
          <h2 className="text-sm font-bold text-[var(--on-navy)]">Resources</h2>
          <ul className="mt-4 space-y-3 text-sm text-[var(--on-navy-muted)]">
            {resourceLinks.map((link) => <li key={link.href}><Link className="hover:text-[var(--on-navy)]" href={link.href}>{link.label}</Link></li>)}
          </ul>
        </div>
        <div>
          <h2 className="text-sm font-bold text-[var(--on-navy)]">Designed for dependable flows</h2>
          <p className="mt-4 text-sm leading-6 text-[var(--on-navy-muted)]">
            Payment state follows provider evidence. A request being accepted is not proof that money moved.
          </p>
          <p className="mt-4 inline-flex items-center gap-2 text-xs text-[var(--on-navy-muted)]"><ShieldCheck size={14} aria-hidden /> Clear payment-state boundaries</p>
          <Link className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-[var(--on-navy-accent)] hover:underline" href="/api-overview/"><Code2 size={15} aria-hidden /> Read the API overview</Link>
        </div>
      </div>
      <div className="border-t border-[var(--on-navy-border)]">
        <div className="mx-auto flex max-w-7xl flex-col gap-2 px-5 py-5 text-xs text-[var(--on-navy-muted)] sm:px-8 md:flex-row md:items-center md:justify-between">
          <p>© {new Date().getFullYear()} NetPay by <a href="https://nethub.co.ke" className="font-semibold hover:text-[var(--on-navy)]">NetHub</a>.</p>
          <p>NetPay by NetHub — payments that work for your business.</p>
        </div>
      </div>
    </footer>
  );
}
