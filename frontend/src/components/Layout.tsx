import { NavLink, Outlet } from 'react-router-dom'
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
          <span className="brand-mark">⬡</span>
          <div>
            <strong>NetPay</strong>
            <div className="muted tiny">Collect M-Pesa payments</div>
          </div>
        </div>

        <nav>
          <NavLink to="/intents" className={linkClass}>Payments</NavLink>
          <NavLink to="/integrations" className={linkClass}>Paybills &amp; tills</NavLink>
          <NavLink to="/webhooks" className={linkClass}>Payment notifications</NavLink>
          <NavLink to="/reconciliation" className={linkClass}>Needs attention</NavLink>
          <NavLink to="/events" className={linkClass}>Activity</NavLink>
          <NavLink to="/docs" className={linkClass}>Help</NavLink>
          {isAdmin && <NavLink to="/tenants" className={linkClass}>Businesses</NavLink>}
          {isAdmin && <NavLink to="/oauth-clients" className={linkClass}>Apps &amp; API access</NavLink>}
          <NavLink to="/" end className={linkClass}>System status</NavLink>
        </nav>

        <div className="sidebar-footer">
          <button type="button" className="btn ghost full" onClick={toggle}>
            Appearance: {theme === 'light' ? 'Light' : 'Dark'}
          </button>
          <div className="live-row">
            <span className={`live-dot ${connected ? 'on' : 'off'}`} />
            <span className="tiny">{connected ? 'Live updates on' : 'Live updates off'}</span>
          </div>
          <div className="user-chip">
            <div className="tiny muted">{user?.email}</div>
            <span className={`badge role-${user?.role}`}>{user?.role}</span>
          </div>
          <button type="button" className="btn ghost full" onClick={logout}>Sign out</button>
        </div>
      </aside>
      <main className="content">
        <Outlet />
      </main>
    </div>
  )
}
