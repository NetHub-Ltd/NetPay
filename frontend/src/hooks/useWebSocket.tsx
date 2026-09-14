import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import { getToken } from '../api/client'

export type LiveMessage = {
  type: string
  payload?: Record<string, unknown>
}

export type AppNotification = {
  id: string
  title: string
  body: string
  level?: string
  href?: string | null
  status?: string | null
  intent_id?: string | null
  ts?: string
  read?: boolean
}

const notifListeners = new Set<(n: AppNotification) => void>()
const messageListeners = new Set<(m: LiveMessage) => void>()

export function subscribeNotifications(fn: (n: AppNotification) => void) {
  notifListeners.add(fn)
  return () => {
    notifListeners.delete(fn)
  }
}

export function subscribeLiveMessages(fn: (m: LiveMessage) => void) {
  messageListeners.add(fn)
  return () => {
    messageListeners.delete(fn)
  }
}

function emitNotification(n: AppNotification) {
  for (const fn of notifListeners) {
    try {
      fn(n)
    } catch {
      /* ignore */
    }
  }
}

function emitMessage(m: LiveMessage) {
  for (const fn of messageListeners) {
    try {
      fn(m)
    } catch {
      /* ignore */
    }
  }
}

type LiveCtx = {
  connected: boolean
  lastEvent: string | null
  lastMessage: LiveMessage | null
}

const LiveContext = createContext<LiveCtx>({
  connected: false,
  lastEvent: null,
  lastMessage: null,
})

export function LiveProvider({ children }: { children: ReactNode }) {
  const [connected, setConnected] = useState(false)
  const [lastEvent, setLastEvent] = useState<string | null>(null)
  const [lastMessage, setLastMessage] = useState<LiveMessage | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const retryRef = useRef<number | null>(null)

  useEffect(() => {
    let cancelled = false

    function connect() {
      const token = getToken()
      if (!token) {
        setConnected(false)
        return
      }
      const proto = location.protocol === 'https:' ? 'wss' : 'ws'
      const url = `${proto}://${location.host}/ws/events?token=${encodeURIComponent(token)}`
      let ws: WebSocket
      try {
        ws = new WebSocket(url)
      } catch {
        setConnected(false)
        return
      }
      wsRef.current = ws
      ws.onopen = () => {
        if (!cancelled) setConnected(true)
      }
      ws.onclose = () => {
        if (!cancelled) {
          setConnected(false)
          retryRef.current = window.setTimeout(connect, 4000)
        }
      }
      ws.onerror = () => {}
      ws.onmessage = (ev) => {
        if (cancelled) return
        try {
          const data = JSON.parse(ev.data) as LiveMessage
          setLastMessage(data)
          setLastEvent(new Date().toISOString())
          if (data.type !== 'ping') setConnected(true)
          emitMessage(data)

          const p = data.payload || {}
          if (data.type === 'notification' || data.type === 'payment.update') {
            if (p.title || p.status) {
              emitNotification({
                id: String(p.id || `${Date.now()}`),
                title: String(p.title || `Payment ${p.status || 'update'}`),
                body: String(p.body || ''),
                level: p.level ? String(p.level) : 'info',
                href: p.href ? String(p.href) : p.intent_id ? `/intents/${p.intent_id}` : null,
                status: p.status ? String(p.status) : null,
                intent_id: p.intent_id ? String(p.intent_id) : null,
                ts: p.ts ? String(p.ts) : new Date().toISOString(),
                read: false,
              })
            }
          }
        } catch {
          setLastEvent(String(ev.data).slice(0, 120))
        }
      }
    }

    connect()
    return () => {
      cancelled = true
      if (retryRef.current) window.clearTimeout(retryRef.current)
      wsRef.current?.close()
    }
  }, [])

  return (
    <LiveContext.Provider value={{ connected, lastEvent, lastMessage }}>
      {children}
    </LiveContext.Provider>
  )
}

/** Prefer LiveProvider in Layout; this still works on pages that mount alone. */
export function useLiveStatus() {
  const ctx = useContext(LiveContext)
  // If provider mounted, use context (connected may be shared)
  return ctx
}

export function useNotificationInbox() {
  const [items, setItems] = useState<AppNotification[]>([])
  const [open, setOpen] = useState(false)

  useEffect(() => {
    return subscribeNotifications((n) => {
      setItems((prev) => {
        if (prev.some((x) => x.id === n.id)) return prev
        return [n, ...prev].slice(0, 40)
      })
    })
  }, [])

  const unread = items.filter((i) => !i.read).length
  const markAllRead = useCallback(() => {
    setItems((prev) => prev.map((i) => ({ ...i, read: true })))
  }, [])
  const markRead = useCallback((id: string) => {
    setItems((prev) => prev.map((i) => (i.id === id ? { ...i, read: true } : i)))
  }, [])
  const clear = useCallback(() => setItems([]), [])

  return { items, open, setOpen, unread, markAllRead, markRead, clear }
}
