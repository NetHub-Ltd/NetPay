import type { Metadata } from "next";
import Link from "next/link";
import {
  ArrowDownLeft,
  ArrowRight,
  ArrowUpRight,
  Check,
  CheckCircle2,
  CircleHelp,
  Code2,
  ListChecks,
  RefreshCw,
  ShieldCheck,
  Smartphone,
  Wallet,
  Webhook,
} from "lucide-react";
import { PublicSiteFrame } from "../components/PublicSiteFrame";
import styles from "./home.module.css";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "https://pay.nethub.co.ke";

export const metadata: Metadata = {
  title: "M-Pesa payments without the integration headache",
  description:
    "Connect business software to M-Pesa with merchant-owned Daraja integrations, STK Push, callback-backed payment outcomes, and durable payment events.",
  alternates: { canonical: "/" },
  openGraph: {
    type: "website",
    locale: "en_KE",
    url: siteUrl,
    title: "NetPay | M-Pesa payments without the integration headache",
    description:
      "A practical M-Pesa payment gateway for collecting payments, tracking outcomes, and keeping transaction records in order.",
  },
  twitter: {
    card: "summary_large_image",
    title: "NetPay | M-Pesa payments without the integration headache",
    description: "Merchant-aware M-Pesa integrations and callback-backed payment outcomes for business software.",
  },
  robots: { index: true, follow: true },
};

const structuredData = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": siteUrl + "/#organization",
      name: "NetHub",
      url: "https://nethub.co.ke",
      logo: siteUrl + "/opengraph-image",
    },
    {
      "@type": "WebSite",
      "@id": siteUrl + "/#website",
      url: siteUrl,
      name: "NetPay",
      publisher: { "@id": siteUrl + "/#organization" },
      inLanguage: "en-KE",
    },
    {
      "@type": "SoftwareApplication",
      "@id": siteUrl + "/#software",
      name: "NetPay",
      url: siteUrl,
      applicationCategory: "FinanceApplication",
      operatingSystem: "Web",
      description: "An M-Pesa Daraja gateway for merchant-owned integrations, STK Push, and provider-informed payment status.",
      publisher: { "@id": siteUrl + "/#organization" },
    },
  ],
};

const capabilities = [
  { icon: Smartphone, title: "STK Push", text: "Initiate an M-Pesa payment request from your application and track its reported outcome." },
  { icon: ArrowDownLeft, title: "C2B callbacks", text: "Receive supported customer-to-business callbacks for a connected merchant when C2B is configured." },
  { icon: ShieldCheck, title: "Clear payment states", text: "Distinguish an accepted request from a payment outcome supported by provider evidence." },
  { icon: ListChecks, title: "Payment records", text: "Use callback and payment-event records to support your own reconciliation workflow." },
];

const sampleRows = [
  { date: "28 Oct · 10:44", amount: "KES 1,000", state: "Example", kind: "matched" },
  { date: "28 Oct · 09:21", amount: "KES 2,500", state: "Example", kind: "matched" },
  { date: "27 Oct · 16:32", amount: "KES 980", state: "Example", kind: "matched" },
  { date: "27 Oct · 11:07", amount: "KES 3,200", state: "Review", kind: "review" },
];

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
          <div><span>Phone number</span><strong>254 7XX XXX XXX</strong></div>
        </div>
        <ol className={styles.timeline}>
          <li><span className={styles.timelineIcon}><Smartphone size={13} /></span><div><strong>Payment request sent</strong><small>Waiting for provider response</small></div></li>
          <li><span className={styles.timelineIcon}><Check size={13} /></span><div><strong>Provider callback</strong><small>Example state · not live</small></div></li>
          <li><span className={styles.timelineIcon}><Check size={13} /></span><div><strong>Payment status updated</strong><small>Based on available provider evidence</small></div></li>
        </ol>
        <p className={styles.sampleNote}>Sample interface only — no live payment is shown.</p>
      </section>
      <div className={styles.sidePanels}>
        <section className={styles.reconciliationCard}>
          <div className={styles.smallPanelHeading}><h3>Payment records</h3><span>Preview</span></div>
          <div className={styles.tableHeader}><span>Date</span><span>Amount</span><span>State</span></div>
          {sampleRows.map((row) => (
            <div className={styles.tableRow} key={row.date}>
              <span>{row.date}</span><span>{row.amount}</span><span className={row.kind === "matched" ? styles.matched : styles.review}>{row.state}</span>
            </div>
          ))}
          <p className={styles.sampleNote}>Illustrative records, not connected data.</p>
        </section>
        <section className={styles.callbackCard}>
          <div className={styles.callbackIcon}><Webhook size={17} /></div>
          <div><strong>Callback visibility</strong><small>Understand the provider event your integration received</small></div>
          <ArrowRight size={17} />
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
      <pre><code><span className={styles.codeMuted}># Request shape only — check the current API docs</span>{"\n"}response = requests.post({"\n"}    api_url,{"\n"}    json={"{"}{"\n"}        <span className={styles.codeKey}>&quot;amount_minor&quot;</span>: <span className={styles.codeNumber}>250000</span>,{"\n"}        <span className={styles.codeKey}>&quot;phone_number&quot;</span>: <span className={styles.codeString}>&quot;07XXXXXXXX&quot;</span>,{"\n"}        <span className={styles.codeKey}>&quot;client_reference&quot;</span>: <span className={styles.codeString}>&quot;ORDER-1048&quot;</span>,{"\n"}    {"}"},{"\n"}    headers=auth_headers,{"\n"})</code></pre>
      <div className={styles.codeFooter}><Code2 size={14} /> Conceptual example — follow the API overview for the current contract.</div>
    </div>
  );
}

export default function HomePage() {
  return (
    <PublicSiteFrame>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }} />
      <main id="main-content" className={styles.page} tabIndex={-1}>
        <section className={styles.heroShell}>
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
          <p className={styles.heroFootnote}>Payment examples are illustrative only <span>·</span> Current capabilities and limitations are documented</p>
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
                <h3>{title}</h3><p>{text}</p>
              </article>
            ))}
          </div>
          <p className={styles.capabilityNote}><CircleHelp size={14} /> Some Daraja capabilities require extra configuration. Check the API overview for current support and limits.</p>
        </section>

        <section className={styles.developerSection} id="developers">
          <div className={styles.developerCopy}>
            <p className={styles.sectionEyebrow}>FOR DEVELOPERS</p>
            <h2>Clean integration. Clearer payment outcomes.</h2>
            <p>Build M-Pesa payment flows around a documented request, a merchant integration, and callback-backed status updates.</p>
            <Link className={styles.outlineCta} href="/developers/">Explore developer resources <ArrowRight size={16} /></Link>
          </div>
          <CodeExample />
        </section>

        <section className={styles.businessSection} id="businesses">
          <div>
            <p className={styles.sectionEyebrow}>BUILT FOR REAL WORKFLOWS</p>
            <h2>Practical payment infrastructure for Kenyan businesses.</h2>
            <p>Whether you are building a shop system, pharmacy POS, restaurant platform or online store, NetPay is designed to connect merchant M-Pesa integrations to the software your business runs on.</p>
          </div>
          <div className={styles.businessPoints}>
            <div><span><RefreshCw size={20} /></span><p><strong>Know what happened</strong><small>Separate request acceptance from callback-backed outcomes.</small></p></div>
            <div><span><Webhook size={20} /></span><p><strong>Work with payment events</strong><small>Use callback and event records to support your own workflows.</small></p></div>
            <div><span><Wallet size={20} /></span><p><strong>Built around merchant integrations</strong><small>Each connected merchant supplies their own Daraja credentials.</small></p></div>
          </div>
        </section>

        <section className={styles.finalCta}>
          <div><p className={styles.sectionEyebrow}>YOUR NEXT STEP</p><h2>Have an M-Pesa use case in mind?</h2><p>Explore the current API or tell us what you are building.</p></div>
          <div><Link className={styles.primaryCta} href="/request-access/">Get started <ArrowRight size={16} /></Link><Link className={styles.finalLink} href="/why-netpay/">Why NetPay <ArrowUpRight size={15} /></Link></div>
        </section>
      </main>
    </PublicSiteFrame>
  );
}
