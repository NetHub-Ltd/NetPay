import type { ButtonHTMLAttributes, ReactNode } from 'react'

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'onHero' | 'onHeroOutline'
type Size = 'sm' | 'md' | 'lg'

const variants: Record<Variant, string> = {
  primary:
    'border border-[var(--accent)] bg-[var(--accent)] text-white hover:bg-[var(--accent-hover)] shadow-sm',
  secondary:
    'border border-[var(--border)] bg-[var(--panel)] text-[var(--text)] hover:bg-[var(--panel-2)] shadow-[var(--shadow-sm)]',
  ghost:
    'border border-transparent bg-transparent text-[var(--muted)] hover:bg-[var(--panel-2)] hover:text-[var(--text)]',
  danger:
    'border border-[var(--danger)] bg-[var(--danger)] text-white hover:opacity-90 shadow-sm',
  onHero:
    'border border-white bg-white text-[var(--accent-hover)] hover:bg-white/90 shadow-sm',
  onHeroOutline:
    'border border-white/40 bg-white/10 text-white hover:bg-white/15',
}

const sizes: Record<Size, string> = {
  sm: 'rounded-lg px-3 py-1.5 text-xs font-semibold',
  md: 'rounded-xl px-4 py-2.5 text-sm font-semibold',
  lg: 'rounded-xl px-5 py-3.5 text-sm font-semibold',
}

export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant
  size?: Size
  loading?: boolean
  leftIcon?: ReactNode
  rightIcon?: ReactNode
}

export function Button({
  variant = 'primary',
  size = 'md',
  loading,
  disabled,
  leftIcon,
  rightIcon,
  className = '',
  children,
  type = 'button',
  ...rest
}: ButtonProps) {
  return (
    <button
      type={type}
      disabled={disabled || loading}
      className={`inline-flex items-center justify-center gap-2 transition active:scale-[0.98] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--accent)] disabled:cursor-not-allowed disabled:opacity-50 disabled:active:scale-100 ${variants[variant]} ${sizes[size]} ${className}`}
      {...rest}
    >
      {loading ? (
        <span
          className="size-4 animate-spin rounded-full border-2 border-current border-r-transparent"
          aria-hidden
        />
      ) : (
        leftIcon
      )}
      {children}
      {!loading && rightIcon}
    </button>
  )
}
