export function EmptyState({ title, hint, action }: { title: string; hint?: string; action?: React.ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 rounded-[var(--radius)] border border-dashed border-[var(--border)] bg-[var(--panel)] px-6 py-12 text-center">
      <h3 className="m-0 text-base font-semibold tracking-[-0.02em]">{title}</h3>
      {hint && <p className="m-0 text-sm text-[var(--muted)]">{hint}</p>}
      {action}
    </div>
  )
}
