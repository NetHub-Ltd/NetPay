import { useEffect, useRef, useState, type ReactNode } from 'react'
import { getToken } from '../api/client'
import {
  emitMessage,
  emitNotification,
  LiveContext,
  type LiveMessage,
} from './liveEvents'

/**
 * LiveProvider — WebSocket to /ws/events for near-instant payment updates.
 *
 * Critical: reconnect when the session token appears (auth finishes after mount).
 * Previous bug: connect() ran once with empty deps; if token was missing, live never started.
 */
export function LiveProvider({ children }: { children: ReactNode }) {
  const [connected, setConnected] = useState(false)
  const [lastEvent, setLastEvent] = useState<string | null>(null)
  const [lastMessage, setLastMessage] = useState<LiveMessage | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const retryRef = useRef<number | null>(null)
  const attemptRef = useRef(0)
  const cancelledRef = useRef(false)

  useEffect(() => {
    cancelledRef.current = false

    function clearRetry() {
      if (retryRef.current) {
        window.clearTimeout(retryRef.current)
        retryRef.current = null
      }
    }

    function scheduleReconnect() {
      clearRetry()
      // Exponential backoff: 1s, 2s, 4s … cap 15s
      const delay = Math.min(15000, 1000 * Math.pow(2, Math.min(attemptRef.current, 4)))
      attemptRef.current += 1
      retryRef.current = window.setTimeout(() => {
        connect()
      }, delay)
    }

    function connect() {
      if (cancelledRef.current) return
      const token = getToken()
      if (!token) {
        setConnected(false)
        // Token may appear after OIDC callback / hydration — keep probing
        clearRetry()
        retryRef.current = window.setTimeout(connect, 1500)
        return
      }

      // Close any existing socket before opening a new one
      try {
        wsRef.current?.close()
      } catch {
        /* ignore */
      }
      wsRef.current = null

      const proto = location.protocol === 'https:' ? 'wss' : 'ws'
      const url = `${proto}://${location.host}/ws/events?token=${encodeURIComponent(token)}`
      let ws: WebSocket
      try {
        ws = new WebSocket(url)
      } catch {
        setConnected(false)
        scheduleReconnect()
        return
      }
      wsRef.current = ws

      ws.onopen = () => {
        if (cancelledRef.current) return
        attemptRef.current = 0
        setConnected(true)
      }
      ws.onclose = () => {
        if (cancelledRef.current) return
        setConnected(false)
        scheduleReconnect()
      }
      ws.onerror = () => {
        // onclose will follow
      }
      ws.onmessage = (ev) => {
        if (cancelledRef.current) return
        try {
          const data = JSON.parse(ev.data) as LiveMessage
          setLastMessage(data)
          setLastEvent(new Date().toISOString())
          if (data.type !== 'ping') setConnected(true)
          emitMessage(data)

          const p = data.payload || {}
          if (data.type === 'notification' || data.type === 'payment.update') {
            if (p.title || p.status || p.intent_id) {
              emitNotification({
                id: String(p.id || `${Date.now()}`),
                title: String(p.title || `Payment ${p.status || 'update'}`),
                body: String(p.body || ''),
                level: p.level ? String(p.level) : 'info',
                href: p.href
                  ? String(p.href)
                  : p.intent_id
                    ? `/intents/${p.intent_id}`
                    : null,
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

    // Re-check token when storage may have changed (login in another tab / late setToken)
    function onStorage(e: StorageEvent) {
      if (e.key === 'nethub_token' || e.key === null) {
        attemptRef.current = 0
        connect()
      }
    }
    window.addEventListener('storage', onStorage)

    // Visibility: when user returns to tab, ensure socket is up
    function onVisible() {
      if (document.visibilityState === 'visible' && !cancelledRef.current) {
        const ws = wsRef.current
        if (!ws || ws.readyState === WebSocket.CLOSED || ws.readyState === WebSocket.CLOSING) {
          attemptRef.current = 0
          connect()
        }
      }
    }
    document.addEventListener('visibilitychange', onVisible)

    return () => {
      cancelledRef.current = true
      clearRetry()
      window.removeEventListener('storage', onStorage)
      document.removeEventListener('visibilitychange', onVisible)
      try {
        wsRef.current?.close()
      } catch {
        /* ignore */
      }
    }
  }, [])

  return (
    <LiveContext.Provider value={{ connected, lastEvent, lastMessage }}>
      {children}
    </LiveContext.Provider>
  )
}
