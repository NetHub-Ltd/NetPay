import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { X, CheckCircle2, AlertCircle, Info } from 'lucide-react'
import { subscribeNotifications, type AppNotification } from '../hooks/liveEvents'

type ToastItem = { key: string; title: string; body: string; level: string; href?: string | null; leaving?: boolean }

const MAX_VISIBLE = 3
const TTL_SUCCESS = 5000
const TTL_INFO = 5000
const TTL_ERROR = 9000

function toastKey(n: AppNotification): string {
  if (n.intent_id) return `intent:${n.intent_id}`
  return n.id || `n:${n.ts || Date.now()}`
}
function ttlFor(level: string): number {
  if (level === 'error' || level === 'danger') return TTL_ERROR
  if (level === 'success') return TTL_SUCCESS
  return TTL_INFO
}

export function ToastHost() {
  const [toasts, setToasts] = useState<ToastItem[]>([])
  const navigate = useNavigate()
  const timers = useState(() => new Map<string, number>())[0]

  const dismiss = useCallback((key: string) => {
    const t = timers.get(key)
    if (t) window.clearTimeout(t)
    timers.delete(key)
    setToasts((prev) => prev.map((x) => x.key === key ? { ...x, leaving: true } : x))
    window.setTimeout(() => setToasts((prev) => prev.filter((x) => x.key !== key)), 220)
  }, [timers])

  const schedule = useCallback((key: string, level: string) => {
    const prev = timers.get(key)
    if (prev) window.clearTimeout(prev)
    const id = window.setTimeout(() => dismiss(key), ttlFor(level))
    timers.set(key, id)
  }, [dismiss, timers])

  useEffect(() => {
    return subscribeNotifications((n) => {
      const level = (n.level || 'info').toLowerCase()
      const key = toastKey(n)
      setToasts((prev) => [{ key, title: n.title || 'Update', body: n.body || '', level, href: n.href }, ...prev.filter((x) => x.key !== key)].slice(0, MAX_VISIBLE))
      schedule(key, level)
    })
  }, [schedule])

  useEffect(() => () => {
    for (const id of timers.values()) window.clearTimeout(id)
    timers.clear()
  }, [timers])

  if (toasts.length === 0) return null

  return (
    <div className="fixed right-4 top-4 z-50 flex w-[min(380px,calc(100vw-2rem))] flex-col gap-2" aria-live="polite" aria-relevant="additions">
      {toasts.map((t) => (
        <div key={t.key}
          className={`flex items-start gap-3 rounded-xl border border-[var(--border)] bg-[var(--panel)] p-3 shadow-[var(--shadow)] transition-opacity duration-200 ${t.leaving ? 'opacity-0' : 'opacity-100'}`}
          role="status">
          <span className={`mt-0.5 shrink-0 ${t.level === 'success' ? 'text-[var(--accent)]' : t.level === 'error' || t.level === 'danger' ? 'text-[var(--danger)]' : 'text-[var(--muted)]'}`} aria-hidden>
            {t.level === 'success' ? <CheckCircle2 size={18} strokeWidth={1.75} /> : t.level === 'error' || t.level === 'danger' ? <AlertCircle size={18} strokeWidth={1.75} /> : <Info size={18} strokeWidth={1.75} />}
          </span>
          <button type="button" className="min-w-0 flex-1 text-left outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)]" onClick={() => { if (t.href) navigate(t.href); dismiss(t.key) }}>
            <div className="text-sm font-semibold">{t.title}</div>
            {t.body && <div className="mt-0.5 text-xs text-[var(--muted)]">{t.body}</div>}
          </button>
          <button type="button" className="rounded-md p-1 text-[var(--muted)] hover:bg-[var(--panel-2)] hover:text-[var(--text)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--accent)]" aria-label="Dismiss" onClick={() => dismiss(t.key)}>
            <X size={14} strokeWidth={2} />
          </button>
        </div>
      ))}
    </div>
  )
}
