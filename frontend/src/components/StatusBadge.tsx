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

export function StatusBadge({ value }: { value: string }) {
  const key = value?.toLowerCase?.() || ''
  const tone = MAP[key] || 'neutral'
  const label = LABEL[key] || value
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-semibold leading-5 ${TONE_CLASSES[tone]}`}>
      {label}
    </span>
  )
}

export function statusHint(status: string, failureReason?: string | null): string {
  switch (status) {
    case 'created':
      return 'Sending the phone prompt…'
    case 'provider_requested':
      return 'Waiting for the customer’s response from the network.'
    case 'succeeded':
      return 'Paid. Ledger credit recorded.'
    case 'failed':
      return failureReason?.trim()
        ? failureReason
        : 'Did not complete. The network or customer did not approve.'
    case 'expired':
      return failureReason?.trim()
        ? failureReason
        : 'No network result in time. Start a new payment if needed.'
    default:
      return failureReason || ''
  }
}

export function formatKes(amountMinor?: number | null, amount?: string | number | null, currency = 'KES') {
  if (amountMinor != null && !Number.isNaN(Number(amountMinor))) {
    return `${currency} ${(Number(amountMinor) / 100).toFixed(2)}`
  }
  if (amount != null) return `${currency} ${amount}`
  return `${currency} —`
}

export function paymentLifecycleBucket(status: string): 'processing' | 'successful' | 'failed' {
  const s = status?.toLowerCase() || ''
  if (s === 'succeeded') return 'successful'
  if (s === 'failed' || s === 'expired') return 'failed'
  return 'processing'
}
