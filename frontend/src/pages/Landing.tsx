import { Link } from 'react-router-dom'
import {
  ArrowRight,
  ArrowUpRight,
  Bell,
  Check,
  ChevronRight,
  CircleCheck,
  CreditCard,
  Landmark,
  LockKeyhole,
  Radio,
  ShieldCheck,
  Webhook,
  Zap,
} from 'lucide-react'
import { useAuth } from '../auth/authState'

const button =
  'inline-flex items-center justify-center gap-2 rounded-xl px-5 py-3 text-sm font-semibold transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--accent)]'

const highlights = [
  {
    icon: CreditCard,
    title: 'Request payments',
    description:
      'Send an M-Pesa phone prompt and see when the customer responds.',
  },
  {
    icon: CircleCheck,
    title: 'Know what settled',
    description:
      'Follow each payment from request to result with a clear status and ledger trail.',
  },
  {
    icon: Webhook,
    title: 'Keep systems in sync',
    description:
      'Connect your app to payment updates with HTTPS notification endpoints.',
  },
]

const steps = [
  {
    number: '01',
    title: 'Connect your shortcode',
    description: 'Add a paybill or till and configure your Daraja connection.',
    icon: Landmark,
  },
  {
    number: '02',
    title: 'Send a payment request',
    description: 'Enter a customer number and amount to send a phone prompt.',
    icon: Zap,
  },
  {
    number: '03',
    title: 'Track the outcome',
    description: 'See the result in NetPay and notify your own application.',
    icon: Radio,
  },
]

export function Landing() {
  const { user } = useAuth()
  const primaryHref = user ? '/dashboard' : '/login'

  return (
    <main className="min-h-screen overflow-hidden bg-[var(--bg)] text-[var(--text)]">
      <header className="relative z-10 mx-auto flex w-full max-w-7xl items-center justify-between px-5 py-5 sm:px-8 lg:px-10">
        <Link
          className="flex items-center gap-2.5 no-underline hover:no-underline"
          to="/"
          aria-label="NetPay home"
        >
          <span className="flex size-10 items-center justify-center rounded-xl bg-[var(--accent)] text-white shadow-sm">
            <Landmark size={21} strokeWidth={1.9} aria-hidden="true" />
          </span>
          <span className="text-lg font-bold tracking-tight text-[var(--text)]">
            NetPay
          </span>
        </Link>

        <nav className="hidden items-center gap-8 md:flex" aria-label="Main">
          <a className="text-sm font-medium text-[var(--muted)] hover:text-[var(--text)]" href="#features">
            Why NetPay
          </a>
          <a className="text-sm font-medium text-[var(--muted)] hover:text-[var(--text)]" href="#how-it-works">
            How it works
          </a>
          <a className="text-sm font-medium text-[var(--muted)] hover:text-[var(--text)]" href="#built-for">
            Built for business
          </a>
        </nav>

        <div className="flex items-center gap-2">
          <Link
            className="hidden rounded-xl px-4 py-2.5 text-sm font-semibold text-[var(--text)] transition hover:bg-[var(--panel-2)] sm:inline-flex"
            to={user ? '/dashboard' : '/login'}
          >
            {user ? 'Dashboard' : 'Sign in'}
          </Link>
          <Link
            className={`${button} bg-[var(--accent)] text-white shadow-sm hover:bg-[var(--accent-hover)]`}
            to={primaryHref}
          >
            {user ? 'Open dashboard' : 'Get started'}
            <ArrowRight size={16} aria-hidden="true" />
          </Link>
        </div>
      </header>

      <section className="relative mx-auto grid w-full max-w-7xl items-center gap-14 px-5 pb-20 pt-10 sm:px-8 sm:pb-28 sm:pt-16 lg:grid-cols-[1.02fr_0.98fr] lg:gap-8 lg:px-10 lg:pt-20">
        <div className="relative z-10 max-w-2xl">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-[var(--accent)]/20 bg-[var(--accent-soft)] px-3.5 py-1.5 text-xs font-semibold text-[var(--accent)]">
            <span className="size-1.5 rounded-full bg-[var(--accent)]" />
            M-Pesa collections, made clear
          </div>
          <h1 className="max-w-[13ch] text-5xl font-semibold leading-[1.04] tracking-[-0.055em] sm:text-6xl lg:text-[4.5rem]">
            Payments in.
            <span className="block text-[var(--accent)]">Clarity out.</span>
          </h1>
          <p className="mt-6 max-w-xl text-base leading-7 text-[var(--muted)] sm:text-lg sm:leading-8">
            Send M-Pesa payment requests, follow every result, and keep your
            business systems informed — all from one calm, clear workspace.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Link
              className={`${button} bg-[var(--accent)] text-white shadow-[var(--shadow)] hover:bg-[var(--accent-hover)]`}
              to={primaryHref}
            >
              {user ? 'Go to your dashboard' : 'Start collecting'}
              <ArrowRight size={17} aria-hidden="true" />
            </Link>
            <a
              className={`${button} border border-[var(--border)] bg-[var(--panel)] text-[var(--text)] hover:bg-[var(--panel-2)]`}
              href="#how-it-works"
            >
              See how it works
              <ChevronRight size={16} aria-hidden="true" />
            </a>
          </div>
          <div className="mt-8 flex flex-wrap items-center gap-x-5 gap-y-2 text-xs font-medium text-[var(--muted)]">
            <span className="inline-flex items-center gap-1.5">
              <ShieldCheck size={15} className="text-[var(--accent)]" aria-hidden="true" />
              Built for payment operations
            </span>
            <span className="inline-flex items-center gap-1.5">
              <LockKeyhole size={14} className="text-[var(--accent)]" aria-hidden="true" />
              NetHub sign-in
            </span>
          </div>
        </div>

        <div className="relative mx-auto w-full max-w-[580px] lg:ml-auto">
          <div className="absolute -inset-8 -z-10 rounded-full bg-[var(--accent)]/10 blur-3xl" />
          <div className="overflow-hidden rounded-3xl border border-[var(--border)] bg-[var(--panel)] shadow-[var(--shadow-hero)]">
            <div className="flex items-center justify-between border-b border-[var(--border)] px-5 py-4 sm:px-6">
              <div className="flex items-center gap-3">
                <span className="flex size-9 items-center justify-center rounded-xl bg-[var(--accent-soft)] text-[var(--accent)]">
                  <Landmark size={17} aria-hidden="true" />
                </span>
                <div>
                  <div className="text-sm font-semibold">Collections overview</div>
                  <div className="text-[11px] text-[var(--muted)]">A preview of your workspace</div>
                </div>
              </div>
              <span className="inline-flex items-center gap-1.5 rounded-full bg-[var(--accent-soft)] px-2.5 py-1 text-[10px] font-semibold text-[var(--accent)]">
                <span className="size-1.5 rounded-full bg-[var(--accent)]" />
                Ready
              </span>
            </div>

            <div className="p-5 sm:p-6">
              <div className="grid grid-cols-2 gap-3">
                <PreviewMetric label="Payment status" value="Easy to follow" icon={CircleCheck} />
                <PreviewMetric label="Connections" value="Shortcodes + apps" icon={Webhook} />
              </div>

              <div className="mt-5 rounded-2xl border border-[var(--border)] bg-[var(--bg)]/60 p-4 sm:p-5">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="text-xs font-medium text-[var(--muted)]">Example payment</div>
                    <div className="mt-1 text-2xl font-semibold tracking-tight">KES 2,500</div>
                  </div>
                  <span className="flex size-11 items-center justify-center rounded-2xl bg-[var(--accent-soft)] text-[var(--accent)]">
                    <CreditCard size={20} aria-hidden="true" />
                  </span>
                </div>
                <div className="mt-4 flex items-center justify-between border-t border-[var(--border)] pt-3 text-xs">
                  <span className="font-mono text-[var(--muted)]">Customer · 07•• ••• 428</span>
                  <span className="inline-flex items-center gap-1 rounded-full bg-[var(--accent-soft)] px-2.5 py-1 font-semibold text-[var(--accent)]">
                    <Check size={12} aria-hidden="true" />
                    Paid
                  </span>
                </div>
              </div>

              <div className="mt-5">
                <div className="mb-3 flex items-center justify-between">
                  <span className="text-xs font-semibold">A clear payment trail</span>
                  <span className="text-[10px] text-[var(--muted)]">From request to result</span>
                </div>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { label: 'Request sent', icon: CreditCard },
                    { label: 'Customer pays', icon: Check },
                    { label: 'App notified', icon: Bell },
                  ].map(({ label, icon: Icon }, index) => (
                    <div className="relative flex flex-col items-center gap-2 text-center" key={label}>
                      {index < 2 && (
                        <span className="absolute left-[calc(50%+19px)] top-4 h-px w-[calc(100%-24px)] bg-[var(--accent)]/25" />
                      )}
                      <span className="relative flex size-8 items-center justify-center rounded-full border border-[var(--accent)]/20 bg-[var(--accent-soft)] text-[var(--accent)]">
                        <Icon size={14} aria-hidden="true" />
                      </span>
                      <span className="text-[10px] leading-4 text-[var(--muted)]">{label}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2 border-t border-[var(--border)] bg-[var(--panel-2)]/60 px-5 py-3 text-[11px] text-[var(--muted)] sm:px-6">
              <Bell size={13} aria-hidden="true" />
              Payment outcomes can flow to your app
              <ArrowUpRight className="ml-auto" size={14} aria-hidden="true" />
            </div>
          </div>
          <div className="absolute -bottom-5 -left-3 hidden items-center gap-3 rounded-2xl border border-[var(--border)] bg-[var(--panel)] p-3.5 shadow-[var(--shadow)] sm:flex lg:-left-10">
            <span className="flex size-9 items-center justify-center rounded-xl bg-[var(--accent-soft)] text-[var(--accent)]">
              <Check size={17} aria-hidden="true" />
            </span>
            <span>
              <span className="block text-xs font-semibold">Every result has a place</span>
              <span className="mt-0.5 block text-[10px] text-[var(--muted)]">Status · history · ledger</span>
            </span>
          </div>
        </div>
      </section>

      <section id="features" className="border-y border-[var(--border)] bg-[var(--panel)]">
        <div className="mx-auto grid w-full max-w-7xl gap-10 px-5 py-16 sm:px-8 sm:py-20 lg:grid-cols-[0.8fr_1.2fr] lg:gap-16 lg:px-10">
          <div className="max-w-md">
            <p className="mb-3 text-xs font-bold uppercase tracking-[0.16em] text-[var(--accent)]">
              Less guesswork
            </p>
            <h2 className="text-3xl font-semibold leading-tight tracking-tight sm:text-4xl">
              The whole collection story, at a glance.
            </h2>
            <p className="mt-4 text-sm leading-6 text-[var(--muted)]">
              Payments are more than a prompt. NetPay brings the request,
              customer response, settlement record, and app notification into
              one place.
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-3">
            {highlights.map(({ icon: Icon, title, description }) => (
              <article
                className="rounded-2xl border border-[var(--border)] bg-[var(--bg)]/60 p-5"
                key={title}
              >
                <span className="flex size-10 items-center justify-center rounded-xl bg-[var(--accent-soft)] text-[var(--accent)]">
                  <Icon size={19} aria-hidden="true" />
                </span>
                <h3 className="mb-2 mt-5 text-sm font-semibold">{title}</h3>
                <p className="m-0 text-xs leading-5 text-[var(--muted)]">{description}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section id="how-it-works" className="mx-auto w-full max-w-7xl px-5 py-16 sm:px-8 sm:py-24 lg:px-10">
        <div className="mx-auto max-w-2xl text-center">
          <p className="mb-3 text-xs font-bold uppercase tracking-[0.16em] text-[var(--accent)]">
            Straightforward by design
          </p>
          <h2 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            From shortcode to settlement.
          </h2>
          <p className="mt-4 text-sm leading-6 text-[var(--muted)]">
            Get connected, send a prompt, and follow the result without jumping
            between tools.
          </p>
        </div>
        <div className="mt-10 grid gap-4 md:grid-cols-3">
          {steps.map(({ number, title, description, icon: Icon }) => (
            <article className="relative rounded-2xl border border-[var(--border)] bg-[var(--panel)] p-6 shadow-[var(--shadow-sm)]" key={number}>
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold tracking-widest text-[var(--accent)]">{number}</span>
                <span className="flex size-10 items-center justify-center rounded-xl bg-[var(--accent-soft)] text-[var(--accent)]">
                  <Icon size={18} aria-hidden="true" />
                </span>
              </div>
              <h3 className="mb-2 mt-6 text-base font-bold">{title}</h3>
              <p className="m-0 text-sm leading-6 text-[var(--muted)]">{description}</p>
            </article>
          ))}
        </div>
      </section>

      <section id="built-for" className="mx-auto w-full max-w-7xl px-5 pb-16 sm:px-8 sm:pb-24 lg:px-10">
        <div className="relative overflow-hidden rounded-3xl bg-[var(--accent)] px-6 py-10 text-white sm:px-10 sm:py-12">
          <div aria-hidden="true" className="pointer-events-none absolute -right-20 -top-36 size-80 rounded-full border border-white/10" />
          <div className="relative flex flex-col justify-between gap-7 md:flex-row md:items-center">
            <div className="max-w-2xl">
              <p className="mb-2 text-xs font-bold uppercase tracking-[0.16em] text-white/70">
                Ready when you are
              </p>
              <h2 className="m-0 text-2xl font-semibold tracking-tight sm:text-3xl">
                Make every payment easier to follow.
              </h2>
              <p className="mb-0 mt-3 text-sm leading-6 text-white/75">
                Sign in with NetHub and bring your collections into focus.
              </p>
            </div>
            <Link
              className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl bg-white px-5 py-3 text-sm font-semibold text-[var(--accent-hover)] shadow-sm transition hover:bg-white/90"
              to={primaryHref}
            >
              {user ? 'Open your dashboard' : 'Continue with NetHub'}
              <ArrowRight size={16} aria-hidden="true" />
            </Link>
          </div>
        </div>
      </section>

      <footer className="border-t border-[var(--border)] bg-[var(--panel)]">
        <div className="mx-auto flex w-full max-w-7xl flex-col gap-3 px-5 py-6 text-xs text-[var(--muted)] sm:flex-row sm:items-center sm:justify-between sm:px-8 lg:px-10">
          <Link className="font-semibold text-[var(--text)] no-underline hover:no-underline" to="/">
            NetPay
          </Link>
          <span>Payment collection and visibility for your business.</span>
          <Link className="inline-flex items-center gap-1 font-medium" to="/login">
            Sign in <ArrowRight size={13} aria-hidden="true" />
          </Link>
        </div>
      </footer>
    </main>
  )
}

function PreviewMetric({
  label,
  value,
  icon: Icon,
}: {
  label: string
  value: string
  icon: typeof CircleCheck
}) {
  return (
    <div className="rounded-2xl border border-[var(--border)] bg-[var(--panel)] p-3.5">
      <span className="flex size-8 items-center justify-center rounded-lg bg-[var(--accent-soft)] text-[var(--accent)]">
        <Icon size={16} aria-hidden="true" />
      </span>
      <div className="mt-3 text-[10px] text-[var(--muted)]">{label}</div>
      <div className="mt-1 text-xs font-semibold">{value}</div>
    </div>
  )
}
