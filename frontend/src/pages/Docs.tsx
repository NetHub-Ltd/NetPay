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
        <h2 className="mb-2 mt-0 text-base font-semibold">2. Machine-to-machine (M2M) — Partner quickstart</h2>
        <p className="mt-0 text-sm leading-6 text-[var(--muted)]">
          Your service gets a token, starts a payment, and receives a signed notification when it
          settles. Machine tokens include <code>aud=netpay</code> and expire in 60 minutes by default
          (<code>MACHINE_TOKEN_EXPIRE_MINUTES</code>).
        </p>
        <h3 className="mb-1 text-sm font-semibold">A. Get a token</h3>
        <pre className={pre}>{`POST /v1/oauth/token
Content-Type: application/json

{
  "grant_type": "client_credentials",
  "client_id": "cli_…",
  "client_secret": "…"
}

→ { "access_token": "…", "token_type": "bearer", "expires_in": 3600, "tenant_id": "…", "client_id": "…" }`}</pre>
        <p className="mb-0 mt-2 text-xs text-[var(--muted)]">
          Rate-limited per client (default 30 requests / minute). Over limit → HTTP 429 with{' '}
          <code>Retry-After</code>.
        </p>
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
  "metadata": { "order_id": "…" },
  "status_callback_url": "https://your.app/hooks/pay"
}`}</pre>
        <p className="mb-0 mt-2 text-xs text-[var(--muted)]">
          <code>amount_minor</code> is cents (100 = KES 1.00). Prefer a unique{' '}
          <code>Idempotency-Key</code> per attempt. Rate-limited (default 60 / minute). Use{' '}
          <code>status_callback_url</code> for a one-off notify URL, or standing URLs under After
          payment.
        </p>
        <h3 className="mb-1 mt-4 text-sm font-semibold">C. Verify settlement callbacks</h3>
        <p className="mt-0 text-sm leading-6 text-[var(--muted)]">
          NetPay POSTs JSON to your webhook or <code>status_callback_url</code> with header{' '}
          <code>X-Nethub-Signature: sha256=&lt;hex&gt;</code>.
        </p>
        <ul className="m-0 space-y-2 pl-5 text-sm leading-6 text-[var(--muted)]">
          <li>
            <strong>Tenant webhook</strong> (After payment): HMAC-SHA256 of the raw body using the{' '}
            <code>whsec_…</code> secret shown once when you added the URL.
          </li>
          <li>
            <strong>Per-intent <code>status_callback_url</code></strong>: HMAC-SHA256 of the raw body
            using secret = <code>SHA256(hex)</code> of the string{' '}
            <code>{'{SECRET_KEY}:{intent_id}'}</code> (server <code>SECRET_KEY</code> + intent UUID).
            Prefer tenant webhooks when you control the endpoint long-term.
          </li>
        </ul>
        <p className="mb-0 mt-2 text-sm">
          Respond with HTTP 2xx so we treat delivery as successful. Create credentials under{' '}
          <Link to="/oauth-clients">Connect your system</Link> (you can rotate secrets there).
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
          <li>
            <Link to="/events">Events</Link> — audit trail including delivery outcomes.
          </li>
        </ul>
      </div>
    </div>
  )
}
