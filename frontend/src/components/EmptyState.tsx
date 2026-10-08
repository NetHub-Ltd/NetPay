import type { ReactNode } from 'react'

type Props = {
  title: string
  hint?: string
  action?: ReactNode
  icon?: ReactNode
}

/** Centered empty region that points the user at the next useful action. */
export function EmptyState({ title, hint, action, icon }: Props) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-[var(--border)] bg-[var(--panel)] px-6 py-14 text-center">
      {icon && (
        <div className="flex size-12 items-center justify-center rounded-xl bg-[var(--accent-soft)] text-[var(--accent)]">
          {icon}
        </div>
      )}
      <h3 className="m-0 text-base font-semibold tracking-tight text-[var(--text)]">
        {title}
      </h3>
      {hint && (
        <p className="m-0 max-w-sm text-sm leading-6 text-[var(--muted)]">{hint}</p>
      )}
      {action && <div className="mt-1 flex flex-wrap items-center justify-center gap-2">{action}</div>}
    </div>
  )
}
