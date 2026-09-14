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
  LogOut,
  Moon,
  Plus,
  Radio,
  Sun,
} from 'lucide-react'
import { useAuth } from '../auth/AuthContext'
import { useTheme } from '../theme/ThemeContext'
import { NotificationBell } from './NotificationBell'

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `nav-link${isActive ? ' active' : ''}`

const ico = { size: 16, strokeWidth: 1.75, className: 'nav-ico' as const }

export function Layout() {
  const { user, logout, isAdmin } = useAuth()
  const { theme, toggle } = useTheme()
  const shortName = user?.email?.split('@')[0] || 'Account'

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark" aria-hidden>
            <Landmark size={22} strokeWidth={1.75} />
          </span>
          <div>
            <strong>NetPay</strong>
            <div className="muted tiny">Payments you can trust</div>
          </div>
        </div>

        <nav className="sidebar-nav" aria-label="Main">
          <NavLink to="/" end className={linkClass}>
            <Home {...ico} /> Home
          </NavLink>
          <NavLink to="/intents" className={linkClass}>
            <CreditCard {...ico} /> Payments
          </NavLink>
          <NavLink to="/integrations" className={linkClass}>
            <Landmark {...ico} /> Shortcodes
          </NavLink>
          <NavLink to="/webhooks" className={linkClass}>
            <Bell {...ico} /> App endpoints
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
            <button
              type="button"
              className="btn icon-only"
              onClick={toggle}
              title={theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}
              aria-label={theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}
            >
              {theme === 'light' ? <Moon size={16} strokeWidth={1.75} /> : <Sun size={16} strokeWidth={1.75} />}
            </button>
            <div className="topbar-user" title={user?.email || ''}>
              <span className="tiny">{shortName}</span>
              <span className={`badge role-${user?.role}`}>{user?.role}</span>
            </div>
            <button type="button" className="btn icon-only" onClick={logout} title="Sign out" aria-label="Sign out">
              <LogOut size={16} strokeWidth={1.75} />
            </button>
          </div>
        </header>
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
