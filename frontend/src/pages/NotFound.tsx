import { Link } from 'react-router-dom'

export function NotFound() {
  return (
    <div className="card" data-testid="notfound-page" style={{ maxWidth: 480, margin: '3rem auto' }}>
      <h1>404 — Not found</h1>
      <p className="muted">That page or resource does not exist.</p>
      <Link className="btn" to="/">Home</Link>
    </div>
  )
}
