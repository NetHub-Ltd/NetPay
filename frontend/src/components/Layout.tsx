import { NavLink, Outlet, Link } from 'react-router-dom'
import {
  Activity,
  AlertTriangle,
  Bell,
  Building2,
  CircleHelp,
  CreditCard,
  Home,
  KeyRound,
  Landmark,
  Moon,
  Plus,
  Radio,
  Sun,
} from 'lucide-react'
import { useAuth } from '../auth/AuthContext'
import { useLiveStatus } from '../hooks/useWebSocket'
import { NotificationBell } from './NotificationBell'
import { useTheme } from '../theme/ThemeContext'

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `nav-link${isActive ? ' active' : ''}`

const ico = { size: 16, strokeWidth: 1.75, className: 'nav-ico' as const }

export function Layout() {
  const { user, logout, isAdmin } = useAuth()
  const { connected } = useLiveStatus()
  const { theme, toggle } = useTheme()

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark" aria-hidden>
            <Landmark size={22} strokeWidth={1.75} />
          </span>
          <div>
            <strong>NetPay</strong>
            <div className="muted tiny">Collect payments</div>
          </div>
        </div>

        <nav>
          <NavLink to="/" end className={linkClass}>
            <Home {...ico} /> Home
          </NavLink>
          <NavLink to="/intents" className={linkClass}>
            <CreditCard {...ico} /> Payments
          </NavLink>
          <NavLink to="/integrations" className={linkClass}>
            <Landmark {...ico} /> Paybills &amp; tills
          </NavLink>
          <NavLink to="/webhooks" className={linkClass}>
            <Bell {...ico} /> Payment notifications
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

        <div className="sidebar-footer">
          <button type="button" className="btn ghost full" onClick={toggle}>
            {theme === 'light' ? <Moon size={14} /> : <Sun size={14} />}{' '}
            {theme === 'light' ? 'Dark mode' : 'Light mode'}
          </button>
          <div className="live-row">
            <span className={`live-dot ${connected ? 'on' : 'off'}`} />
            <span className="tiny">{connected ? 'Live' : 'Offline'}</span>
          </div>
          <div className="user-chip">
            <div className="tiny muted">{user?.email}</div>
            <span className={`badge role-${user?.role}`}>{user?.role}</span>
          </div>
          <button type="button" className="btn ghost full" onClick={logout}>
            Sign out
          </button>
        </div>
      </aside>

      <div className="main-column">
        <header className="topbar">
          <div className="topbar-left">
            <span className="topbar-title">Dashboard</span>
          </div>
          <div className="topbar-actions">
            <Link className="btn" to="/integrations" title="Paybills & tills">
              <Landmark size={16} strokeWidth={1.75} />
              <span className="btn-label">Shortcodes</span>
            </Link>
            <Link className="btn primary" to="/intents">
              <Plus size={16} strokeWidth={2} />
              <span className="btn-label">New payment</span>
            </Link>
            <NotificationBell />
            <Link className="btn icon-only" to="/status" title="System status">
              <Radio size={16} strokeWidth={1.75} />
            </Link>
          </div>
        </header>
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
