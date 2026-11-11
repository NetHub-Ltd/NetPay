import type { ReactNode } from "react";

export function Card({
  children,
  className = "",
  elevated = false,
}: {
  children: ReactNode;
  className?: string;
  elevated?: boolean;
}) {
  return (
    <div
      className={`rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--panel)] p-6 ${
        elevated ? "shadow-[var(--shadow)]" : "shadow-[var(--shadow-sm)]"
      } ${className}`}
    >
      {children}
    </div>
  );
}
