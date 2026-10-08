import type { ReactNode } from 'react'

type Props = {
  tone?: 'error' | 'success' | 'info'
  children: ReactNode
  onDismiss?: () => void
  dismissLabel?: string
}

const tones = {
  error:
    'border-[var(--danger)]/30 bg-[var(--danger-soft)] text-[var(--danger)]',
  success:
    'border-[var(--accent)]/30 bg-[var(--ok-soft)] text-[var(--text)]',
  info:
    'border-[var(--border)] bg-[var(--panel-2)] text-[var(--text)]',
}

/** In-page banner with optional dismiss — prefer toast for short-lived success. */
export function DismissibleBanner({
  tone = 'error',
  children,
  onDismiss,
  dismissLabel = 'Dismiss',
}: Props) {
  return (
    <div
      className={`mb-4 rounded-xl border px-4 py-3 text-sm font-semibold ${tones[tone]}`}
      role={tone === 'error' ? 'alert' : 'status'}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">{children}</div>
        {onDismiss && (
          <button
            type="button"
            className="shrink-0 text-xs font-bold uppercase tracking-wide underline opacity-90 hover:opacity-100"
            onClick={onDismiss}
          >
            {dismissLabel}
          </button>
        )}
      </div>
    </div>
  )
}
