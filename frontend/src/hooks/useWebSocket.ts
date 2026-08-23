import { useEffect, useRef, useState } from 'react'
import { getToken } from '../api/client'

/** Lightweight live indicator. Backend may not expose /ws yet — we poll health as fallback signal. */
export function useLiveStatus(pollMs = 15000) {
  const [connected, setConnected] = useState(false)
  const [lastEvent, setLastEvent] = useState<string | null>(null)
  const timer = useRef<number | null>(null)

  useEffect(() => {
    let cancelled = false

    async function tick() {
      try {
        const res = await fetch('/health')
        if (!cancelled) {
          setConnected(res.ok)
          if (res.ok) setLastEvent(new Date().toISOString())
        }
      } catch {
        if (!cancelled) setConnected(false)
      }
    }

    tick()
    timer.current = window.setInterval(tick, pollMs)

    // Optional WS if available
    const proto = location.protocol === 'https:' ? 'wss' : 'ws'
    const token = getToken()
    let ws: WebSocket | null = null
    try {
      ws = new WebSocket(`${proto}://${location.host}/ws/events${token ? `?token=${encodeURIComponent(token)}` : ''}`)
      ws.onopen = () => setConnected(true)
      ws.onclose = () => setConnected(false)
      ws.onmessage = (ev) => {
        setLastEvent(ev.data?.slice?.(0, 120) || new Date().toISOString())
        setConnected(true)
      }
    } catch {
      /* WS optional */
    }

    return () => {
      cancelled = true
      if (timer.current) clearInterval(timer.current)
      ws?.close()
    }
  }, [pollMs])

  return { connected, lastEvent }
}
