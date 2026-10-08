import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, ApiError, type Integration } from '../api/client'
import { StatusBadge } from '../components/StatusBadge'
import { PageHeader } from '../components/PageHeader'
import { Button, ConfirmModal, PageLoader } from '../components/primitives'
import { emitNotification } from '../hooks/liveEvents'
import { button, card, errorAlert, successAlert } from '../components/ui'

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
    <div className="mb-3">
      <div className="text-[var(--muted)] text-xs">{label}</div>
      <div className="flex flex-wrap items-center gap-2">
        <code className="break-all font-mono text-xs">
          {value}
        </code>
        <button type="button" className={button} onClick={copy}>
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
  const [pathCheck, setPathCheck] = useState<{
    ok?: boolean
    message?: string
    steps?: Array<Record<string, unknown>>
  } | null>(null)
  const [lastOauth, setLastOauth] = useState<{
    token_redacted?: string
    expires_in?: number
    environment?: string
  } | null>(null)
  const [confirmKind, setConfirmKind] = useState<'connect' | 'disconnect' | null>(null)

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

  async function doConnectPayments() {
    if (!item) return
    setBusy(true)
    setError(null)
    setMsg(null)
    setConfirmKind(null)
    try {
      const urls = buildUrls(item.public_id)
      const res = await api.post<{
        message?: string
        detail?: string
        oauth?: { token_redacted?: string; expires_in?: number; environment?: string }
      }>(`/v1/integrations/${item.id}/register-urls`, {
        confirmation_url: urls.confirmation,
        validation_url: urls.validation,
        response_type: 'Completed',
      })
      if (res.oauth) setLastOauth(res.oauth)
      const success =
        res.message ||
        `Shortcode ${item.shortcode} is connected. Payment results for this number can reach NetPay.`
      setMsg(success)
      emitNotification({
        id: `connect-${item.id}-${Date.now()}`,
        title: 'Shortcode connected',
        body: success,
        level: 'success',
        href: `/integrations/${item.id}`,
      })
      await load()
    } catch (e) {
      const detail = e instanceof ApiError ? e.detail : 'Could not connect this shortcode'
      setError(
        `${detail} You can still copy the links below and register them in your provider portal if needed.`,
      )
    } finally {
      setBusy(false)
    }
  }

  async function doDisconnectPayments() {
    if (!item) return
    setBusy(true)
    setError(null)
    setMsg(null)
    setConfirmKind(null)
    try {
      const res = await api.post<{ message?: string }>(`/v1/integrations/${item.id}/disconnect`, {})
      setLastOauth(null)
      const success = res.message || 'Disconnected in NetPay.'
      setMsg(success)
      emitNotification({
        id: `disconnect-${item.id}-${Date.now()}`,
        title: 'Shortcode disconnected',
        body: success,
        level: 'info',
        href: `/integrations/${item.id}`,
      })
      await load()
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Could not disconnect')
    } finally {
      setBusy(false)
    }
  }

  async function runPathCheck() {
    if (!item) return
    setBusy(true)
    setError(null)
    setMsg(null)
    setPathCheck(null)
    try {
      const res = await api.post<{
        ok: boolean
        message?: string
        steps?: Array<Record<string, unknown>>
      }>(`/v1/integrations/${item.id}/path-check`, {})
      setPathCheck(res)
      const pathMsg = res.message || (res.ok ? 'Path check finished.' : 'Path check found issues.')
      setMsg(pathMsg)
      emitNotification({
        id: `path-check-${item.id}-${Date.now()}`,
        title: res.ok ? 'Path check OK' : 'Path check found issues',
        body: pathMsg,
        level: res.ok ? 'success' : 'error',
        href: `/integrations/${item.id}`,
      })
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Path check failed')
    } finally {
      setBusy(false)
    }
  }

  if (error && !item) {
    return (
      <div data-testid="integration-detail-page">
        <div className={errorAlert} role="alert">
          <div className="flex items-start justify-between gap-3">
            <span>{error}</span>
            <button type="button" className="shrink-0 text-xs font-bold uppercase tracking-wide text-[var(--danger)] underline" onClick={() => setError(null)}>Dismiss</button>
          </div>
        </div>
        <Link to="/integrations">← All paybills &amp; tills</Link>
      </div>
    )
  }
  if (!item) return <div data-testid="integration-detail-page"><PageLoader label="Loading shortcode…" /></div>

  const urls = buildUrls(item.public_id)

  return (
    <div data-testid="integration-detail-page">
      <p className="mb-3 text-xs text-[var(--muted)]">
        <Link to="/integrations">← All paybills &amp; tills</Link>
      </p>
      <PageHeader
        title={`Shortcode ${item.shortcode}`}
        description={`${item.type === 'till' ? 'Till' : 'Paybill'} · ${
          item.environment === 'production' ? 'Live' : 'Test'
        }`}
        actions={
          <div className="flex gap-2">
            <StatusBadge value={item.environment} />
            <StatusBadge value={item.status} />
          </div>
        }
      />
      {error && (
        <div className={errorAlert} role="alert">
          <div className="flex items-start justify-between gap-3">
            <span>{error}</span>
            <button
              type="button"
              className="shrink-0 text-xs font-bold uppercase tracking-wide text-[var(--danger)] underline"
              onClick={() => setError(null)}
            >
              Dismiss
            </button>
          </div>
        </div>
      )}
      {msg && (
        <div className={successAlert} role="status">
          <div className="flex items-start justify-between gap-3">
            <span>{msg}</span>
            <button
              type="button"
              className="shrink-0 text-xs font-bold uppercase tracking-wide text-[var(--muted)] underline"
              onClick={() => setMsg(null)}
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      <div className={card}>
        <h2 className="mb-3 text-base font-bold">Setup for this shortcode</h2>
        <ol className="list-decimal space-y-2 pl-5 text-sm">
          <li>
            <strong>Shortcode saved</strong> — done
          </li>
          <li>
            <strong>Connect payment updates</strong>
            {item.connected || item.status === 'connected' ? ' — done' : ' — use the button below'}
          </li>
          <li>
            <strong>Notify your app</strong> — <Link to="/webhooks">Payment notifications</Link>
          </li>
        </ol>
      </div>

      <div className={card}>
        <h2 className="mb-2 text-base font-bold">Connect payment updates</h2>
        <p className="mb-4 text-sm text-[var(--muted)]">
          Connects this shortcode so paybill and till results
          reach NetPay. You will be asked to confirm. Production URLs must be HTTPS and publicly reachable.
        </p>
        <div className="flex flex-wrap gap-2">
          <Button type="button" onClick={() => setConfirmKind('connect')} loading={busy}>
            {busy
              ? 'Working…'
              : item.connected || item.status === 'connected'
                ? 'Reconnect to M-Pesa'
                : 'Connect M-Pesa'}
          </Button>
          {(item.connected || item.status === 'connected') && (
            <Button
              type="button"
              variant="secondary"
              disabled={busy}
              onClick={() => setConfirmKind('disconnect')}
            >
              Disconnect in NetPay
            </Button>
          )}
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          <Button type="button" variant="secondary" disabled={busy} onClick={() => void runPathCheck()}>
            Run path check
          </Button>
        </div>
        <p className="mb-0 mt-2 text-xs text-[var(--muted)]">
          Path check verifies network login, callback URLs, edge reachability, and sends a live toast — without depending on M-Pesa registration uptime.
        </p>
        {pathCheck && (
          <div className="mt-3 space-y-2 rounded-xl border border-[var(--border)] bg-[var(--panel-2)] p-3 text-xs">
            <div className="font-semibold">
              {pathCheck.ok ? 'Checks look healthy' : 'Issues found'} — {pathCheck.message}
            </div>
            {(pathCheck.steps || []).map((s: Record<string, unknown>) => (
              <div key={String(s.id)} className="border-t border-[var(--border)] pt-2">
                <span className={s.ok ? 'text-[var(--accent)]' : 'text-[var(--danger)]'}>{s.ok ? '✓' : '✗'}</span>{' '}
                <strong>{String(s.label)}</strong>
                {s.source ? <span className="text-[var(--muted)]"> · {String(s.source)}</span> : null}
                {s.error ? <div className="text-[var(--danger)]">{String(s.error)}</div> : null}
                {s.hint ? <div className="text-[var(--muted)]">{String(s.hint)}</div> : null}
                {s.token_redacted ? (
                  <div className="text-[var(--muted)]">
                    token {String(s.token_redacted)}
                    {s.expires_in != null && Number(s.expires_in) > 0 ? ` · expires_in ${String(s.expires_in)}s` : ''}
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        )}
        {lastOauth && (

          <p className="mb-0 mt-3 text-xs text-[var(--muted)]">
            Last network login check: token {lastOauth.token_redacted}
            {lastOauth.expires_in != null && lastOauth.expires_in > 0
              ? ` · expires_in ${lastOauth.expires_in}s`
              : ''}
            {lastOauth.environment ? ` · ${lastOauth.environment}` : ''}
          </p>
        )}
      </div>

      <div className={card}>
        <h2 className="mb-2 text-base font-bold">Links (if you need them)</h2>
        <p className="mb-4 text-sm text-[var(--muted)]">
          Keep these for your records or if a portal asks you to paste addresses manually. You can return here anytime
          from <Link to="/integrations">Paybills &amp; tills</Link> → Open.
        </p>
        <CopyField label="Phone prompt results" value={urls.stk} />
        <CopyField label="Paybill / till payment notice" value={urls.confirmation} />
        <CopyField label="Paybill / till pre-check" value={urls.validation} />
      </div>

      <div className={card}>
        <h2 className="mb-3 text-base font-bold">Advanced</h2>
        <div className="text-[var(--muted)] text-xs">Routing id (support)</div>
        <code className="font-mono text-[0.85em]">{item.public_id}</code>
      </div>

      <ConfirmModal
        open={confirmKind === 'connect'}
        title="Connect this shortcode?"
        body={
          item
            ? `Connect ${item.shortcode} so payment results reach NetPay automatically. You only need to do this once per shortcode. You can still copy the technical links below if your provider portal needs them.`
            : ''
        }
        confirmLabel="Connect"
        busy={busy}
        onCancel={() => !busy && setConfirmKind(null)}
        onConfirm={() => void doConnectPayments()}
      />
      <ConfirmModal
        open={confirmKind === 'disconnect'}
        title="Disconnect this shortcode?"
        body={
          item
            ? `Disconnect ${item.shortcode} in NetPay? This clears the connected state here. You can reconnect later. In live mode the network may keep old callback URLs until they are updated.`
            : ''
        }
        confirmLabel="Disconnect"
        danger
        busy={busy}
        onCancel={() => !busy && setConfirmKind(null)}
        onConfirm={() => void doDisconnectPayments()}
      />
    </div>
  )
}
