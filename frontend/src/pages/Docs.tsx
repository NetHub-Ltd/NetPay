import { Link } from 'react-router-dom'
import { PageHeader } from '../components/PageHeader'

const card =
  'mb-4 rounded-2xl border border-[var(--border)] bg-[var(--panel)] p-5 shadow-[var(--shadow-sm)]'
const pre =
  'overflow-x-auto rounded-xl border border-[var(--border)] bg-[var(--panel-2)] p-3 font-mono text-xs leading-5 text-[var(--text)]'

export function Docs() {
  return (
    <div data-testid="docs-page">
      <PageHeader
        title="Help"
        description="Collect in the app, or from your own system — in the order that works."
      />

      <div className={card}>
        <h2 className="mb-2 mt-0 text-base font-semibold">1. First-time setup (in the app)</h2>
        <ol className="m-0 space-y-2 pl-5 text-sm leading-6">
          <li>
            <Link to="/integrations">Shortcodes</Link> — add your paybill or till and network credentials.
          </li>
          <li>
            Open the shortcode → <strong>Connect</strong> so payment results reach NetPay.
          </li>
          <li>
            <Link to="/webhooks">After payment</Link> — HTTPS URL where we notify your system when a
            payment succeeds or fails.
          </li>
          <li>
            Optional: <Link to="/oauth-clients">Connect your system</Link> if a backend will start
            payments (not only the dashboard).
          </li>
        </ol>
      </div>

      <div className={card}>
        <h2 className="mb-2 mt-0 text-base font-semibold">2. Machine-to-machine (M2M)</h2>
        <p className="mt-0 text-sm leading-6 text-[var(--muted)]">
          Your service gets a token, starts a payment, and receives a notification when it settles.
        </p>
        <h3 className="mb-1 text-sm font-semibold">A. Get a token</h3>
        <pre className={pre}>{`POST /v1/oauth/token
Content-Type: application/json

{
  "grant_type": "client_credentials",
  "client_id": "cli_…",
  "client_secret": "…"
}

→ { "access_token": "…", "token_type": "bearer", "expires_in": 43200 }`}</pre>
        <h3 className="mb-1 mt-4 text-sm font-semibold">B. Start a payment</h3>
        <pre className={pre}>{`POST /v1/payment-intents
Authorization: Bearer <access_token>
Idempotency-Key: <unique-id>
Content-Type: application/json

{
  "integration_public_id": "gw_…",
  "phone": "2547XXXXXXXX",
  "amount_minor": 100,
  "account_reference": "ORDER1",
  "description": "Payment",
  "status_callback_url": "https://your.app/hooks/pay"
}`}</pre>
        <p className="mb-0 mt-2 text-xs text-[var(--muted)]">
          <code>amount_minor</code> is cents (100 = KES 1.00). Prefer a unique{' '}
          <code>Idempotency-Key</code> per attempt. Use{' '}
          <code>status_callback_url</code> for a one-off notify URL, or configure standing URLs under
          After payment.
        </p>
        <h3 className="mb-1 mt-4 text-sm font-semibold">C. What we send after settlement</h3>
        <p className="mt-0 text-sm leading-6 text-[var(--muted)]">
          NetPay POSTs a JSON body to your webhook or <code>status_callback_url</code> when the
          payment reaches a final state (succeeded / failed / expired). Verify the signature using the
          webhook secret shown when you added the URL (or the documented HMAC for per-intent
          callbacks). Respond with HTTP 2xx so we treat delivery as successful.
        </p>
        <p className="mb-0 text-sm">
          Create credentials under <Link to="/oauth-clients">Connect your system</Link>.
        </p>
      </div>

      <div className={card}>
        <h2 className="mb-2 mt-0 text-base font-semibold">3. In the dashboard</h2>
        <ul className="m-0 space-y-2 pl-5 text-sm leading-6">
          <li>
            <Link to="/intents">Payments</Link> — status of each collection attempt.
          </li>
          <li>
            <Link to="/dashboard">Overview</Link> — setup checklist for the business you’re working in.
          </li>
        </ul>
      </div>
    </div>
  )
}
