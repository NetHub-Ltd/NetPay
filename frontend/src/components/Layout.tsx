import { NavLink, Outlet, Link } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { useLiveStatus } from '../hooks/useWebSocket'
import { useTheme } from '../theme/ThemeContext'

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `nav-link${isActive ? ' active' : ''}`

export function Layout() {
  const { user, logout, isAdmin } = useAuth()
  const { connected } = useLiveStatus()
  const { theme, toggle } = useTheme()

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark" aria-hidden>
            ⬡
          </span>
          <div>
            <strong>NetPay</strong>
            <div className="muted tiny">Collect payments</div>
          </div>
        </div>

        <nav>
          <NavLink to="/" end className={linkClass}>
            <span className="nav-ico" aria-hidden>
              🏠
            </span>{' '}
            Home
          </NavLink>
          <NavLink to="/intents" className={linkClass}>
            <span className="nav-ico" aria-hidden>
              💳
            </span>{' '}
            Payments
          </NavLink>
          <NavLink to="/integrations" className={linkClass}>
            <span className="nav-ico" aria-hidden>
              🏦
            </span>{' '}
            Paybills &amp; tills
          </NavLink>
          <NavLink to="/webhooks" className={linkClass}>
            <span className="nav-ico" aria-hidden>
              🔔
            </span>{' '}
            Payment notifications
          </NavLink>
          <NavLink to="/reconciliation" className={linkClass}>
            <span className="nav-ico" aria-hidden>
              ⚠️
            </span>{' '}
            Needs attention
          </NavLink>
          <NavLink to="/events" className={linkClass}>
            <span className="nav-ico" aria-hidden>
              📜
            </span>{' '}
            Activity
          </NavLink>
          <NavLink to="/docs" className={linkClass}>
            <span className="nav-ico" aria-hidden>
              ❓
            </span>{' '}
            Help
          </NavLink>
          {isAdmin && (
            <NavLink to="/tenants" className={linkClass}>
              <span className="nav-ico" aria-hidden>
                🏢
              </span>{' '}
              Businesses
            </NavLink>
          )}
          {isAdmin && (
            <NavLink to="/oauth-clients" className={linkClass}>
              <span className="nav-ico" aria-hidden>
                🔑
              </span>{' '}
              Apps &amp; API access
            </NavLink>
          )}
          <NavLink to="/status" className={linkClass}>
            <span className="nav-ico" aria-hidden>
              📡
            </span>{' '}
            System status
          </NavLink>
        </nav>

        <div className="sidebar-footer">
          <button type="button" className="btn ghost full" onClick={toggle}>
            {theme === 'light' ? '🌙' : '☀️'} Appearance: {theme === 'light' ? 'Light' : 'Dark'}
          </button>
          <div className="live-row">
            <span className={`live-dot ${connected ? 'on' : 'off'}`} />
            <span className="tiny">{connected ? 'Live updates on' : 'Live updates off'}</span>
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
            <span className="muted tiny">NetPay</span>
          </div>
          <div className="topbar-actions">
            <Link className="btn" to="/integrations">
              🏦 Shortcodes
            </Link>
            <Link className="btn primary" to="/intents">
              ＋ Payment
            </Link>
            <Link className="btn" to="/webhooks" title="Payment notifications">
              🔔
            </Link>
            <Link className="btn" to="/status" title="System status">
              📡
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
