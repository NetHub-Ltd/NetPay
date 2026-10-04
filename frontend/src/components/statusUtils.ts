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
