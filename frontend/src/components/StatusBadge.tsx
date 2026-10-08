/**
 * Operator lifecycle labels. Internal DB statuses are unchanged;
 * M-Pesa ResultCode drives succeeded vs failed via the callback processor.
 */
const MAP: Record<string, string> = {
  ok: 'ok',
  active: 'ok',
  succeeded: 'ok',
  paid: 'ok',
  completed: 'ok',
  degraded: 'warn',
  pending: 'warn',
  created: 'warn',
  provider_requested: 'warn',
  waiting: 'warn',
  processing: 'warn',
  failed: 'err',
  error: 'err',
  inactive: 'err',
  expired: 'err',
  dead: 'err',
  cancelled: 'err',
  canceled: 'err',
}

const LABEL: Record<string, string> = {
  created: 'Processing',
  provider_requested: 'Processing',
  succeeded: 'Successful',
  failed: 'Failed',
  expired: 'Failed',
}

const TONE_CLASSES: Record<string, string> = {
  ok: 'border-[color-mix(in_srgb,var(--accent)_28%,var(--border))] bg-[var(--ok-soft)] text-[var(--accent)]',
  warn: 'border-[color-mix(in_srgb,var(--warn)_30%,var(--border))] bg-[var(--warn-soft)] text-[var(--warn)]',
  err: 'border-[color-mix(in_srgb,var(--danger)_30%,var(--border))] bg-[var(--danger-soft)] text-[var(--danger)]',
  neutral: 'border-[var(--border)] bg-[var(--panel-2)] text-[var(--muted)]',
}

const PROCESSING = new Set(['pending', 'created', 'provider_requested', 'waiting', 'processing'])

export function StatusBadge({ value }: { value: string }) {
  const key = value?.toLowerCase?.() || ''
  const tone = MAP[key] || 'neutral'
  const label = LABEL[key] || value
  const pulse = PROCESSING.has(key)
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-bold leading-5 ${TONE_CLASSES[tone]} ${pulse ? 'animate-pulse' : ''}`}
    >
      {label}
    </span>
  )
}
