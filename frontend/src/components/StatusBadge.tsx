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
  provider_requested: 'Waiting on M-Pesa',
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
      return 'Payment recorded. Waiting to reach M-Pesa.'
    case 'provider_requested':
      return 'STK push sent. Ask the customer to enter their M-Pesa PIN on the phone.'
    case 'succeeded':
      return 'Payment completed. Ledger credit recorded.'
    case 'failed':
      return 'Payment did not complete. You can start a new attempt with a new amount/phone.'
    case 'expired':
      return 'No callback in time. Start a new payment if the customer still wants to pay.'
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
