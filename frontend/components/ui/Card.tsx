import type { ReactNode } from "react";

type Surface = "panel" | "navy";

const surfaces: Record<Surface, string> = {
  panel: "border-[var(--line)] bg-[var(--panel)] text-[var(--ink)]",
  navy: "border-[var(--on-navy-border)] bg-[var(--navy)] text-[var(--on-navy)]",
};

export function Card({
  children,
  className = "",
  elevated = false,
  surface = "panel",
}: {
  children: ReactNode;
  className?: string;
  elevated?: boolean;
  surface?: Surface;
}) {
  return (
    <div
      className={`rounded-[var(--radius-lg)] border p-6 ${surfaces[surface]} ${
        elevated ? "shadow-[var(--shadow)]" : "shadow-[var(--shadow-sm)]"
      } ${className}`}
    >
      {children}
    </div>
  );
}
