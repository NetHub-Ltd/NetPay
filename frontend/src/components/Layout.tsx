import { NavLink, Outlet, Link } from 'react-router-dom'
import {
  Activity, AlertTriangle, Bell, Building2, CircleHelp, CreditCard, Home,
  KeyRound, Landmark, LogOut, Moon, Plus, Radio, Sun,
} from 'lucide-react'
import { useAuth } from '../auth/AuthContext'
import { useTheme } from '../theme/ThemeContext'
import { NotificationBell } from './NotificationBell'
import { LiveProvider } from '../hooks/useWebSocket'
import { ToastHost } from './ToastHost'

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `flex items-center gap-3 rounded-lg px-3 py-2 text-[0.92rem] no-underline transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--accent)] ${
    isActive
      ? 'bg-[var(--nav-active-bg)] font-semibold text-[var(--nav-active-color)]'
      : 'text-[var(--muted)] hover:bg-[var(--panel-2)] hover:text-[var(--text)]'
  }`

const ico = { size: 16, strokeWidth: 1.75, className: 'shrink-0' as const }

const buttonClass = 'inline-flex items-center justify-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--panel)] px-3 py-2 text-sm font-medium text-[var(--text)] no-underline shadow-[var(--shadow-sm)] transition-colors hover:bg-[var(--panel-2)] hover:no-underline disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--accent)]'
const iconButtonClass = `${buttonClass} h-9 w-9 p-0`
const primaryButtonClass = `${buttonClass} border-[var(--accent)] bg-[var(--accent)] text-white hover:bg-[var(--accent-hover)]`

export function Layout() {
  const { user, logout, isAdmin } = useAuth()
  const { theme, toggle } = useTheme()
  const shortName = user?.email?.split('@')[0] || 'Account'

  return (
    <LiveProvider>
      <ToastHost />
      <div className="grid h-screen max-h-screen grid-cols-[240px_minmax(0,1fr)] overflow-hidden bg-[var(--bg)] text-[var(--text)]">
        <aside className="sticky top-0 flex h-screen max-h-screen flex-col gap-3 overflow-hidden border-r border-[var(--border)] bg-[var(--panel)] px-4 py-5">
          <div className="flex shrink-0 items-center gap-3">
            <span className="flex items-center" aria-hidden>
              <Landmark size={22} strokeWidth={1.75} />
            </span>
            <div>
              <strong>NetPay</strong>
              <div className="text-xs text-[var(--muted)]">Payments you can trust</div>
            </div>
          </div>

          <nav className="flex min-h-0 flex-1 flex-col gap-1 overflow-x-hidden overflow-y-auto pr-1" aria-label="Main">
            <NavLink to="/" end className={linkClass}><Home {...ico} /> Home</NavLink>
            <NavLink to="/intents" className={linkClass}><CreditCard {...ico} /> Payments</NavLink>
            <NavLink to="/integrations" className={linkClass}><Landmark {...ico} /> Shortcodes</NavLink>
            <NavLink to="/webhooks" className={linkClass}><Bell {...ico} /> App endpoints</NavLink>
            <NavLink to="/reconciliation" className={linkClass}><AlertTriangle {...ico} /> Needs attention</NavLink>
            <NavLink to="/events" className={linkClass}><Activity {...ico} /> Activity</NavLink>
            <NavLink to="/docs" className={linkClass}><CircleHelp {...ico} /> Help</NavLink>
            {isAdmin && <NavLink to="/tenants" className={linkClass}><Building2 {...ico} /> Businesses</NavLink>}
            {isAdmin && <NavLink to="/oauth-clients" className={linkClass}><KeyRound {...ico} /> Apps &amp; API access</NavLink>}
            <NavLink to="/status" className={linkClass}><Radio {...ico} /> System status</NavLink>
          </nav>
        </aside>

        <div className="flex h-screen min-h-0 min-w-0 flex-col overflow-hidden">
          <header className="z-5 flex shrink-0 items-center justify-between gap-4 border-b border-[var(--border)] bg-[var(--panel)] px-6 py-2.5">
            <div><span className="text-sm font-semibold">Dashboard</span></div>
            <div className="flex flex-wrap items-center justify-end gap-2">
              <Link className={buttonClass} to="/integrations" title="Paybills & tills"><Landmark size={16} strokeWidth={1.75} /><span className="hidden sm:inline">Shortcodes</span></Link>
              <Link className={primaryButtonClass} to="/intents"><Plus size={16} strokeWidth={2} /><span className="hidden sm:inline">New payment</span></Link>
              <NotificationBell />
              <button type="button" className={iconButtonClass} onClick={toggle} title={theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'} aria-label={theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}>
                {theme === 'light' ? <Moon size={16} strokeWidth={1.75} /> : <Sun size={16} strokeWidth={1.75} />}
              </button>
              <div className="hidden items-center gap-2 md:flex" title={user?.email || ''}>
                <span className="text-xs text-[var(--muted)]">{shortName}</span>
                <span className="rounded-full border border-[var(--border)] bg-[var(--panel-2)] px-2 py-0.5 text-xs font-semibold text-[var(--text)]">{user?.role}</span>
              </div>
              <button type="button" className={iconButtonClass} onClick={logout} title="Sign out" aria-label="Sign out"><LogOut size={16} strokeWidth={1.75} /></button>
            </div>
          </header>
          <main className="mx-auto w-full max-w-[1120px] flex-1 min-h-0 overflow-y-auto px-4 py-6 sm:px-6">{<Outlet />}</main>
        </div>
      </div>
    </LiveProvider>
  )
}
