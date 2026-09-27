import { Link } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { useTheme } from '../theme/ThemeContext'

/**
 * Public marketing / SEO landing at /.
 */
export default function Landing() {
  const { user } = useAuth()
  const { theme, toggle } = useTheme()

  return (
    <div className="landing">
      <header className="landing-nav">
        <div className="landing-brand">
          <span className="landing-logo" aria-hidden>
            N
          </span>
          <div>
            <strong>NetPay</strong>
            <span className="muted tiny"> by NetHub</span>
          </div>
        </div>
        <div className="landing-nav-actions">
          <button type="button" className="btn ghost" onClick={toggle} title="Toggle appearance">
            {theme === 'light' ? 'Dark' : 'Light'}
          </button>
          {user ? (
            <Link className="btn primary" to="/home">
              Open dashboard
            </Link>
          ) : (
            <Link className="btn primary" to="/login">
              Sign in
            </Link>
          )}
        </div>
      </header>

      <main>
        <section className="landing-hero">
          <p className="landing-eyebrow">M-Pesa collections for Kenyan businesses</p>
          <h1>Accept payments without the operational headache</h1>
          <p className="landing-lead">
            Send STK Push to any Safaricom number, track Paid / Waiting / Failed in plain language,
            and keep a ledger trail your team can trust — on the NetHub platform.
          </p>
          <div className="landing-cta">
            {user ? (
              <Link className="btn primary" to="/home">
                Go to dashboard
              </Link>
            ) : (
              <Link className="btn primary" to="/login">
                Sign in with NetHub
              </Link>
            )}
            <a className="btn ghost" href="#how-it-works">
              How it works
            </a>
          </div>
          <ul className="landing-pills" aria-label="Capabilities">
            <li>Paybill</li>
            <li>Till</li>
            <li>STK Push</li>
            <li>C2B</li>
            <li>Ledger</li>
            <li>Webhooks</li>
          </ul>
        </section>

        <section className="landing-grid" id="how-it-works">
          <article>
            <h2>Request payment</h2>
            <p>
              Create a payment intent with phone, amount, and optional metadata. Customer approves on
              their phone via STK Push.
            </p>
          </article>
          <article>
            <h2>Track status live</h2>
            <p>
              See every intent move through a clear lifecycle — with provider callbacks and a durable
              event trail when something needs support.
            </p>
          </article>
          <article>
            <h2>Stay reconciled</h2>
            <p>
              Successful collections land on a ledger. Reconciliation tools flag gaps so finance is not
              guessing from chat threads.
            </p>
          </article>
        </section>

        <section className="landing-trust">
          <h2>Built for the NetHub ecosystem</h2>
          <p>
            Sign in with NetHub (Keycloak). Authorization and user context come from NetHub API —
            NetPay stays focused on payments.
          </p>
        </section>
      </main>

      <footer className="landing-footer">
        <span className="muted tiny">© {new Date().getFullYear()} NetHub · NetPay</span>
        <a className="muted tiny" href="https://nethub.co.ke" rel="noopener noreferrer">
          nethub.co.ke
        </a>
      </footer>
    </div>
  )
}
