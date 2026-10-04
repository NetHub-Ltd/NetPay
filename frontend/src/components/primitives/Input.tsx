import type { InputHTMLAttributes, ReactNode } from 'react'

export type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  label?: string
  hint?: string
  error?: string
  leftAddon?: ReactNode
}

export function Input({
  label,
  hint,
  error,
  leftAddon,
  className = '',
  id,
  ...rest
}: InputProps) {
  const inputId = id || rest.name
  return (
    <label className="flex w-full flex-col gap-1.5 text-sm">
      {label && (
        <span className="font-medium text-[var(--text)]">{label}</span>
      )}
      <span className="relative flex items-center">
        {leftAddon && (
          <span className="pointer-events-none absolute left-3 text-[var(--muted)]">
            {leftAddon}
          </span>
        )}
        <input
          id={inputId}
          className={`w-full rounded-xl border bg-[var(--panel)] px-3.5 py-2.5 text-sm text-[var(--text)] shadow-[var(--shadow-sm)] transition placeholder:text-[var(--muted)] focus:border-[var(--accent)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/25 disabled:cursor-not-allowed disabled:opacity-60 ${
            error
              ? 'border-[var(--danger)]'
              : 'border-[var(--border)]'
          } ${leftAddon ? 'pl-10' : ''} ${className}`}
          {...rest}
        />
      </span>
      {error ? (
        <span className="text-xs text-[var(--danger)]" role="alert">
          {error}
        </span>
      ) : hint ? (
        <span className="text-xs text-[var(--muted)]">{hint}</span>
      ) : null}
    </label>
  )
}
