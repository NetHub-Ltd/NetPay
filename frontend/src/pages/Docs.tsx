import { Link } from 'react-router-dom'

export function Docs() {
  return (
    <div data-testid="docs-page" className="docs-page">
      <div className="page-header">
        <div>
          <h1>How to use NetPay</h1>
          <p>Short guides for collecting payments and checking what happened.</p>
        </div>
        <Link className="btn primary" to="/intents">
          Go to Payments
        </Link>
      </div>

      <div className="card" style={{ marginBottom: '1rem' }}>
        <h2>1. Take a payment (M-Pesa STK)</h2>
        <ol>
          <li>
            Open <Link to="/intents">Payments</Link> and click <strong>Take a payment</strong>.
          </li>
          <li>Choose the integration (your Paybill / Till setup).</li>
          <li>Enter the customer’s phone (format <code>2547…</code>) and amount in KES.</li>
          <li>Click <strong>Send STK Push</strong>. The customer gets an M-Pesa PIN prompt on their phone.</li>
          <li>
            Open the payment to watch status: <strong>Waiting on M-Pesa</strong> → <strong>Paid</strong> (or Failed /
            Expired).
          </li>
        </ol>
        <p className="muted">
          Tip: double-clicking won’t charge twice — each send uses a unique security key automatically.
        </p>
      </div>

      <div className="card" style={{ marginBottom: '1rem' }}>
        <h2>2. What each status means</h2>
        <ul>
          <li>
            <strong>Created</strong> — saved, not yet sent to M-Pesa.
          </li>
          <li>
            <strong>Waiting on M-Pesa</strong> — prompt sent; customer should enter PIN.
          </li>
          <li>
            <strong>Paid</strong> — success. A ledger line is recorded for the amount.
          </li>
          <li>
            <strong>Failed</strong> — customer cancelled or M-Pesa rejected. Start a <em>new</em> payment if needed.
          </li>
          <li>
            <strong>Expired</strong> — no answer in time. Start a new payment; we don’t auto-revive expired ones.
          </li>
        </ul>
      </div>

      <div className="card" style={{ marginBottom: '1rem' }}>
        <h2>3. Check the money record (ledger)</h2>
        <p>
          On a payment’s detail page, the <strong>Ledger</strong> section shows financial lines. A successful collection
          adds one <code>collection_credit</code>. That is NetPay’s internal money trail for that payment.
        </p>
      </div>

      <div className="card" style={{ marginBottom: '1rem' }}>
        <h2>4. Something looks wrong?</h2>
        <ol>
          <li>
            Open <Link to="/reconciliation">Needs attention</Link> for open exceptions (for example a Paid payment
            missing a ledger line, or a payment stuck waiting too long).
          </li>
          <li>Admins can run a <strong>Scan</strong> to refresh the list.</li>
          <li>Resolve an item when you’ve fixed or understood it — add a short note for the team.</li>
        </ol>
      </div>

      <div className="card" style={{ marginBottom: '1rem' }}>
        <h2>5. First-time setup checklist</h2>
        <ol>
          <li>
            <Link to="/integrations">Integrations</Link> — shortcode, environment (sandbox/live), credentials.
          </li>
          <li>
            <Link to="/webhooks">Webhooks</Link> — HTTPS URL so your app gets payment updates (optional but recommended).
          </li>
          <li>
            Confirm callback URLs with your NetHub / Worker setup so M-Pesa results reach NetPay.
          </li>
        </ol>
      </div>

      <div className="card">
        <h2>Need the technical report?</h2>
        <p className="muted">
          Engineering gate evaluation lives in the repo under <code>.reports/</code> when published on your branch.
        </p>
      </div>
    </div>
  )
}
