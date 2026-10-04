import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from 'react'

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

export function emitNotification(n: AppNotification) {
  for (const fn of notifListeners) {
    try {
      fn(n)
    } catch {
      /* ignore */
    }
  }
}

export function emitMessage(m: LiveMessage) {
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

export const LiveContext = createContext<LiveCtx>({
  connected: false,
  lastEvent: null,
  lastMessage: null,
})

export function useLiveStatus() {
  return useContext(LiveContext)
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
