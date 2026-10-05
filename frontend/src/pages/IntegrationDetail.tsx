import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, ApiError, type Integration } from '../api/client'
import { StatusBadge } from '../components/StatusBadge'
import { PageHeader } from '../components/PageHeader'
import { Button, PageLoader } from '../components/primitives'
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
  const [lastOauth, setLastOauth] = useState<{
    token_redacted?: string
    expires_in?: number
    environment?: string
  } | null>(null)

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
      setMsg(
        res.message ||
          `Shortcode ${item.shortcode} is connected. Payment results for this number can reach NetPay.`,
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

  async function disconnectPayments() {
    if (!item) return
    const confirmed = window.confirm(
      `Disconnect shortcode ${item.shortcode} in NetPay?\n\n` +
        `This clears NetPay's "connected" state. Daraja has no public unregister API — ` +
        `in sandbox you can re-register; in production Safaricom may still use previous URLs until they clear them.`,
    )
    if (!confirmed) return
    setBusy(true)
    setError(null)
    setMsg(null)
    try {
      const res = await api.post<{ message?: string }>(`/v1/integrations/${item.id}/disconnect`, {})
      setLastOauth(null)
      setMsg(res.message || 'Disconnected in NetPay.')
      await load()
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Could not disconnect')
    } finally {
      setBusy(false)
    }
  }

  if (error && !item) {
    return (
      <div data-testid="integration-detail-page">
        <div className={errorAlert} role="alert">{error}</div>
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
      {error && <div className={errorAlert} role="alert">{error}</div>}
      {msg && <div className={successAlert} role="status">{msg}</div>}

      <div className={card}>
        <h2 className="mb-3 text-base font-semibold">Setup for this shortcode</h2>
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
        <h2 className="mb-2 text-base font-semibold">Connect payment updates</h2>
        <p className="mb-4 text-sm text-[var(--muted)]">
          Registers Confirmation and Validation URLs with Daraja (C2B registerurl) so paybill/till results
          reach NetPay. You will be asked to confirm. Production URLs must be HTTPS and publicly reachable.
        </p>
        <div className="flex flex-wrap gap-2">
          <Button type="button" onClick={() => void connectPayments()} loading={busy}>
            {busy
              ? 'Working…'
              : item.connected || item.status === 'connected'
                ? 'Re-register with Daraja'
                : 'Connect M-Pesa'}
          </Button>
          {(item.connected || item.status === 'connected') && (
            <Button
              type="button"
              variant="secondary"
              disabled={busy}
              onClick={() => void disconnectPayments()}
            >
              Disconnect in NetPay
            </Button>
          )}
        </div>
        {lastOauth && (
          <p className="mb-0 mt-3 text-xs text-[var(--muted)]">
            Last OAuth check: token {lastOauth.token_redacted}
            {lastOauth.expires_in != null && lastOauth.expires_in > 0
              ? ` · expires_in ${lastOauth.expires_in}s`
              : ''}
            {lastOauth.environment ? ` · ${lastOauth.environment}` : ''}
          </p>
        )}
      </div>

      <div className={card}>
        <h2 className="mb-2 text-base font-semibold">Links (if you need them)</h2>
        <p className="mb-4 text-sm text-[var(--muted)]">
          Keep these for your records or if a portal asks you to paste addresses manually. You can return here anytime
          from <Link to="/integrations">Paybills &amp; tills</Link> → Open.
        </p>
        <CopyField label="Phone prompt results" value={urls.stk} />
        <CopyField label="Paybill / till payment notice" value={urls.confirmation} />
        <CopyField label="Paybill / till pre-check" value={urls.validation} />
      </div>

      <div className={card}>
        <h2 className="mb-3 text-base font-semibold">Advanced</h2>
        <div className="text-[var(--muted)] text-xs">Routing id (support)</div>
        <code className="font-mono text-[0.85em]">{item.public_id}</code>
      </div>
    </div>
  )
}
