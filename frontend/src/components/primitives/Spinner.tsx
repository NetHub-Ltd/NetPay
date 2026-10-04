type Props = {
  size?: 'sm' | 'md' | 'lg'
  label?: string
  className?: string
}

const dims = {
  sm: 'size-4 border-2',
  md: 'size-7 border-2',
  lg: 'size-10 border-[3px]',
}

/** Inline spinner for buttons and compact UI. */
export function Spinner({ size = 'md', label, className = '' }: Props) {
  return (
    <span className={`inline-flex items-center gap-2 ${className}`} role="status">
      <span
        className={`${dims[size]} animate-spin rounded-full border-[var(--accent)] border-r-transparent`}
        aria-hidden
      />
      {label ? (
        <span className="text-sm text-[var(--muted)]">{label}</span>
      ) : (
        <span className="sr-only">Loading</span>
      )}
    </span>
  )
}

/** Full-page or section loader. */
export function PageLoader({ label = 'Loading…' }: { label?: string }) {
  return (
    <div className="flex min-h-[40vh] flex-col items-center justify-center gap-3 bg-[var(--bg)]">
      <Spinner size="lg" />
      <p className="m-0 text-sm text-[var(--muted)]">{label}</p>
    </div>
  )
}
