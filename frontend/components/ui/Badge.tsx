import type { ReactNode } from "react";

type Tone = "teal" | "navy" | "muted" | "onNavy";

const tones: Record<Tone, string> = {
  teal: "bg-[var(--accent-soft)] text-[var(--accent-hover)]",
  navy: "bg-[var(--navy)] text-[var(--on-navy)]",
  muted: "bg-[var(--surface)] text-[var(--muted)] border border-[var(--line)]",
  onNavy: "bg-white/10 text-[var(--on-navy-muted)]",
};

export function Badge({
  children,
  tone = "teal",
  className = "",
}: {
  children: ReactNode;
  tone?: Tone;
  className?: string;
}) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-bold uppercase tracking-[0.14em] ${tones[tone]} ${className}`}
    >
      {children}
    </span>
  );
}
