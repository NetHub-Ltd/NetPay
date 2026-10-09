/**
 * Living reference for global theme tokens (styles.css is source of truth).
 */
import { useState } from 'react'
import { Bell, Check, CreditCard, KeyRound, Landmark } from 'lucide-react'
import { PageHeader } from '../components/PageHeader'
import { Button, ConfirmModal, Input, Modal } from '../components/primitives'
import { EmptyState } from '../components/EmptyState'
import { StatusBadge } from '../components/StatusBadge'
import { emitNotification } from '../hooks/liveEvents'

const section =
  'mb-6 rounded-2xl border border-[var(--border)] bg-[var(--panel)] p-5 shadow-[var(--shadow-sm)]'
const label =
  'mb-2 text-[0.6875rem] font-bold uppercase tracking-wider text-[var(--muted)]'
const h1 =
  'mt-0 mb-2 text-[clamp(1.5rem,1.25rem+1vw,1.875rem)] font-extrabold leading-tight tracking-tight text-[var(--text)]'
const h2 =
  'mt-0 mb-2 text-[clamp(1.2rem,1.1rem+0.5vw,1.375rem)] font-bold leading-snug tracking-tight text-[var(--text)]'
const h3 = 'mt-0 mb-3 text-[1.05rem] font-bold leading-snug tracking-tight text-[var(--text)]'
const body = 'm-0 text-[0.9375rem] font-semibold leading-relaxed text-[var(--text)]'
const muted = 'm-0 text-sm font-medium leading-relaxed text-[var(--muted)]'

export function ThemeLab() {
  const [modalOpen, setModalOpen] = useState(false)
  const [confirmOpen, setConfirmOpen] = useState(false)

  return (
    <div data-testid="theme-lab-page">
      <PageHeader
        title="Theme lab"
        description="Living reference for global theme tokens, type scale, and notification patterns."
      />

      <div className={`${section} border-[var(--accent)]/30 bg-[var(--accent-soft)]`}>
        <p className={`${body} text-sm`}>
          This page uses the global theme tokens from styles.css (source of truth).
        </p>
        <ul className="mb-0 mt-2 list-disc pl-5 text-sm font-semibold text-[var(--text)]">
          <li>Body text is darker green (primary family), not pure gray-black</li>
          <li>Headings 700–800; body 600; muted 500 and darker for readability</li>
          <li>Canvas gray + white cards with border and soft lift shadow</li>
          <li>No sticky undismissable body banners — use toast / modal instead</li>
        </ul>
      </div>

      <section className={section}>
        <div className={label}>Typography</div>
        <h1 className={h1}>Heading 1 — Shortcode 174379</h1>
        <h2 className={h2}>Heading 2 — Connect payment updates</h2>
        <h3 className={h3}>Heading 3 — Setup for this shortcode</h3>
        <p className={`${body} mb-2`}>
          Body — Main operator copy. Connect this shortcode so paybill and till results reach NetPay.
          Production URLs must be HTTPS and publicly reachable.
        </p>
        <p className={`${muted} mb-2`}>
          Muted — Secondary hints and meta. Path check verifies network login without depending on
          registration uptime.
        </p>
        <p className={`${label} mb-1`}>Overline / section label</p>
        <code className="font-mono text-xs font-medium text-[var(--text)]">
          Mono — cli_ab12cd · gw_public_id · KES 1,250.00
        </code>
      </section>

      <section className={section}>
        <div className={label}>Layered surface</div>
        <div className="rounded-xl bg-[var(--bg)] p-4">
          <p className={`${muted} mb-3 text-sm`}>Canvas (page background)</p>
          <div className="rounded-xl border border-[var(--border)] bg-[var(--panel)] p-4 shadow-[var(--shadow)]">
            <p className={`${h3} mb-1`}>Card on canvas</p>
            <p className={`${body} mb-3 text-sm`}>
              White panel, border, soft shadow — primary content lives here.
            </p>
            <div className="rounded-lg border border-[var(--border)] bg-[var(--panel-2)] p-3">
              <p className={`${muted} m-0 text-sm`}>Nested well (panel-2) for secondary blocks</p>
            </div>
          </div>
        </div>
      </section>

      <section className={section}>
        <div className={label}>Buttons</div>
        <div className="flex flex-wrap gap-2">
          <Button>Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="danger">Danger</Button>
          <Button size="sm">Small</Button>
          <Button loading>Loading</Button>
          <Button disabled>Disabled</Button>
        </div>
      </section>

      <section className={section}>
        <div className={label}>Inputs & badges</div>
        <div className="mb-4 max-w-sm">
          <Input label="Shortcode name" placeholder="Paybill - Test" defaultValue="Paybill - Test" />
        </div>
        <div className="flex flex-wrap gap-2">
          <StatusBadge value="connected" />
          <StatusBadge value="pending_setup" />
          <StatusBadge value="sandbox" />
          <StatusBadge value="failed" />
          <StatusBadge value="succeeded" />
        </div>
      </section>

      <section className={section}>
        <div className={label}>Notifications (proposed model)</div>
        <p className={`${body} mb-3 text-sm`}>
          Prefer toast or modal — not permanent page banners. Try the controls:
        </p>
        <div className="mb-4 flex flex-wrap gap-2">
          <Button
            variant="secondary"
            onClick={() =>
              emitNotification({
                id: `lab-ok-${Date.now()}`,
                title: 'Shortcode connected',
                body: 'Payment results for this number can reach NetPay.',
                level: 'success',
              })
            }
          >
            Toast success
          </Button>
          <Button
            variant="secondary"
            onClick={() =>
              emitNotification({
                id: `lab-err-${Date.now()}`,
                title: 'Couldn’t connect',
                body: 'The payment network may be temporarily unavailable. Try again in a few minutes.',
                level: 'error',
              })
            }
          >
            Toast error
          </Button>
          <Button variant="secondary" onClick={() => setModalOpen(true)}>
            Info modal
          </Button>
          <Button variant="secondary" onClick={() => setConfirmOpen(true)}>
            Confirm modal
          </Button>
        </div>
        <p className={`${muted} text-sm`}>
          Toasts appear top-right (existing ToastHost). Use the bell for history. Avoid sticky green/red
          strips that stay in the page body until navigation.
        </p>
      </section>

      <section className={section}>
        <div className={label}>Empty state & list row</div>
        <EmptyState
          icon={<Landmark size={22} />}
          title="No shortcodes yet"
          hint="Add a paybill or till. Credentials are verified before save."
          action={<Button size="sm">Add shortcode</Button>}
        />
        <ul className="m-0 mt-4 list-none space-y-2 p-0">
          <li className="rounded-xl border border-[var(--border)] bg-[var(--panel)] px-4 py-3 shadow-[var(--shadow-sm)]">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <div className="font-bold text-[var(--text)]">Shortcode 174379</div>
                <div className="text-sm font-medium text-[var(--muted)]">Paybill · Test</div>
              </div>
              <div className="flex gap-2">
                <StatusBadge value="sandbox" />
                <StatusBadge value="pending_setup" />
              </div>
            </div>
          </li>
        </ul>
      </section>

      <section className={section}>
        <div className={label}>Icon affordances</div>
        <div className="flex gap-4 text-[var(--accent)]">
          <CreditCard size={22} />
          <KeyRound size={22} />
          <Bell size={22} />
          <Check size={22} />
        </div>
      </section>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="Path check finished">
        <p className={`${body} text-sm`}>
          NetPay-side checks look healthy. Connecting to the payment network can still fail when the
          sandbox is down — try again later if needed.
        </p>
        <div className="mt-4 flex justify-end">
          <Button onClick={() => setModalOpen(false)}>Got it</Button>
        </div>
      </Modal>

      <ConfirmModal
        open={confirmOpen}
        title="Connect this shortcode?"
        body="Connect 174379 so payment results reach NetPay automatically. You only need to do this once per shortcode."
        confirmLabel="Connect"
        onCancel={() => setConfirmOpen(false)}
        onConfirm={() => {
          setConfirmOpen(false)
          emitNotification({
            id: `lab-confirm-${Date.now()}`,
            title: 'Connected',
            body: 'Shortcode 174379 is ready for payment updates.',
            level: 'success',
          })
        }}
      />
    </div>
  )
}
