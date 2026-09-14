import { Link } from 'react-router-dom'

export function Docs() {
  return (
    <div data-testid="docs-page">
      <div className="page-header">
        <div>
          <h1>Help</h1>
          <p>How to collect payments with NetPay.</p>
        </div>
      </div>

      <div className="card" style={{ marginBottom: '1rem' }}>
        <h2>1. First-time setup</h2>
        <ol>
          <li>
            <Link to="/integrations">Paybills &amp; tills</Link> — add your shortcode and network credentials.
          </li>
          <li>
            Open the shortcode → <strong>Connect this shortcode</strong> (confirm when asked). Links stay on the page if
            you need them later. Phone-prompt results use these links automatically.
          </li>
          <li>
            <Link to="/webhooks">App endpoints</Link> — optional HTTPS URL so <em>your</em> app is told when a
            payment is Paid or Failed.
          </li>
        </ol>
        <p className="muted tiny">
          Connecting the shortcode (so NetPay receives network results) is different from App endpoints (so your
          own app is told). Re-open any shortcode anytime from Paybills &amp; tills.
        </p>
      </div>

      <div className="card" style={{ marginBottom: '1rem' }}>
        <h2>2. Take a payment</h2>
        <p>
          Open <Link to="/intents">Payments</Link>, choose the shortcode, enter the customer’s phone and amount, then
          send. The customer gets a prompt on their phone.
        </p>
      </div>

      <div className="card" style={{ marginBottom: '1rem' }}>
        <h2>3. What each status means</h2>
        <ul>
          <li>
            <strong>Created</strong> — saved, not yet sent to the network.
          </li>
          <li>
            <strong>Waiting for customer</strong> — prompt sent; customer should enter PIN.
          </li>
          <li>
            <strong>Paid</strong> — success. A ledger line is recorded for the amount.
          </li>
          <li>
            <strong>Failed</strong> — customer cancelled or the network rejected. Start a <em>new</em> payment if needed.
          </li>
          <li>
            <strong>Expired</strong> — no answer in time. Start a new payment; we don’t auto-revive expired ones.
          </li>
        </ul>
      </div>

      <div className="card" style={{ marginBottom: '1rem' }}>
        <h2>4. Phone prompt stuck or failed?</h2>
        <ol>
          <li>
            Open the payment — check <strong>Timeline</strong> and any failure message.
          </li>
          <li>
            Open <Link to="/status">System status</Link> → <strong>Provider calls</strong>. Look for a failed “Phone
            prompt request” or “Network login” for that payment.
          </li>
          <li>
            Confirm the shortcode is connected and credentials match the environment (test vs live).
          </li>
          <li>
            Check <strong>Edge connection</strong> on System status — heartbeats and last message should be recent.
          </li>
          <li>
            If the prompt succeeded on the phone but NetPay still waits, the network result may not have reached the edge
            (callback path / secrets). Support uses the payment’s checkout id on the detail page.
          </li>
        </ol>
      </div>

      <div className="card" style={{ marginBottom: '1rem' }}>
        <h2>5. For other systems (API)</h2>
        <p className="muted" style={{ marginTop: 0 }}>
          Create a payment with <code>POST /v1/payment-intents</code> and header <code>Idempotency-Key</code> (required).
        </p>
        <ul>
          <li>
            <strong>Required:</strong> shortcode ref (<code>integration_public_id</code>), phone, amount in minor units (
            <code>amount_minor</code>).
          </li>
          <li>
            <strong>Optional:</strong> <code>status_callback_url</code> (HTTPS) — we POST status here after the payment
            is resolved; <code>metadata</code> — your own fields (e.g. order id).
          </li>
          <li>
            If there is no status URL, we use <Link to="/webhooks">App endpoints</Link> for the business. If
            neither is set, we do not notify your system (network results still go to NetPay via the edge).
          </li>
          <li>
            Validation / confirmation / phone-prompt result URLs always stay on the NetHub edge — they are not the same
            as <code>status_callback_url</code>.
          </li>
        </ul>
      </div>

      <div className="card" style={{ marginBottom: '1rem' }}>
        <h2>6. Ledger &amp; exceptions</h2>
        <p>
          On a payment’s detail page, the <strong>Ledger</strong> section shows financial lines. A successful collection
          adds one <code>collection_credit</code>.
        </p>
        <p>
          Open <Link to="/reconciliation">Needs attention</Link> for open exceptions. Admins can run a scan; resolve with
          a short note when done.
        </p>
      </div>
    </div>
  )
}
