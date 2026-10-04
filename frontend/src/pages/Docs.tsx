import { Link } from 'react-router-dom'
import { PageHeader } from '../components/PageHeader'
import { Button } from '../components/primitives'

const card =
  'mb-4 rounded-2xl border border-[var(--border)] bg-[var(--panel)] p-5 shadow-[var(--shadow-sm)]'

export function Docs() {
  return (
    <div data-testid="docs-page">
      <PageHeader
        title="Help"
        description="How to collect payments with NetPay — in the order that works."
      />

      <div className={card}>
        <h2 className="mb-2 mt-0 text-base font-semibold">1. First-time setup</h2>
        <ol className="m-0 space-y-2 pl-5 text-sm leading-6">
          <li>
            <Link to="/integrations">Shortcodes</Link> — add your paybill or till and network credentials.
          </li>
          <li>
            Open the shortcode → <strong>Connect M-Pesa</strong> so results can reach NetPay.
          </li>
          <li>
            <Link to="/webhooks">Notifications</Link> — optional HTTPS URL so <em>your</em> app is told when a
            payment is paid or failed.
          </li>
        </ol>
      </div>

      <div className={card}>
        <h2 className="mb-2 mt-0 text-base font-semibold">2. Take a payment</h2>
        <p className="m-0 text-sm leading-6 text-[var(--text)]">
          Open <Link to="/intents">Payments</Link>, choose the shortcode, enter the customer’s phone and amount, then
          send. The customer gets a prompt on their phone. Track status on the same list.
        </p>
        <Link to="/intents" className="mt-3 inline-block no-underline">
          <Button size="sm">Go to payments</Button>
        </Link>
      </div>

      <div className={card}>
        <h2 className="mb-2 mt-0 text-base font-semibold">3. Paybill &amp; till (customer pays without a prompt)</h2>
        <p className="m-0 text-sm leading-6">
          Customers can pay your shortcode directly. NetPay matches the account reference on an open payment. Mismatches
          land under <Link to="/reconciliation">Needs attention</Link>.
        </p>
      </div>

      <div className={card}>
        <h2 className="mb-2 mt-0 text-base font-semibold">4. If something looks wrong</h2>
        <ul className="m-0 space-y-1.5 pl-5 text-sm leading-6">
          <li>
            <Link to="/reconciliation">Needs attention</Link> — payments that need a human look.
          </li>
          <li>
            <Link to="/events">Activity</Link> — internal processing log; you can replay an event.
          </li>
          <li>
            <Link to="/status">System status</Link> — whether NetPay and the edge link are healthy.
          </li>
        </ul>
      </div>
    </div>
  )
}
