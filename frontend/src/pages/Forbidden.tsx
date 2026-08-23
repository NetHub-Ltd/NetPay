import { Link } from 'react-router-dom'

export function Forbidden() {
  return (
    <div className="card" data-testid="forbidden-page" style={{ maxWidth: 480, margin: '3rem auto' }}>
      <h1>403 — Forbidden</h1>
      <p className="muted">You do not have access to this area. Admin role or matching tenant is required.</p>
      <Link className="btn" to="/">Back to health</Link>
    </div>
  )
}
