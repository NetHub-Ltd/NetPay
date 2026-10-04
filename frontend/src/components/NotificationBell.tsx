import { useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { Bell, X } from 'lucide-react'
import { useNotificationInbox } from '../hooks/liveEvents'

const buttonClass = 'inline-flex h-9 w-9 items-center justify-center rounded-lg border border-[var(--border)] bg-[var(--panel)] text-[var(--text)] shadow-[var(--shadow-sm)] transition-colors hover:bg-[var(--panel-2)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--accent)]'

export function NotificationBell() {
  const { items, open, setOpen, unread, markAllRead, markRead, clear } = useNotificationInbox()
  const panelRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    function onKey(e: KeyboardEvent) { if (e.key === 'Escape') setOpen(false) }
    function onPointer(e: MouseEvent | TouchEvent) {
      const target = e.target as Node | null
      if (!target) return
      if ((target as Element).closest?.('.notif-btn')) return
      if (panelRef.current && !panelRef.current.contains(target)) setOpen(false)
    }
    document.addEventListener('keydown', onKey)
    document.addEventListener('mousedown', onPointer)
    document.addEventListener('touchstart', onPointer)
    return () => {
      document.removeEventListener('keydown', onKey)
      document.removeEventListener('mousedown', onPointer)
      document.removeEventListener('touchstart', onPointer)
    }
  }, [open, setOpen])

  function toggle() {
    setOpen(!open)
    if (!open) markAllRead()
  }

  return (
    <div className="relative">
      <button type="button" className={`${buttonClass} relative`} title="Notifications" aria-label="Notifications" aria-expanded={open} onClick={toggle}>
        <Bell size={16} strokeWidth={1.75} />
        {unread > 0 && <span className="absolute -right-1 -top-1 min-w-4 rounded-full bg-[var(--danger)] px-1 text-center text-[10px] font-bold leading-4 text-white">{unread > 9 ? '9+' : unread}</span>}
      </button>

      <div className={`fixed inset-0 z-40 bg-black/20 transition-opacity md:hidden ${open ? 'visible opacity-100' : 'invisible opacity-0'}`} aria-hidden={!open} onClick={() => setOpen(false)} />
      <aside ref={panelRef} className={`fixed right-0 top-0 z-50 flex h-full w-[min(380px,100vw)] flex-col border-l border-[var(--border)] bg-[var(--panel)] shadow-2xl transition-transform duration-200 ${open ? 'translate-x-0' : 'translate-x-full'}`} role="dialog" aria-label="Notifications" aria-hidden={!open}>
        <div className="flex items-center justify-between border-b border-[var(--border)] px-4 py-3">
          <span className="font-semibold">Notifications</span>
          <div className="flex items-center gap-1">
            {items.length > 0 && <button type="button" className="rounded-md px-2 py-1 text-xs font-medium text-[var(--muted)] hover:bg-[var(--panel-2)] hover:text-[var(--text)]" onClick={clear}>Clear</button>}
            <button type="button" className="rounded-md p-2 text-[var(--muted)] hover:bg-[var(--panel-2)] hover:text-[var(--text)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--accent)]" aria-label="Close notifications" onClick={() => setOpen(false)}><X size={16} strokeWidth={1.75} /></button>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto">
          {items.length === 0 ? (
            <div className="px-4 py-8 text-center text-sm text-[var(--muted)]">No notifications yet. Payment results appear here live.</div>
          ) : items.map((n) => (
            <Link key={`${n.id}-${n.ts}`} to={n.href || '/intents'}
              className={`block border-b border-[var(--border)] px-4 py-3 no-underline hover:bg-[var(--panel-2)] hover:no-underline ${n.read ? '' : 'border-l-2 border-l-[var(--accent)] bg-[var(--accent-soft)]'}`}
              onClick={() => { markRead(n.id); setOpen(false) }}>
              <div className="text-sm font-semibold text-[var(--text)]">{n.title}</div>
              <div className="text-xs text-[var(--muted)]">{n.body}</div>
              {n.ts && <div className="mt-0.5 text-xs text-[var(--muted)]">{new Date(n.ts).toLocaleString()}</div>}
            </Link>
          ))}
        </div>
      </aside>
    </div>
  )
}
