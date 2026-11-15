# NetPay SEO & Marketing Strategy

> Strategic source of truth for NetPay's product positioning, website information architecture, SEO, content marketing, and customer acquisition.
>
> Primary market: businesses in Kenya that receive or want to receive customer payments, whether they operate from a physical location, online, or across both.
>
> Positioning principle: **We target businesses, not business models.**

## 1. Executive summary

NetPay should be presented as a business payment solution that helps businesses accept and manage payments through supported payment channels, with less manual work.

The customer is not buying an API, a Daraja connection, or a collection of technical features. They are trying to solve everyday business problems:

- Customers need a convenient way to pay.
- The business needs to know whether a payment was successful.
- Staff should not have to rely on screenshots or manually inspect messages to confirm every transaction.
- Orders and services should move forward when payment is confirmed.
- The business needs useful, organized payment records.

The marketing should explain these outcomes in clear, ordinary language. Technical detail belongs on developer and integration pages, where it helps a technical reader make an informed decision.

### Recommended core message

# Getting paid should be the easy part of running your business.

NetPay helps businesses accept payments, receive payment confirmations, and connect payments to the way they work. Whether you serve customers at a physical location or through a website or app, make paying easier for your customers and payment management easier for your business.

**NetPay — Payments that work for your business.**

NetPay's current payment foundation is M-Pesa Daraja. The strategy must communicate this honestly while presenting NetPay as a business-facing product, not merely a Daraja integration service.

This document defines how to explain and market the product. It is not authorization to advertise unimplemented functionality. The current product and repository must be checked before publishing any feature-specific claim.

SEO can improve relevance, discoverability, and conversion potential; no keyword plan or content volume guarantees first-page rankings or outranking a competitor.

## 2. Product definition and positioning

### 2.1 What is NetPay?

NetPay is a payment solution that helps businesses receive and manage customer payments through supported payment channels.

It helps connect a customer's payment with the business process that needs to know about it. For example, after a payment is successfully received and verified, a connected business application can be notified and can take the next appropriate action.

NetPay is intended for businesses that sell products, provide services, collect fees, or run digital services. A business may operate from a shop, office, restaurant, salon, website, mobile app, or a combination of these.

### 2.2 The problem NetPay addresses

The central problem is not simply that a business needs to receive money. It is the work and uncertainty around handling payments:

- A customer says they have paid, but the business still needs to confirm it.
- Staff spend time checking payment messages and matching them to sales.
- Orders or services wait while someone verifies a transaction.
- Payment information is scattered across messages, statements, spreadsheets, and business systems.
- A growing business needs its payment process to work consistently.

NetPay's marketing should connect its actual capabilities to these problems without suggesting that every problem is solved automatically in every setup.

### 2.3 Value proposition

| Business need | NetPay value to communicate |
|---|---|
| Let customers pay | Give customers a supported way to pay the business. |
| Know when payment succeeds | Receive payment outcomes through the configured integration. |
| Reduce manual checking | Automate supported payment confirmation steps instead of relying entirely on screenshots or manual checks. |
| Keep payment information organized | Use transaction information available through the product to support business records and follow-up. |
| Connect payment to business activity | Let a connected website, app, or business system respond to a verified payment. |
| Build a more convenient experience | Make payment part of the customer's journey instead of an unrelated manual process. |

### 2.4 What NetPay is not

Do not position NetPay as:

- A bank, wallet, lender, or deposit-taking institution.
- A replacement for M-Pesa or a mobile network operator.
- A standalone POS terminal or till device.
- An accounting, inventory, or complete business-management system.
- A payment-link product unless payment links are implemented and available.
- A card, PayPal, Airtel Money, or multi-provider gateway today unless those methods have actually shipped.
- A guarantee that every payment is instant, never fails, or never needs investigation.

### 2.5 The relationship with Tawala

Tawala and NetPay serve related but distinct business needs.

- **Tawala** is NetHub's business management and POS product. It helps businesses manage sales and day-to-day operations.
- **NetPay** focuses on payment capabilities: receiving payment requests, handling payment outcomes, and supporting payment-related workflows through its supported integrations.

It is appropriate to mention Tawala when explaining that NetHub has a POS/business-management solution for physical businesses. Do not imply that NetPay itself is a POS system, that it supplies POS hardware, or that every Tawala and NetPay workflow is already integrated. Describe a direct integration only after it is implemented, tested, and available to customers.

Suggested cross-reference:

> Running a physical shop and need more than payment processing? Explore Tawala, NetHub's business management and POS solution.

Use a verified Tawala URL and current product description when adding this link.

## 3. Audience and customer understanding

### 3.1 Primary audience: SME owners and operators

Speak first to the person responsible for running the business. That person may also be the developer, but their first concern is usually whether the solution helps the business.

Target businesses by their payment needs and operating context—not only by whether they are online.

#### A. Physical businesses

Examples include retail shops, minimarts, boutiques, supermarkets, pharmacies, agrovets, hardware and electronics shops, restaurants, cafés, hotels, salons, barbershops, repair shops, service businesses, wholesalers, and distributors.

**Their questions:** How do I receive customer payments? How do I know a payment went through? Can I reduce manual checking? How do I keep payment records? Can this work with the systems my business uses?

**Messaging:** Focus on payment visibility, confirmation, reduced manual work, and fit with the business's existing systems. Be explicit about what requires an application integration. Do not claim automatic till reconciliation or automatic matching of every walk-in sale unless that exact workflow is supported.

For businesses seeking a full point-of-sale and business-management system, introduce Tawala as a separate, complementary NetHub product. Do not present Tawala features as NetPay features.

#### B. Online stores and e-commerce businesses

Examples include product stores, social-commerce businesses with a website, and businesses taking orders online.

**Their questions:** Can customers pay online? Can my store know when an order has been paid? Can I reduce payment screenshots and manual order confirmation?

**Messaging:** Explain the customer's payment journey and how a connected store can respond to a confirmed payment. State the supported integration requirements and payment method accurately.

#### C. Service and booking businesses

Examples include appointment-based businesses, event services, consultants, training providers, and booking platforms.

**Their questions:** Can customers pay for a booking or service? Can I confirm payment before proceeding? Can my system be notified?

**Messaging:** Explain payment confirmation and the potential to connect a confirmed payment to the service workflow. Do not advertise a ready-made booking product.

#### D. Mobile apps, SaaS, and digital services

Examples include app businesses, software subscriptions, membership services, and digital products.

**Their questions:** Can my application collect payments? Can it know when payment succeeds? Can access or an order be updated after confirmation?

**Messaging:** Explain the integration value in business language first. Technical documentation should then provide the implementation detail.

#### E. Developers and software agencies

Developers are an important enabling audience, but they should not define the entire brand.

**Their questions:** Is there an API? How do I authenticate? Which payment flows are supported? How are callbacks, verification, and errors handled? What are the integration requirements?

**Messaging:** Provide accurate API documentation, clear examples, onboarding requirements, and capability boundaries. Keep developer language on developer-focused pages.

### 3.2 Customer decision stages

1. **Problem aware:** “I spend too much time confirming customer payments.”
2. **Solution aware:** “Can I automate payment confirmation?”
3. **Product aware:** “What is NetPay and how does it work?”
4. **Evaluation:** “Does it support my business and payment method? What do I need to get started?”
5. **Action:** “How do I contact the team, onboard, or integrate it?”

Every key page should help the visitor answer the next question and move naturally to the next step.

## 4. Brand voice and writing rules

### 4.1 Voice

NetPay should sound clear, practical, confident, helpful rather than overly promotional, business-minded rather than developer-centric, locally relevant to Kenyan businesses, and honest about what is available today.

### 4.2 Prefer everyday language

| Avoid leading with | Say instead |
|---|---|
| Daraja API integration | Accept and manage supported M-Pesa payments |
| Webhooks and callbacks | Your connected system receives a payment update |
| Transaction reconciliation | Matching payment information with business records |
| API credentials | The account details needed to connect your business |
| Payment orchestration | Managing payment activity through one integration |
| C2B | Customer-to-business payments (explain the term only where useful) |
| STK Push | A payment request sent to the customer's phone (where applicable) |
| Idempotency and asynchronous processing | Keep payment handling reliable when explaining technical behavior to developers |

Technical terms are acceptable in documentation, FAQs, and technical pages when defined. Do not use them as the main explanation on the homepage.

### 4.3 Messaging pillars

1. **Make paying easier:** A convenient payment experience for customers.
2. **Know when you've been paid:** Clear, dependable payment outcomes through supported integrations.
3. **Spend less time checking:** Reduce manual work where payment workflows are connected.
4. **Make payments part of business operations:** Let connected systems respond to confirmed payment outcomes.
5. **Choose tools that fit your business:** NetPay for payment workflows; Tawala for POS and broader business management where appropriate.

### 4.4 Claims discipline

Every public claim must be classified as one of:

- **Available now:** Verified in the current production product and supported by documentation.
- **Available with integration/configuration:** Works when the merchant or developer completes stated setup.
- **Planned:** A roadmap item, never presented as currently available.
- **Not supported:** Do not market it as a NetPay feature.

Avoid absolute claims such as “instant,” “zero failures,” “guaranteed,” “all payment methods,” “works with every till,” or “no technical setup required” unless there is specific evidence and the wording is appropriately qualified.

## 5. Website information architecture and page-by-page content plan

The website should be organized around visitor questions. Each page needs a distinct search intent, useful content, and one clear primary action. Do not create thin pages that repeat the same paragraph with a different keyword.

### 5.1 Homepage — /

**Purpose:** Help a business owner understand what NetPay is, who it is for, and why it may help within the first few seconds.

**Search intent:** NetPay, payment solution for businesses, payment gateway Kenya, accept business payments.

**Suggested title:** NetPay | Business Payment Solutions in Kenya

**Suggested meta description:** Make it easier for your business to receive and manage customer payments. Discover NetPay's supported payment solutions for physical and digital businesses.

Recommended content order:

1. **Hero:** “Getting paid should be the easy part of running your business.” Explain in one or two short sentences that NetPay helps businesses accept payments and receive payment confirmations through supported integrations. Primary CTA: “Talk to our team” or the verified onboarding CTA. Secondary CTA: “See how it works.”
2. **Recognize the visitor:** Physical business, online store, service business, mobile app or digital platform. Make clear that a business does not need to be online-only to be relevant.
3. **Explain the problem:** Manual payment checking, payment screenshots and follow-ups, delayed order or service confirmation, disorganized payment information.
4. **Explain how NetPay helps:** Accept supported payments, receive payment outcomes, connect a confirmed payment to a connected business system, and keep payment activity easier to manage.
5. **How it works:** Customer makes a payment; payment is processed through the configured provider; NetPay receives/handles the payment outcome; the connected business system can take the next action.
6. **Supported payment method:** Explain the currently supported M-Pesa capability accurately. Link to the dedicated M-Pesa page. Do not suggest other providers are available until shipped.
7. **Who it is for:** Use business examples, not generic industry keyword lists. Include physical and digital businesses.
8. **NetPay and Tawala:** Explain the distinction: NetPay handles payment capabilities; Tawala is the POS/business-management product. Link to Tawala with a clear label. Never suggest a feature belongs to both products unless it does.
9. **Trust and clarity:** Explain merchant setup and support honestly. Include verified company/contact details, security explanations, and policies. Use only real testimonials, customer counts, certifications, and logos with permission.
10. **FAQs and final CTA:** Answer common buying questions and end with a practical next step.

**Conversion goal:** A qualified business owner understands the product and contacts the team or starts the verified onboarding journey.

### 5.2 How it works — /how-it-works

**Purpose:** Remove uncertainty for non-technical business owners.

**Search intent:** how online payments work, how to confirm M-Pesa payments, business payment process.

Include:
- A plain-language explanation of the customer's payment journey.
- What the business needs before getting started.
- What happens when a customer pays.
- How NetPay communicates the payment outcome.
- What the business's connected system can do next.
- What happens when a payment is pending, unsuccessful, or needs checking—only describe verified behavior.
- A simple diagram with customer, business, NetPay, and supported provider.
- A clear distinction between an ordinary customer payment and a payment automatically linked to a specific sale.

CTA: “Discuss your payment setup.”

### 5.3 Business solutions — /businesses or /solutions

**Purpose:** Help visitors find the scenario closest to their business without implying unsupported industry-specific products.

Possible sections:
- Retail and physical businesses.
- Restaurants and hospitality.
- Service providers.
- Online stores.
- Digital services and subscriptions.
- Businesses with custom websites or applications.

Each section should describe the business problem and relevant NetPay capability. Where a physical business needs sales, inventory, staff, or POS management, link to Tawala rather than implying NetPay provides those tools.

Avoid creating separate industry pages until each has unique, substantial content and a genuinely relevant supported use case.

### 5.4 M-Pesa payments — /mpesa-payments or /mpesa-integration

**Purpose:** Capture high-intent searches while explaining M-Pesa as a supported payment method, not the whole identity of NetPay.

**Search intent:** M-Pesa payment gateway Kenya, accept M-Pesa payments online, M-Pesa integration for business.

Include:
- What businesses can do with the currently supported M-Pesa flows.
- Explain STK Push in ordinary language where relevant.
- Explain C2B support and its requirements accurately.
- Merchant onboarding requirements.
- What a business needs to configure.
- How payment confirmations and verification work.
- Integration requirements and limitations.
- Link to technical documentation.

Do not say NetPay supports every Paybill, Till, account, or payment scenario unless verified. Clarify merchant configuration and any Safaricom/provider requirements.

### 5.5 Features — /features

**Purpose:** Give evaluators a factual overview of available capabilities.

Organize around customer outcomes, not internal module names:
- Initiating supported payment requests.
- Receiving payment notifications.
- Verifying payment outcomes.
- Viewing or working with transaction information, if available in the current product.
- Reconciliation support, with exact scope and limitations stated.

For each item, specify availability, setup requirements, and limitations. Remove any feature from the public page if it cannot be demonstrated in the current production product.

### 5.6 Developers — /developers

**Purpose:** Convert technical evaluators after the business value is clear.

Include:
- What NetPay's integration is designed to help developers build.
- Supported flows and payment methods.
- API overview and authentication.
- Merchant configuration and integration onboarding.
- Request/response examples.
- Callback/notification behavior.
- Payment verification.
- Error handling and testing.
- Security responsibilities and production checklist.
- Link to full API documentation.

Use exact technical behavior from the current API specification. Do not invent SDKs, plugins, sample apps, uptime commitments, or integration times.

### 5.7 Pricing — /pricing

**Purpose:** Answer the commercial question without hiding material costs.

Publish this page only when approved, current pricing and fee rules are known.

Include, where applicable:
- NetPay platform fees.
- Payment provider charges.
- Transaction fees and who bears them.
- Taxes and other applicable charges.
- Any setup, subscription, or minimum charges.
- Refund/reversal treatment, if supported.
- Examples that clearly state assumptions.

If pricing is quote-based, say so plainly and explain what information is needed for a quote. Never invent “free,” “no hidden fees,” or a specific transaction rate.

### 5.8 About — /about

**Purpose:** Establish who is behind NetPay and why the product exists.

Include:
- NetPay's purpose: making business payments easier to accept and manage.
- The problem it is solving for businesses.
- Its relationship to NetHub.
- The team's commitment to practical, dependable business software.
- Verified company identity and location details.
- A clear distinction between NetPay and other NetHub products.

Avoid inflated claims such as “Kenya's leading,” “number one,” or “trusted by thousands” without verifiable evidence.

### 5.9 Contact — /contact

**Purpose:** Make it easy for a prospective customer to take the next step.

Include:
- A friendly invitation to discuss their business payment needs.
- Verified email, phone, location, and business hours only.
- A short contact form asking only for useful information: name, business, contact details, and what they want to achieve.
- A choice of business enquiry or developer/integration enquiry if operationally supported.
- Expected response time only if the team can consistently meet it.
- Privacy notice explaining how submitted information is handled.

Do not invent contact details. Use the official, verified NetPay/NetHub contact channels configured for the product.

### 5.10 FAQ — /faq

**Purpose:** Answer real objections and capture question-based search demand.

Recommended questions:
- What is NetPay?
- Who can use NetPay?
- Can a physical business use NetPay?
- Does my business need a website?
- Can I accept M-Pesa payments?
- What do I need to get started?
- How does my business know when a customer has paid?
- Do I need a developer?
- Can NetPay connect to my existing website or app?
- Is NetPay a POS system?
- What is the difference between NetPay and Tawala?
- Which payment methods are currently supported?
- How much does NetPay cost?
- How do I get help?

Answers must reflect current product behavior. Link each answer to the relevant detailed page. Do not add FAQ structured data for content that is not visibly present on the page.

### 5.11 Trust, privacy, and legal pages

Publish accurate, accessible pages for:
- Privacy policy.
- Terms of service.
- Payment terms and merchant responsibilities where applicable.
- Security information and responsible disclosure/contact route, if established.
- Refund, reversal, and dispute guidance only to the extent supported by the actual service and provider arrangements.

These pages must be reviewed against actual business, data, and operational practices. Do not copy another gateway's legal terms.

## 6. SEO strategy

### 6.1 Search strategy

Build topical authority around business payment needs in Kenya. Use three layers:

1. **Commercial intent:** payment gateway, payment solution, accept payments.
2. **Problem intent:** confirm payments, reduce manual checking, manage payment records.
3. **Implementation intent:** M-Pesa integration, payment API, website/app integration.

Do not make the homepage compete with every supporting page for the same phrase. Give each page one primary topic and a set of closely related questions.

### 6.2 Keyword clusters and page mapping

These are target themes to validate with Google Search Console, Keyword Planner, and actual search results. They are not claims about search volume or ranking difficulty.

| Cluster | Example phrases | Primary destination |
|---|---|---|
| Business payment solution | business payment solution Kenya, payment solutions for businesses | Homepage |
| Payment gateway | payment gateway Kenya, online payment gateway Kenya | Homepage / dedicated gateway page if substantively distinct |
| Physical business payments | accept customer payments, manage business payments, M-Pesa payments for shops | Business solutions / M-Pesa page |
| Online payments | accept payments online Kenya, website payment integration | Online payments page |
| E-commerce | e-commerce payments Kenya, online store M-Pesa payments | Online store use-case section/page |
| M-Pesa | M-Pesa payment gateway, M-Pesa integration Kenya | M-Pesa page |
| Payment confirmation | automatic payment confirmation, verify M-Pesa payment | How it works / relevant guide |
| Reconciliation | payment reconciliation for business, match customer payments | Feature page or educational article, carefully scoped |
| Developers | payment API Kenya, M-Pesa API integration | Developers |
| Mobile apps | mobile app payment integration Kenya | Developers / mobile app use case |
| Business management/POS | POS system Kenya, shop management system | Tawala page/site, not NetPay feature pages |

### 6.3 Supporting content and article plan

Create genuinely useful guides that answer a question fully and lead naturally to the appropriate product page.

**Business-owner education**
1. How to make it easier for customers to pay your business in Kenya.
2. How to reduce the time spent confirming customer payments.
3. What to consider before choosing a payment solution for your business.
4. How to keep better records of customer payments.
5. Mobile payments for physical shops: what business owners should consider.
6. How to handle payment confirmation when selling through WhatsApp and a website—clearly distinguish supported NetPay workflows from manual processes.
7. When does a growing business need payment automation?
8. Payment collection for service businesses: a practical guide.

**Online business education**
9. How to accept M-Pesa payments on a website.
10. What happens after a customer pays for an online order?
11. How to reduce manual payment checks in an online store.
12. What to consider when adding payments to a mobile app.
13. Payment confirmation and order fulfilment: how they fit together.

**Developer education**
14. M-Pesa integration: direct integration versus using a payment platform.
15. A practical guide to testing payment flows.
16. How to verify payment outcomes safely.
17. Designing reliable payment handling for websites and apps.
18. Common causes of payment integration problems and how to investigate them.

Every article should answer the query directly near the beginning, use clear headings and concise explanations, include original examples and diagrams where useful, link to one relevant product page and related guides, state the date or version when technical details may change, be reviewed against current provider documentation, and avoid keyword stuffing and repetitive AI-generated pages.

### 6.4 Competitor landscape and differentiation

Competitors to monitor include:

- **Pesapal:** Markets payment acceptance for online and in-person business contexts, with payment products and integrations.
- **Paystack:** Emphasizes online/offline payment acceptance, checkout experience, payment methods, and developer tools.
- **IntaSend:** Communicates payment collection, payment links, invoicing, and developer-facing payment services.
- **Other Kenyan payment providers:** Maintain a current list based on actual search results, customer alternatives, and relevant product overlap.

Competitor messaging is not proof of feature parity, market share, or search ranking. Review each competitor's current official product pages before publishing comparative claims.

#### The opportunity for NetPay

Do not try to win by copying every competitor's feature list. Build a clear, focused story around:

1. **Business-first clarity:** Explain the value to an owner before introducing technical implementation.
2. **Physical and digital relevance:** Do not imply that only online stores need better payment processes.
3. **Practical payment confirmation:** Explain the difference between receiving money and knowing which business activity it belongs to.
4. **A connected NetHub product ecosystem:** Explain the distinct roles of NetPay and Tawala without blurring their capabilities.
5. **Transparent capability boundaries:** State exactly what is supported today and what requires configuration or a connected application.

Avoid competitor comparison pages until NetPay can substantiate every comparison with current, like-for-like evidence. Never claim to be cheaper, faster, safer, or more reliable without evidence.

### 6.5 Local relevance

The initial market is Kenya. Use Kenyan business examples, local terminology, and KSh where relevant. Explain M-Pesa in a familiar way without making every page a Daraja tutorial.

Use location-specific landing pages only where NetPay has a genuine local offering and can provide unique value. Do not generate doorway pages for towns or counties with only swapped place names.

### 6.6 On-page SEO standards

For every indexable page:
- One descriptive, unique title tag.
- One concise, unique meta description focused on the visitor's decision.
- One clear H1 that matches the page's purpose.
- Logical H2/H3 structure.
- Descriptive URLs in lowercase with hyphens.
- Helpful internal links using meaningful anchor text.
- Descriptive image alt text; decorative images should have empty alt text.
- Canonical URL where needed.
- Open Graph title, description, and image.
- Fast, responsive, accessible page experience.
- No duplicated or thin location/industry pages.
- No keyword stuffing.

### 6.7 Technical SEO checklist

The implementation team should verify:
- Search engines can crawl and render important public pages.
- Correct production domain and HTTPS canonicalization.
- XML sitemap includes canonical, indexable pages only.
- robots.txt does not accidentally block public pages or assets.
- Staging, preview, dashboard, and authenticated pages are not indexed.
- Correct redirects for changed URLs; no redirect chains or loops.
- No accidental duplicate pages from query parameters or trailing slash variants.
- Useful 404 page and correct status codes.
- Structured data matches visible, factual page content.
- Page metadata is unique and not left as framework defaults.
- Images are optimized and dimensioned to reduce layout shift.
- Mobile usability, keyboard access, and readable contrast are checked.
- Core Web Vitals are measured on real pages, not assumed from a local build.
- Analytics and conversion events respect the privacy policy and consent requirements.

Suggested structured data, only where eligible and accurate:
- Organization for the real operating organization.
- WebSite for the public site.
- Product only if the page genuinely describes the product and all properties are accurate.
- BreadcrumbList where breadcrumbs are visible.
- Article for editorial articles.
- FAQPage only where appropriate under current search engine eligibility rules; do not expect a rich result.

Do not add fake ratings, reviews, prices, addresses, or aggregate claims to structured data.

## 7. Conversion strategy

SEO traffic is useful only if visitors can understand the offer and take a sensible next step.

### Primary calls to action

Use one consistent primary CTA across key pages, such as “Talk to our team”, “Get started”, or “Discuss your payment needs”. Choose the CTA that matches the actual onboarding process. Do not use “Start free” or “Sign up” unless that flow exists and is ready.

### Secondary calls to action

- See how it works.
- Explore supported payments.
- Read developer documentation.
- Explore Tawala for visitors who need POS/business management.

### Contact and enquiry experience

Keep the first contact step simple. Ask for only information needed to respond: name, business name, contact method, business type or use case, and what the visitor wants to achieve.

If a technical integration enquiry needs more detail, collect it after the initial contact rather than making every business owner complete a developer questionnaire.

### Trust elements

Use only verifiable evidence: real product screenshots, accurate supported-payment descriptions, clear onboarding requirements, real customer testimonials with permission, actual company details and support channels, clear privacy and terms pages, and honest explanations of what the product does and does not do.

## 8. Measurement and improvement

### 8.1 Baseline before optimization

Before setting targets, record:
- Current indexed pages.
- Search queries and impressions.
- Click-through rate by page/query.
- Organic landing page sessions.
- Qualified enquiries and their sources.
- Contact form completion rate.
- Visitor-to-enquiry conversion rate.
- Search visibility for the agreed keyword set.
- Technical SEO issues and Core Web Vitals.

Use Google Search Console and a privacy-conscious analytics setup. Ensure conversion tracking is tested and documented.

### 8.2 Useful events

Subject to the actual site and consent configuration:
- contact CTA clicked.
- contact form started.
- contact form submitted.
- developer docs opened.
- how-it-works viewed.
- Tawala link clicked.

Track meaningful actions, not every click. Do not send personal information or payment data into analytics events.

### 8.3 Review cadence

**Weekly:** Check indexing, crawl errors, broken pages, and conversion issues. Review new enquiries and identify recurring customer questions.

**Monthly:** Review Search Console query/page performance. Identify pages with impressions but weak click-through rate. Improve pages that attract the wrong audience or fail to convert. Publish or update content based on genuine search demand.

**Quarterly:** Reassess keyword priorities and competitor positioning. Review product capabilities with engineering/product owners. Remove outdated claims and refresh technical guidance. Review whether content produces qualified business enquiries.

### 8.4 Practical success measures

Prioritize:
1. Qualified enquiries from relevant businesses.
2. Enquiry-to-customer conversion.
3. Organic traffic to high-intent pages.
4. Search impressions and clicks for relevant non-brand queries.
5. Search visibility for priority topics.
6. Technical health and page experience.

Do not optimize for raw traffic alone. A page attracting visitors who cannot use the product is not necessarily a successful SEO page.

## 9. Rollout plan

### Phase 1 — Establish truth and foundations

- Confirm current production capabilities with product/engineering.
- Approve the product description, audience, and claims.
- Verify official contact details, URLs, pricing position, and onboarding path.
- Audit the existing site and its indexable pages.
- Set up Search Console and analytics baseline.

**Exit condition:** Every public-facing claim has an owner and evidence.

### Phase 2 — Build the core website story

Prioritize homepage, how it works, business solutions, M-Pesa payments, features, developers/documentation, about, contact, FAQ, privacy and terms.

Publish pricing only after the commercial model is approved and confirmed.

**Exit condition:** A business owner can understand NetPay, assess fit, see supported capabilities, and contact the team.

### Phase 3 — Build topical authority

- Publish the first business-owner guides.
- Add online business and developer guides.
- Link articles to relevant product pages.
- Use customer questions and sales conversations to choose future topics.
- Refresh pages when product capabilities or provider behavior changes.

**Exit condition:** Content is useful, internally linked, accurate, and mapped to real search intent.

### Phase 4 — Improve based on evidence

- Review rankings, queries, traffic quality, and enquiries.
- Expand topics that attract qualified prospects.
- Rewrite pages that get impressions but do not earn clicks.
- Improve conversion paths based on observed visitor behavior.
- Monitor competitor product and messaging changes.

**Exit condition:** SEO work is driven by measured business outcomes, not publishing volume alone.

## 10. Editorial and product governance

SEO content can outlive the feature it describes. Assign clear ownership.

| Content or claim | Required reviewer |
|---|---|
| Payment methods and supported flows | Product/engineering |
| API behavior and integration examples | Engineering |
| Pricing and fees | Business/product owner |
| Privacy, terms, and data handling | Legal/compliance owner |
| Customer stories and testimonials | Customer/business owner with consent |
| SEO metadata and internal links | Marketing/content owner |
| Tawala positioning and cross-links | Owners of both products |

Review product capability claims whenever a payment flow changes. Review provider-specific guidance when Safaricom documentation or integration requirements change.

Maintain a simple claim register with claim, page/asset, status (available, configuration-dependent, planned, or unsupported), evidence/documentation, reviewer, and last reviewed date.

## 11. Approved messaging reference

### Short description

NetPay helps businesses accept and manage customer payments through supported payment channels, with less manual work.

### Medium description

NetPay is a business payment solution for companies that want to make it easier for customers to pay and easier for the business to keep track of payments. Whether you serve customers from a physical location or through a website or app, NetPay helps connect supported payments with the systems and processes your business relies on.

### Long description

Getting paid is an important part of every business, but checking payments, confirming orders, and keeping payment information organized can take valuable time. NetPay helps businesses accept payments through supported payment channels and receive payment outcomes through their configured integrations. This can help a connected business system respond when a payment is confirmed, reducing the need for manual steps in supported workflows. NetPay is designed for businesses across physical and digital settings, with technical integration options for websites, applications, and business systems.

### Tagline

**Payments that work for your business.**

### Message to remember

**We target businesses, not business models.** A business may operate from a physical shop, online, or both. NetPay's marketing should help the owner understand the payment problem it solves, what is supported today, and what they need to do next.

## 12. Research notes and competitor references

This is a qualitative review of competitor messaging and publicly presented product positioning, not a verified ranking or market-share study.

Competitor pages to revisit during ongoing research:

- [Pesapal](https://www.pesapal.com/) — Review its current online and in-person payment messaging, merchant products, integrations, and business use cases.
- [Paystack](https://paystack.com/) — Review its payment acceptance, checkout, payment method, and developer messaging; confirm Kenya-specific availability before making comparisons.
- [IntaSend](https://intasend.com/) — Review its business payment collection, invoices, payment links, and developer positioning; verify which products and payment methods are currently available in Kenya.

Before publishing a competitor comparison:
1. Revisit the official page and record the review date.
2. Confirm the feature is available in the relevant market.
3. Compare like-for-like functionality and commercial terms.
4. Keep screenshots/links or other evidence in the research record.
5. Avoid claims about ranking, revenue, customer numbers, or market leadership without independent evidence.

### Research still required

- Validate keyword volumes, difficulty, and search intent using live keyword data.
- Capture current Google results for priority queries in Kenya.
- Establish NetPay's baseline positions in Search Console.
- Identify additional competitors from actual Kenyan search results and customer alternatives.
- Verify the precise current production feature set and merchant onboarding journey.

## 13. Final strategic direction

NetPay should not sound like a developer tool that happens to be useful to businesses. It should sound like a business solution that also gives developers the tools to integrate it.

Lead with the business problem. Explain the value in plain language. Show how it works. Be honest about supported payment methods and setup requirements. Give technical readers a clear path to the documentation.

Physical businesses belong in the audience, but NetPay must not be mistaken for a POS or shop-management system. Tawala is the relevant NetHub product for that broader operational need. Online stores, service businesses, mobile applications, and digital platforms are equally valid audiences when their payment requirements match NetPay's current capabilities.

**The goal is simple:** help the right business owner recognize their payment problem, understand how NetPay can help, trust what is being promised, and know exactly how to take the next step.
