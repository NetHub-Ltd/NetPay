import { Link } from 'react-router-dom'

export function Forbidden() {
  return (
    <div className="mx-auto my-12 mb-4 max-w-[480px] rounded-[var(--radius)] border border-[var(--border)] bg-[var(--panel)] p-5 shadow-[var(--shadow)]" data-testid="forbidden-page">
      <h1 className="text-2xl font-semibold tracking-tight">403 — Forbidden</h1>
      <p className="text-[var(--muted)]">You do not have access to this area. Admin role or matching tenant is required.</p>
      <Link className="inline-flex items-center justify-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--panel)] px-3 py-2 text-sm font-medium text-[var(--text)] no-underline shadow-[var(--shadow-sm)] hover:bg-[var(--panel-2)] hover:no-underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--accent)] disabled:cursor-not-allowed disabled:opacity-50" to="/">Back to health</Link>
    </div>
  )
}
