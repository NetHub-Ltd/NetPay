const MAP: Record<string, string> = {
  ok: 'ok',
  active: 'ok',
  succeeded: 'ok',
  completed: 'ok',
  degraded: 'warn',
  pending: 'warn',
  created: 'warn',
  provider_requested: 'warn',
  failed: 'err',
  error: 'err',
  inactive: 'err',
}

export function StatusBadge({ value }: { value: string }) {
  const tone = MAP[value?.toLowerCase?.()] || 'neutral'
  return <span className={`badge status-${tone}`}>{value}</span>
}
