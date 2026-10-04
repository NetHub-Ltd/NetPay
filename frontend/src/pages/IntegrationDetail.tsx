import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, ApiError, type Integration } from '../api/client'
import { StatusBadge } from '../components/StatusBadge'

type PublicConfig = {
  edge_public_base_url: string
  edge_callback_path_prefix?: string
}

function CopyField({ label, value }: { label: string; value: string }) {
  const [copied, setCopied] = useState(false)
  async function copy() {
    try {
      await navigator.clipboard.writeText(value)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1500)
    } catch {
      /* ignore */
    }
  }
  return (
    <div style={{ marginBottom: '0.75rem' }}>
      <div className="text-[var(--muted)] text-xs">{label}</div>
      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
        <code className="font-mono text-[0.85em] text-xs" style={{ wordBreak: 'break-all' }}>
          {value}
        </code>
        <button type="button" className="inline-flex items-center justify-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--panel)] px-3 py-2 text-sm font-medium text-[var(--text)] no-underline shadow-[var(--shadow)]" onClick={copy}>
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
    </div>
  )
}

export function IntegrationDetail() {
  const { id } = useParams()
  const [item, setItem] = useState<Integration | null>(null)
  const [edgeBase, setEdgeBase] = useState('https://gateway.nethub.co.ke')
  const [pathPrefix, setPathPrefix] = useState('/cb')
  const [error, setError] = useState<string | null>(null)
  const [msg, setMsg] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [connectedOnce, setConnectedOnce] = useState(false)

  const load = useCallback(async () => {
    if (!id) return
    try {
      const found = await api.get<Integration>(`/v1/integrations/${id}`)
      setItem(found)
      setError(null)
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Could not load shortcode')
      setItem(null)
    }
  }, [id])

  useEffect(() => {
    void Promise.resolve().then(load)
    api
      .get<PublicConfig>('/v1/system/public-config')
      .then((c) => {
        if (c.edge_public_base_url) setEdgeBase(c.edge_public_base_url)
        if (c.edge_callback_path_prefix) setPathPrefix(c.edge_callback_path_prefix)
      })
      .catch(() => {})
  }, [id, load])

  function buildUrls(publicId: string) {
    const prefix = pathPrefix.startsWith('/') ? pathPrefix : `/${pathPrefix}`
    const root = `${edgeBase.replace(/\/$/, '')}${prefix.replace(/\/$/, '')}/${publicId}`
    return {
      stk: `${root}/stk`,
      confirmation: `${root}/confirmation`,
      validation: `${root}/validation`,
    }
  }

  async function connectPayments() {
    if (!item) return
    const confirmed = window.confirm(
      `Connect shortcode ${item.shortcode} so payment results can reach NetPay automatically?\n\n` +
        `You only need to do this once per shortcode. You can still copy the technical links below if your provider portal needs them.`,
    )
    if (!confirmed) return

    setBusy(true)
    setError(null)
    setMsg(null)
    try {
      const urls = buildUrls(item.public_id)
      const res = await api.post<{ message?: string; detail?: string }>(
        `/v1/integrations/${item.id}/register-urls`,
        {
          confirmation_url: urls.confirmation,
          validation_url: urls.validation,
          response_type: 'Completed',
        },
      )
      setConnectedOnce(true)
      setMsg(
        res.message ||
          `Shortcode ${item.shortcode} is connected. Payment results for this number can reach NetPay. Links below stay available if you need them later.`,
      )
      await load()
    } catch (e) {
      const detail = e instanceof ApiError ? e.detail : 'Could not connect this shortcode'
      setError(
        `${detail}. You can still copy the links below and paste them in your provider portal, then try again.`,
      )
    } finally {
      setBusy(false)
    }
  }

  if (error && !item) {
    return (
      <div data-testid="integration-detail-page">
        <div className="mb-4 rounded-lg border px-4 py-3 text-sm border-[var(--danger)]/30 bg-[var(--danger)]/10 text-[var(--danger)]">{error}</div>
        <Link to="/integrations">← All paybills &amp; tills</Link>
      </div>
    )
  }
  if (!item) return <div data-testid="integration-detail-page">Loading…</div>

  const urls = buildUrls(item.public_id)

  return (
    <div data-testid="integration-detail-page">
      <p className="text-[var(--muted)] text-xs">
        <Link to="/integrations">← All paybills &amp; tills</Link>
      </p>
      <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1>Shortcode {item.shortcode}</h1>
          <p>
            {item.type === 'till' ? 'Till' : 'Paybill'} · {' '}
            {item.environment === 'production' ? 'Live' : 'Test'}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <StatusBadge value={item.environment} />
          <StatusBadge value={item.status} />
        </div>
      </div>
      {error && <div className="mb-4 rounded-lg border px-4 py-3 text-sm border-[var(--danger)]/30 bg-[var(--danger)]/10 text-[var(--danger)]">{error}</div>}
      {msg && <div className="mb-4 rounded-lg border px-4 py-3 text-sm border-[var(--accent-2)]/30 bg-[var(--accent-2)]/10 text-[var(--text)]">{msg}</div>}

      <div className="mb-4 rounded-[var(--radius)] border border-[var(--border)] bg-[var(--panel)] p-4 shadow-[var(--shadow)]">
        <h2>Setup for this shortcode</h2>
        <ol style={{ margin: 0, paddingLeft: '1.25rem' }}>
          <li>
            <strong>Shortcode saved</strong> — done
          </li>
          <li>
            <strong>Connect payment updates</strong>
            {connectedOnce ? ' — done' : ' — use the button below'}
          </li>
          <li>
            <strong>Notify your app</strong> — <Link to="/webhooks">Payment notifications</Link>
          </li>
        </ol>
      </div>

      <div className="mb-4 rounded-[var(--radius)] border border-[var(--border)] bg-[var(--panel)] p-4 shadow-[var(--shadow)]">
        <h2>Connect payment updates</h2>
        <p style={{ marginTop: 0 }}>
          One click tells the network where to send results for this shortcode so NetPay can mark payments Paid or
          Failed. You'll be asked to confirm before anything is sent.
        </p>
        <button className="inline-flex items-center justify-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--panel)] px-3 py-2 text-sm font-medium text-[var(--text)] no-underline shadow-[var(--shadow)]" type="button" onClick={connectPayments} disabled={busy}>
          {busy ? 'Connecting…' : 'Connect this shortcode'}
        </button>
      </div>

      <div className="mb-4 rounded-[var(--radius)] border border-[var(--border)] bg-[var(--panel)] p-4 shadow-[var(--shadow)]">
        <h2>Links (if you need them)</h2>
        <p className="text-[var(--muted)]" style={{ marginTop: 0 }}>
          Keep these for your records or if a portal asks you to paste addresses manually. You can return here anytime
          from <Link to="/integrations">Paybills &amp; tills</Link> → Open.
        </p>
        <CopyField label="Phone prompt results" value={urls.stk} />
        <CopyField label="Paybill / till payment notice" value={urls.confirmation} />
        <CopyField label="Paybill / till pre-check" value={urls.validation} />
      </div>

      <div className="mb-4 rounded-[var(--radius)] border border-[var(--border)] bg-[var(--panel)] p-4 shadow-[var(--shadow)]">
        <h2>Advanced</h2>
        <div className="text-[var(--muted)] text-xs">Routing id (support)</div>
        <code className="font-mono text-[0.85em]">{item.public_id}</code>
      </div>
    </div>
  )
}
