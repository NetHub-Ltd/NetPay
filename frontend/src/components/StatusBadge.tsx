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
  failed: 'err',
  error: 'err',
  inactive: 'err',
  expired: 'err',
  dead: 'err',
}

const LABEL: Record<string, string> = {
  created: 'Created',
  provider_requested: 'Waiting for customer',
  succeeded: 'Paid',
  failed: 'Failed',
  expired: 'Expired',
}

export function StatusBadge({ value }: { value: string }) {
  const key = value?.toLowerCase?.() || ''
  const tone = MAP[key] || 'neutral'
  const label = LABEL[key] || value
  return <span className={`badge status-${tone}`}>{label}</span>
}

export function statusHint(status: string): string {
  switch (status) {
    case 'created':
      return 'Payment saved. We’re sending the phone prompt next.'
    case 'provider_requested':
      return 'Prompt sent. Ask the customer to enter their PIN on the phone. This usually updates within a minute.'
    case 'succeeded':
      return 'Payment completed. A ledger credit is recorded for this amount.'
    case 'failed':
      return 'Payment did not complete. Start a new payment if they still want to pay.'
    case 'expired':
      return 'No response in time. Start a new payment if needed — we don’t revive expired ones.'
    default:
      return ''
  }
}

export function formatKes(amountMinor?: number | null, amount?: string | number | null, currency = 'KES') {
  if (amountMinor != null && !Number.isNaN(Number(amountMinor))) {
    return `${currency} ${(Number(amountMinor) / 100).toFixed(2)}`
  }
  if (amount != null) return `${currency} ${amount}`
  return `${currency} —`
}
