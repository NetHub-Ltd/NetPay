import { Link } from 'react-router-dom'
import { Button } from '../components/primitives'

export function Forbidden() {
  return (
    <div className="mx-auto flex min-h-[50vh] max-w-md flex-col items-start justify-center gap-4">
      <p className="m-0 text-xs font-bold uppercase tracking-wider text-[var(--muted)]">403</p>
      <h1 className="m-0 text-2xl font-semibold">You don&apos;t have access</h1>
      <p className="m-0 text-sm text-[var(--muted)]">
        This area is limited to accounts with the right permissions.
      </p>
      <Link to="/dashboard" className="no-underline">
        <Button>Back to overview</Button>
      </Link>
    </div>
  )
}
