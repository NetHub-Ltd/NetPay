import { useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { Bell, X } from 'lucide-react'
import { useNotificationInbox } from '../hooks/useWebSocket'

export function NotificationBell() {
  const { items, open, setOpen, unread, markAllRead, markRead, clear } = useNotificationInbox()
  const panelRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return

    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') setOpen(false)
    }

    function onPointer(e: MouseEvent | TouchEvent) {
      const target = e.target as Node | null
      if (!target) return
      // Ignore clicks on the bell button (handled by toggle)
      if ((target as Element).closest?.('.notif-btn')) return
      if (panelRef.current && !panelRef.current.contains(target)) {
        setOpen(false)
      }
    }

    document.addEventListener('keydown', onKey)
    // Capture phase so we close before other handlers
    document.addEventListener('mousedown', onPointer)
    document.addEventListener('touchstart', onPointer)
    return () => {
      document.removeEventListener('keydown', onKey)
      document.removeEventListener('mousedown', onPointer)
      document.removeEventListener('touchstart', onPointer)
    }
  }, [open, setOpen])

  function toggle() {
    if (open) {
      setOpen(false)
      return
    }
    setOpen(true)
    markAllRead()
  }

  return (
    <div className="notif-wrap">
      <button
        type="button"
        className="btn icon-only notif-btn"
        title="Notifications"
        aria-label="Notifications"
        aria-expanded={open}
        onClick={toggle}
      >
        <Bell size={16} strokeWidth={1.75} />
        {unread > 0 && <span className="notif-badge">{unread > 9 ? '9+' : unread}</span>}
      </button>

      {/* Backdrop + sliding panel — always mounted for CSS transition when open */}
      <div
        className={`notif-backdrop${open ? ' is-open' : ''}`}
        aria-hidden={!open}
        onClick={() => setOpen(false)}
      />
      <aside
        ref={panelRef}
        className={`notif-drawer${open ? ' is-open' : ''}`}
        role="dialog"
        aria-label="Notifications"
        aria-hidden={!open}
      >
        <div className="notif-head">
          <span>Notifications</span>
          <div className="notif-head-actions">
            {items.length > 0 && (
              <button
                type="button"
                className="btn ghost"
                style={{ fontSize: '0.75rem', padding: '0.2rem 0.4rem' }}
                onClick={clear}
              >
                Clear
              </button>
            )}
            <button
              type="button"
              className="btn icon-only"
              aria-label="Close notifications"
              onClick={() => setOpen(false)}
            >
              <X size={16} strokeWidth={1.75} />
            </button>
          </div>
        </div>
        <div className="notif-body">
          {items.length === 0 ? (
            <div className="notif-empty">No notifications yet. Payment results appear here live.</div>
          ) : (
            items.map((n) => (
              <Link
                key={`${n.id}-${n.ts}`}
                to={n.href || '/intents'}
                className={`notif-item${n.read ? '' : ' unread'}`}
                onClick={() => {
                  markRead(n.id)
                  setOpen(false)
                }}
              >
                <div style={{ fontWeight: 600, fontSize: '0.88rem' }}>{n.title}</div>
                <div className="muted tiny">{n.body}</div>
                {n.ts && (
                  <div className="muted tiny" style={{ marginTop: 2 }}>
                    {new Date(n.ts).toLocaleString()}
                  </div>
                )}
              </Link>
            ))
          )}
        </div>
      </aside>
    </div>
  )
}
