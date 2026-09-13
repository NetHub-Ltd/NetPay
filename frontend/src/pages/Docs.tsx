import { Link } from 'react-router-dom'

export function Docs() {
  return (
    <div data-testid="docs-page">
      <div className="page-header">
        <div>
          <h1>Help</h1>
          <p>How to collect M-Pesa payments with NetPay.</p>
        </div>
      </div>

      <div className="card" style={{ marginBottom: '1rem' }}>
        <h2>1. First-time setup</h2>
        <ol>
          <li>
            <Link to="/integrations">Paybills &amp; tills</Link> — add your shortcode and Daraja credentials.
          </li>
          <li>
            Open the shortcode → <strong>Connect this shortcode</strong> (confirm when asked). Links stay on the page if
            you ever need to copy them. Phone-prompt payments also use these links automatically.
          </li>
          <li>
            <Link to="/webhooks">Payment notifications</Link> — HTTPS URL so <em>your</em> app is told when a payment
            is Paid or Failed (copy the signing secret when shown).
          </li>
        </ol>
        <p className="muted tiny">
          Connecting the shortcode (so NetPay receives results) is different from Payment notifications (so your own app
          is told). Both matter for a full setup. Re-open any shortcode anytime from Paybills &amp; tills.
        </p>
      </div>

      <div className="card" style={{ marginBottom: '1rem' }}>
        <h2>2. Take a payment</h2>
        <p>
          Open <Link to="/intents">Payments</Link>, choose the shortcode, enter the customer’s phone and amount, then
          send. The customer gets an STK prompt on their phone.
        </p>
      </div>

      <div className="card" style={{ marginBottom: '1rem' }}>
        <h2>3. What each status means</h2>
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
        <h2>4. Check the money record (ledger)</h2>
        <p>
          On a payment’s detail page, the <strong>Ledger</strong> section shows financial lines. A successful collection
          adds one <code>collection_credit</code>. That is NetPay’s internal money trail for that payment.
        </p>
      </div>

      <div className="card" style={{ marginBottom: '1rem' }}>
        <h2>5. Something looks wrong?</h2>
        <ol>
          <li>
            Open <Link to="/reconciliation">Needs attention</Link> for open exceptions.
          </li>
          <li>Admins can run a <strong>Scan</strong> to refresh the list.</li>
          <li>Resolve an item when you’ve fixed or understood it — add a short note for the team.</li>
        </ol>
      </div>
    </div>
  )
}
