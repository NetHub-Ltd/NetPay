import { Link } from 'react-router-dom'
import { Bell } from 'lucide-react'
import { useNotificationInbox } from '../hooks/useWebSocket'

export function NotificationBell() {
  const { items, open, setOpen, unread, markAllRead, markRead, clear } = useNotificationInbox()

  return (
    <div className="notif-wrap">
      <button
        type="button"
        className="btn icon-only notif-btn"
        title="Notifications"
        aria-label="Notifications"
        onClick={() => {
          setOpen((v) => !v)
          if (!open) markAllRead()
        }}
      >
        <Bell size={16} strokeWidth={1.75} />
        {unread > 0 && <span className="notif-badge">{unread > 9 ? '9+' : unread}</span>}
      </button>
      {open && (
        <div className="notif-panel" role="menu">
          <div className="notif-head">
            <span>Notifications</span>
            <button type="button" className="btn ghost" style={{ fontSize: '0.75rem', padding: '0.2rem 0.4rem' }} onClick={clear}>
              Clear
            </button>
          </div>
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
      )}
    </div>
  )
}
