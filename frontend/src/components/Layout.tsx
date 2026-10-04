import { NavLink, Outlet, Link } from 'react-router-dom'
import {
  Activity,
  AlertTriangle,
  Building2,
  CircleHelp,
  CreditCard,
  Home,
  KeyRound,
  Landmark,
  LogOut,
  Plus,
  Radio,
  Webhook,
} from 'lucide-react'
import { useAuth } from '../auth/authState'
import { NotificationBell } from './NotificationBell'
import { LiveProvider } from '../hooks/useWebSocket'
import { ToastHost } from './ToastHost'
import { Button } from './primitives'

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm no-underline transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--accent)] ${
    isActive
      ? 'bg-[var(--nav-active-bg)] font-semibold text-[var(--nav-active-color)]'
      : 'text-[var(--muted)] hover:bg-[var(--panel-2)] hover:text-[var(--text)]'
  }`

const ico = { size: 16, strokeWidth: 1.75, className: 'shrink-0' as const }

function displayLabel(user: {
  display_name?: string | null
  full_name?: string | null
  email?: string
} | null) {
  if (!user) return 'Account'
  const name = (user.full_name || user.display_name || '').trim()
  if (name) return name.split(/\s+/)[0]
  return user.email?.split('@')[0] || 'Account'
}

export function Layout() {
  const { user, logout, isAdmin } = useAuth()
  const shortName = displayLabel(user)
  const tenantLabel = user?.tenant_name?.trim() || null

  return (
    <LiveProvider>
      <ToastHost />
      <div className="grid min-h-screen grid-cols-1 bg-[var(--bg)] text-[var(--text)] lg:h-screen lg:max-h-screen lg:grid-cols-[248px_minmax(0,1fr)] lg:overflow-hidden">
        <aside className="flex flex-col gap-3 border-b border-[var(--border)] bg-[var(--panel)] px-4 py-4 lg:sticky lg:top-0 lg:h-screen lg:max-h-screen lg:overflow-hidden lg:border-b-0 lg:border-r lg:px-4 lg:py-5">
          <Link
            to="/dashboard"
            className="flex shrink-0 items-center gap-3 no-underline hover:no-underline"
          >
            <span className="flex size-10 items-center justify-center rounded-xl bg-[var(--accent)] text-white shadow-sm">
              <Landmark size={20} strokeWidth={1.9} aria-hidden />
            </span>
            <div>
              <strong className="text-[var(--text)]">NetPay</strong>
              <div className="text-xs text-[var(--muted)]">
                {tenantLabel || 'Your collections'}
              </div>
            </div>
          </Link>

          <nav className="flex flex-1 flex-col gap-0.5 overflow-y-auto py-2" aria-label="Main">
            <NavLink to="/dashboard" className={linkClass} end>
              <Home {...ico} /> Overview
            </NavLink>
            <NavLink to="/intents" className={linkClass}>
              <CreditCard {...ico} /> Payments
            </NavLink>
            <NavLink to="/integrations" className={linkClass}>
              <Landmark {...ico} /> Shortcodes
            </NavLink>
            <NavLink to="/webhooks" className={linkClass}>
              <Webhook {...ico} /> Notifications
            </NavLink>
            <NavLink to="/reconciliation" className={linkClass}>
              <AlertTriangle {...ico} /> Needs attention
            </NavLink>
            <NavLink to="/events" className={linkClass}>
              <Activity {...ico} /> Activity
            </NavLink>
            <NavLink to="/docs" className={linkClass}>
              <CircleHelp {...ico} /> Help
            </NavLink>
            {isAdmin && (
              <NavLink to="/tenants" className={linkClass}>
                <Building2 {...ico} /> Businesses
              </NavLink>
            )}
            {isAdmin && (
              <NavLink to="/oauth-clients" className={linkClass}>
                <KeyRound {...ico} /> Apps &amp; API access
              </NavLink>
            )}
            <NavLink to="/status" className={linkClass}>
              <Radio {...ico} /> System status
            </NavLink>
          </nav>
        </aside>

        <div className="flex min-h-0 min-w-0 flex-col lg:h-screen lg:overflow-hidden">
          <header className="z-5 flex shrink-0 items-center justify-between gap-4 border-b border-[var(--border)] bg-[var(--panel)] px-4 py-2.5 sm:px-6">
            <span className="text-sm font-semibold text-[var(--text)]">NetPay</span>
            <div className="flex flex-wrap items-center justify-end gap-2">
              <Link
                className="inline-flex items-center justify-center gap-2 rounded-xl border border-[var(--border)] bg-[var(--panel)] px-3 py-2 text-sm font-semibold text-[var(--text)] no-underline shadow-[var(--shadow-sm)] transition hover:bg-[var(--panel-2)] hover:no-underline"
                to="/integrations"
              >
                <Landmark size={16} strokeWidth={1.75} aria-hidden />
                <span className="hidden sm:inline">Shortcodes</span>
              </Link>
              <Link
                className="inline-flex items-center justify-center gap-2 rounded-xl border border-[var(--accent)] bg-[var(--accent)] px-3 py-2 text-sm font-semibold text-white no-underline shadow-sm transition hover:bg-[var(--accent-hover)] hover:no-underline"
                to="/intents"
              >
                <Plus size={16} strokeWidth={2} aria-hidden />
                <span className="hidden sm:inline">New payment</span>
              </Link>
              <NotificationBell />
              <div className="hidden items-center gap-2 md:flex" title={user?.email || ''}>
                <span className="text-xs font-medium text-[var(--text)]">{shortName}</span>
                {isAdmin && (
                  <span className="rounded-full border border-[var(--border)] bg-[var(--accent-soft)] px-2 py-0.5 text-[10px] font-semibold text-[var(--accent-hover)]">
                    Admin
                  </span>
                )}
              </div>
              <Button
                variant="secondary"
                size="sm"
                className="!h-9 !w-9 !p-0"
                onClick={logout}
                title="Sign out"
                aria-label="Sign out"
              >
                <LogOut size={16} strokeWidth={1.75} />
              </Button>
            </div>
          </header>
          <main className="mx-auto w-full max-w-[1200px] flex-1 px-4 py-6 sm:px-6 lg:min-h-0 lg:overflow-y-auto">
            <Outlet />
          </main>
        </div>
      </div>
    </LiveProvider>
  )
}
