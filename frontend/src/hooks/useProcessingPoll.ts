import { useEffect, useRef } from 'react'
import { useLiveStatus } from './liveEvents'

/**
 * While any payment is still processing, poll the list periodically.
 * Faster when WS is down. Safety net for missed live frames.
 */
export function useProcessingPoll(
  hasProcessing: boolean,
  reload: () => void | Promise<void>,
) {
  const { connected } = useLiveStatus()
  const reloadRef = useRef(reload)

  useEffect(() => {
    reloadRef.current = reload
  }, [reload])

  useEffect(() => {
    if (!hasProcessing) return
    const ms = connected ? 8000 : 4000
    const id = window.setInterval(() => {
      void reloadRef.current()
    }, ms)
    return () => window.clearInterval(id)
  }, [hasProcessing, connected])
}
