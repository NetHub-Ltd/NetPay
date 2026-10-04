import { Link } from 'react-router-dom'
import { Button } from '../components/primitives'

export function NotFound() {
  return (
    <div className="mx-auto flex min-h-[50vh] max-w-md flex-col items-start justify-center gap-4">
      <p className="m-0 text-xs font-bold uppercase tracking-wider text-[var(--muted)]">404</p>
      <h1 className="m-0 text-2xl font-semibold">Page not found</h1>
      <p className="m-0 text-sm text-[var(--muted)]">
        That link doesn&apos;t match anything in NetPay.
      </p>
      <Link to="/" className="no-underline">
        <Button variant="secondary">Go home</Button>
      </Link>
    </div>
  )
}
