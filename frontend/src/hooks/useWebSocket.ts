import { useEffect, useRef, useState } from 'react'
import { getToken } from '../api/client'

export type LiveMessage = {
  type: string
  payload?: Record<string, unknown>
}

/**
 * Live updates from NetPay only (WebSocket /ws/events).
 * Does not contact the M-Pesa edge worker.
 */
export function useLiveStatus() {
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
      ws.onerror = () => {
        /* onclose will fire */
      }
      ws.onmessage = (ev) => {
        if (cancelled) return
        try {
          const data = JSON.parse(ev.data) as LiveMessage
          setLastMessage(data)
          setLastEvent(new Date().toISOString())
          if (data.type !== 'ping') setConnected(true)
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

  return { connected, lastEvent, lastMessage }
}
