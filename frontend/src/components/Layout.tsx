import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { useLiveStatus } from '../hooks/useWebSocket'

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `nav-link${isActive ? ' active' : ''}`

export function Layout() {
  const { user, logout, isAdmin } = useAuth()
  const { connected } = useLiveStatus()

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">⬡</span>
          <div>
            <strong>NetHub</strong>
            <div className="muted tiny">Collect & track payments</div>
          </div>
        </div>

        <nav>
          <NavLink to="/" end className={linkClass}>Health</NavLink>
          {isAdmin && <NavLink to="/tenants" className={linkClass}>Tenants</NavLink>}
          <NavLink to="/integrations" className={linkClass}>Integrations</NavLink>
          <NavLink to="/webhooks" className={linkClass}>Webhooks</NavLink>
          <NavLink to="/intents" className={linkClass}>Payments</NavLink>
          <NavLink to="/reconciliation" className={linkClass}>Needs attention</NavLink>
          <NavLink to="/docs" className={linkClass}>Help</NavLink>
          <NavLink to="/events" className={linkClass}>Activity</NavLink>
          {isAdmin && <NavLink to="/oauth-clients" className={linkClass}>OAuth Clients</NavLink>}
        </nav>

        <div className="sidebar-footer">
          <div className="live-row">
            <span className={`live-dot ${connected ? 'on' : 'off'}`} />
            <span className="tiny">{connected ? 'Live' : 'Offline'}</span>
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
