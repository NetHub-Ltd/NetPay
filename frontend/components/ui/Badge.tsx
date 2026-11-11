import type { ReactNode } from "react";

type Tone = "teal" | "navy" | "muted" | "onNavy";

const tones: Record<Tone, string> = {
  teal: "bg-[var(--accent-soft)] text-[var(--accent-hover)]",
  navy: "bg-[var(--navy)] text-[var(--on-navy)]",
  muted: "bg-[var(--surface)] text-[var(--muted)] border border-[var(--line)]",
  onNavy: "bg-[var(--on-navy-soft-fill)] text-[var(--on-navy-muted)]",
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
      className={`inline-flex items-center rounded-full px-3 py-1 text-[length:var(--text-xs)] font-[number:var(--weight-bold)] uppercase tracking-[var(--tracking-label)] ${tones[tone]} ${className}`}
    >
      {children}
    </span>
  );
}
