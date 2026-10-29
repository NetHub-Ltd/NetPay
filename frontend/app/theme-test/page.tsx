import type { Metadata } from "next";
import Link from "next/link";
import {
  ArrowDownLeft,
  ArrowRight,
  ArrowUpRight,
  Check,
  CheckCircle2,
  ChevronRight,
  CircleHelp,
  Code2,
  ListChecks,
  RefreshCw,
  ShieldCheck,
  Smartphone,
  Wallet,
  Webhook,
} from "lucide-react";
import styles from "./page.module.css";

export const metadata: Metadata = {
  title: "NetPay — M-Pesa payments without the integration headache",
  description:
    "Explore NetPay's proposed M-Pesa payment gateway experience for businesses and developers. Private design preview, not the production homepage.",
  robots: { index: false, follow: false, googleBot: { index: false, follow: false } },
};

const capabilities = [
  {
    icon: Smartphone,
    title: "STK Push",
    text: "Initiate an M-Pesa payment request from your application and track its reported outcome.",
  },
  {
    icon: ArrowDownLeft,
    title: "C2B payments",
    text: "Receive supported M-Pesa customer-to-business callbacks for a connected merchant.",
  },
  {
    icon: ShieldCheck,
    title: "Clear payment states",
    text: "Distinguish a request being accepted from a payment confirmed by a callback.",
  },
  {
    icon: ListChecks,
    title: "Payment records",
    text: "Keep callback and payment events available to support your own reconciliation workflow.",
  },
];

const sampleRows = [
  { date: "28 Oct · 10:44", amount: "KES 1,000", state: "Matched", kind: "matched" },
  { date: "28 Oct · 09:21", amount: "KES 2,500", state: "Matched", kind: "matched" },
  { date: "27 Oct · 16:32", amount: "KES 980", state: "Matched", kind: "matched" },
  { date: "27 Oct · 11:07", amount: "KES 3,200", state: "Review", kind: "review" },
];

function Brand() {
  return (
    <Link className={styles.brand} href="#top" aria-label="NetPay theme preview home">
      <span className={styles.brandMark}><Wallet size={20} strokeWidth={2.5} /></span>
      <span>NetPay</span>
    </Link>
  );
}

function PaymentPanel() {
  return (
    <div className={styles.dashboard} aria-label="Illustrative payment interface preview">
      <section className={styles.paymentCard}>
        <div className={styles.panelHeading}>
          <div><span className={styles.panelEyebrow}>PAYMENT</span><h3>STK Push</h3></div>
          <span className={styles.pending}>Illustration</span>
        </div>
        <div className={styles.paymentDetails}>
          <div><span>Amount</span><strong>KES 1,000</strong></div>
          <div><span>Phone number</span><strong>254 712 345 678</strong></div>
        </div>
        <ol className={styles.timeline}>
          <li><span className={styles.timelineIcon}><Smartphone size={13} /></span><div><strong>Payment request sent</strong><small>Waiting for provider response</small></div></li>
          <li><span className={styles.timelineIcon}><Check size={13} /></span><div><strong>Customer response</strong><small>Example state · not live</small></div></li>
          <li><span className={styles.timelineIcon}><Check size={13} /></span><div><strong>Callback received</strong><small>Final state depends on provider result</small></div></li>
        </ol>
        <p className={styles.sampleNote}>Sample interface only — no live payment is shown.</p>
      </section>

      <div className={styles.sidePanels}>
        <section className={styles.reconciliationCard}>
          <div className={styles.smallPanelHeading}><h3>Payment records</h3><span>Preview</span></div>
          <div className={styles.tableHeader}><span>Date</span><span>Amount</span><span>Review</span></div>
          {sampleRows.map((row) => (
            <div className={styles.tableRow} key={row.date}>
              <span>{row.date}</span><span>{row.amount}</span><span className={row.kind === "matched" ? styles.matched : styles.review}>{row.state}</span>
            </div>
          ))}
          <p className={styles.sampleNote}>Illustrative records, not connected data.</p>
        </section>
        <section className={styles.callbackCard}>
          <div className={styles.callbackIcon}><Webhook size={17} /></div>
          <div><strong>Callback visibility</strong><small>Inspect the event received by your application</small></div>
          <ChevronRight size={17} />
        </section>
      </div>
    </div>
  );
}

function CodeExample() {
  return (
    <div className={styles.codeWindow}>
      <div className={styles.codeBar}>
        <span className={styles.windowDots}><i /><i /><i /></span>
        <span>request-example.py</span>
        <span className={styles.exampleLabel}>ILLUSTRATIVE</span>
      </div>
      <pre><code><span className={styles.codeMuted}># Request shape only — check the current API docs</span>{"\n"}response = requests.post({"\n"}    api_url,{"\n"}    json={"{"}{"\n"}        <span className={styles.codeKey}>"amount"</span>: <span className={styles.codeNumber}>1000</span>,{"\n"}        <span className={styles.codeKey}>"phone_number"</span>: <span className={styles.codeString}>"2547XXXXXXXX"</span>,{"\n"}        <span className={styles.codeKey}>"account_reference"</span>: <span className={styles.codeString}>"ORDER-1048"</span>,{"\n"}    {"}"},{"\n"}    headers={"{"}<span className={styles.codeKey}>"Authorization"</span>: bearer_token{"}"},{"\n"})</code></pre>
      <div className={styles.codeFooter}><Code2 size={14} /> A conceptual example, not a copy-paste integration.</div>
    </div>
  );
}

export default function ThemeTestPage() {
  return (
    <main id="top" className={styles.page}>
      <section className={styles.heroShell}>
        <header className={styles.nav}>
          <Brand />
          <nav aria-label="Main navigation">
            <a href="#capabilities">Product <ChevronRight size={13} /></a>
            <a href="#developers">Developers <ChevronRight size={13} /></a>
            <a href="#businesses">Why NetPay <ChevronRight size={13} /></a>
          </nav>
          <div className={styles.navActions}>
            <Link href="/request-access/">Request access</Link>
            <Link className={styles.navCta} href="/request-access/">Get started</Link>
          </div>
          <a className={styles.mobileNavCta} href="/request-access/" aria-label="Get started">Start <ArrowRight size={15} /></a>
        </header>

        <div className={styles.hero}>
          <div className={styles.heroCopy}>
            <p className={styles.eyebrow}><span /> M-PESA PAYMENTS FOR BUSINESS SOFTWARE</p>
            <h1>M-Pesa payments, <em>without the integration headache.</em></h1>
            <p className={styles.heroDescription}>A practical payment gateway for collecting payments, tracking outcomes, and keeping transaction records in order.</p>
            <div className={styles.heroActions}>
              <Link className={styles.primaryCta} href="/request-access/">Get started <ArrowRight size={17} /></Link>
              <Link className={styles.secondaryCta} href="/api-overview/">Explore the API <ArrowUpRight size={16} /></Link>
            </div>
            <div className={styles.heroProof}>
              <span><CheckCircle2 size={15} /> Merchant-aware integrations</span>
              <span><CheckCircle2 size={15} /> Callback-backed outcomes</span>
            </div>
          </div>
          <PaymentPanel />
        </div>
        <p className={styles.heroFootnote}>A proposed NetPay marketing direction <span>·</span> Payment examples are illustrative only</p>
      </section>

      <section className={styles.capabilities} id="capabilities">
        <div className={styles.sectionIntro}>
          <p className={styles.sectionEyebrow}>WHAT YOU CAN DO</p>
          <h2>Everything you need to connect M-Pesa payments to your product.</h2>
        </div>
        <div className={styles.capabilityGrid}>
          {capabilities.map(({ icon: Icon, title, text }) => (
            <article className={styles.capability} key={title}>
              <span className={styles.capabilityIcon}><Icon size={23} strokeWidth={1.8} /></span>
              <h3>{title}</h3>
              <p>{text}</p>
            </article>
          ))}
        </div>
        <p className={styles.capabilityNote}><CircleHelp size={14} /> Provider transaction-status verification and merchant-specific validation rules may require additional configuration or remain unavailable. Check the current docs before relying on them.</p>
      </section>

      <section className={styles.developerSection} id="developers">
        <div className={styles.developerCopy}>
          <p className={styles.sectionEyebrow}>FOR DEVELOPERS</p>
          <h2>Clean integration. Clearer payment outcomes.</h2>
          <p>Build M-Pesa payment flows around a documented request, a merchant integration, and callback-backed status updates.</p>
          <Link className={styles.outlineCta} href="/api-overview/">View documentation <ArrowRight size={16} /></Link>
        </div>
        <CodeExample />
      </section>

      <section className={styles.businessSection} id="businesses">
        <div>
          <p className={styles.sectionEyebrow}>BUILT FOR REAL WORKFLOWS</p>
          <h2>Practical payment infrastructure for Kenyan businesses.</h2>
          <p>Whether you are building a shop system, pharmacy POS, restaurant platform or online store, NetPay is designed to help connect merchant M-Pesa integrations to the software your business runs on.</p>
        </div>
        <div className={styles.businessPoints}>
          <div><span><RefreshCw size={20} /></span><p><strong>Know what happened</strong><small>Separate request acceptance from callback-confirmed outcomes.</small></p></div>
          <div><span><Webhook size={20} /></span><p><strong>Work with payment events</strong><small>Use callback and event records to support your own workflows.</small></p></div>
          <div><span><ShieldCheck size={20} /></span><p><strong>Keep the integration understandable</strong><small>Start with current M-Pesa capabilities and documented limitations.</small></p></div>
        </div>
      </section>

      <section className={styles.finalCta}>
        <div><p className={styles.sectionEyebrow}>YOUR NEXT STEP</p><h2>Have an M-Pesa use case in mind?</h2><p>Explore the current API or tell us what you are building.</p></div>
        <div><Link className={styles.primaryCta} href="/request-access/">Get started <ArrowRight size={16} /></Link><Link className={styles.finalLink} href="/api-overview/">Explore the API <ArrowUpRight size={15} /></Link></div>
      </section>

      <footer className={styles.footer}>
        <Brand />
        <p>Practical M-Pesa infrastructure from NetHub.</p>
        <span>Theme test · Not the live homepage</span>
      </footer>
    </main>
  );
}
