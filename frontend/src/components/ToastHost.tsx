import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { X, CheckCircle2, AlertCircle, Info } from 'lucide-react'
import { subscribeNotifications, type AppNotification } from '../hooks/liveEvents'

type ToastItem = {
  key: string
  title: string
  body: string
  level: string
  href?: string | null
  leaving?: boolean
}

const MAX_VISIBLE = 4
const TTL_SUCCESS = 10000
const TTL_INFO = 8000
const TTL_ERROR = 14000

function toastKey(n: AppNotification): string {
  if (n.intent_id && n.status) return `intent:${n.intent_id}:${n.status}`
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

  const dismiss = useCallback(
    (key: string) => {
      const t = timers.get(key)
      if (t) window.clearTimeout(t)
      timers.delete(key)
      setToasts((prev) => prev.map((x) => (x.key === key ? { ...x, leaving: true } : x)))
      window.setTimeout(() => setToasts((prev) => prev.filter((x) => x.key !== key)), 220)
    },
    [timers],
  )

  const schedule = useCallback(
    (key: string, level: string) => {
      const prev = timers.get(key)
      if (prev) window.clearTimeout(prev)
      timers.set(key, window.setTimeout(() => dismiss(key), ttlFor(level)))
    },
    [dismiss, timers],
  )

  useEffect(() => {
    return subscribeNotifications((n) => {
      const level = (n.level || 'info').toLowerCase()
      const key = toastKey(n)
      setToasts((prev) =>
        [
          { key, title: n.title || 'Update', body: n.body || '', level, href: n.href },
          ...prev.filter((x) => x.key !== key),
        ].slice(0, MAX_VISIBLE),
      )
      schedule(key, level)
    })
  }, [schedule])

  useEffect(
    () => () => {
      for (const id of timers.values()) window.clearTimeout(id)
      timers.clear()
    },
    [timers],
  )

  if (toasts.length === 0) return null

  return (
    <div
      className="fixed right-4 top-4 z-[60] flex w-[min(400px,calc(100vw-2rem))] flex-col gap-2"
      aria-live="assertive"
      aria-relevant="additions"
    >
      {toasts.map((t) => {
        const isErr = t.level === 'error' || t.level === 'danger'
        const isOk = t.level === 'success'
        const border = isErr
          ? 'border-[var(--danger)]/40 bg-[var(--danger-soft)]'
          : isOk
            ? 'border-[var(--accent)]/40 bg-[var(--accent-soft)]'
            : 'border-[var(--border)] bg-[var(--panel)]'
        return (
          <div
            key={t.key}
            className={`flex items-start gap-3 rounded-xl border-2 p-3.5 shadow-[var(--shadow)] transition-opacity duration-200 ${border} ${
              t.leaving ? 'opacity-0' : 'opacity-100'
            }`}
            role="alert"
          >
            <span
              className={`mt-0.5 shrink-0 ${isOk ? 'text-[var(--accent)]' : isErr ? 'text-[var(--danger)]' : 'text-[var(--muted)]'}`}
              aria-hidden
            >
              {isOk ? <CheckCircle2 size={20} strokeWidth={2} /> : isErr ? <AlertCircle size={20} strokeWidth={2} /> : <Info size={20} strokeWidth={2} />}
            </span>
            <button
              type="button"
              className="min-w-0 flex-1 text-left outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)]"
              onClick={() => {
                if (t.href) navigate(t.href)
                dismiss(t.key)
              }}
            >
              <div className="text-sm font-bold text-[var(--text)]">{t.title}</div>
              {t.body && <div className="mt-1 text-sm text-[var(--text)]/80">{t.body}</div>}
              {t.href && <div className="mt-1 text-xs font-medium text-[var(--accent)]">Open details →</div>}
            </button>
            <button type="button" className="rounded-md p-1 text-[var(--muted)] hover:bg-[var(--panel)]" aria-label="Dismiss" onClick={() => dismiss(t.key)}>
              <X size={14} strokeWidth={2} />
            </button>
          </div>
        )
      })}
    </div>
  )
}
