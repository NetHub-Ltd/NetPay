import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, ApiError, type Integration } from '../api/client'
import { StatusBadge } from '../components/StatusBadge'

type PublicConfig = { edge_public_base_url: string }

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
      <div className="muted tiny">{label}</div>
      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
        <code className="mono tiny" style={{ wordBreak: 'break-all' }}>
          {value}
        </code>
        <button type="button" className="btn" onClick={copy}>
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
  const [error, setError] = useState<string | null>(null)
  const [msg, setMsg] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [registeredOnce, setRegisteredOnce] = useState(false)

  async function load() {
    if (!id) return
    try {
      const found = await api.get<Integration>(`/v1/integrations/${id}`)
      setItem(found)
      setError(null)
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Could not load shortcode')
      setItem(null)
    }
  }

  useEffect(() => {
    load()
    api
      .get<PublicConfig>('/v1/system/public-config')
      .then((c) => setEdgeBase(c.edge_public_base_url || edgeBase))
      .catch(() => {})
  }, [id])

  async function registerUrls() {
    if (!item) return
    setBusy(true)
    setError(null)
    setMsg(null)
    try {
      const base = `${edgeBase.replace(/\/$/, '')}/mpesa/cb/${item.public_id}`
      const res = await api.post<{ message?: string }>(`/v1/integrations/${item.id}/register-urls`, {
        confirmation_url: `${base}/confirmation`,
        validation_url: `${base}/validation`,
        response_type: 'Completed',
      })
      setRegisteredOnce(true)
      setMsg(
        res.message ||
          'Safaricom was told to send paybill/till notices to NetHub. You can still copy the URLs below for the Daraja portal.',
      )
      await load()
    } catch (e) {
      setError(
        e instanceof ApiError
          ? e.detail
          : 'Could not register with Safaricom. You can still copy the URLs and set them in the Daraja portal.',
      )
    } finally {
      setBusy(false)
    }
  }

  if (error && !item) {
    return (
      <div data-testid="integration-detail-page">
        <div className="alert error">{error}</div>
        <Link to="/integrations">← Paybills &amp; tills</Link>
      </div>
    )
  }
  if (!item) return <div data-testid="integration-detail-page">Loading…</div>

  const base = `${edgeBase.replace(/\/$/, '')}/mpesa/cb/${item.public_id}`
  const urls = {
    stk: `${base}/stk`,
    confirmation: `${base}/confirmation`,
    validation: `${base}/validation`,
  }

  return (
    <div data-testid="integration-detail-page">
      <p className="muted tiny">
        <Link to="/integrations">← Paybills &amp; tills</Link>
      </p>
      <div className="page-header">
        <div>
          <h1>
            Shortcode {item.shortcode}
          </h1>
          <p>
            {item.type === 'till' ? 'Till' : 'Paybill'} ·{' '}
            {item.environment === 'production' ? 'Live' : 'Test'}
          </p>
        </div>
        <div className="btn-row" style={{ display: 'flex', gap: '0.5rem' }}>
          <StatusBadge value={item.environment} />
          <StatusBadge value={item.status} />
        </div>
      </div>
      {error && <div className="alert error">{error}</div>}
      {msg && <div className="alert ok">{msg}</div>}

      <div className="card">
        <h2>Setup for this shortcode</h2>
        <ol style={{ margin: 0, paddingLeft: '1.25rem' }}>
          <li>
            <strong>Shortcode saved</strong> — done
          </li>
          <li>
            <strong>Connect M-Pesa</strong>
            {registeredOnce ? ' — register attempted' : ' — use the section below'}
          </li>
          <li>
            <strong>Notify your app</strong> — <Link to="/webhooks">Payment notifications</Link>
          </li>
        </ol>
      </div>

      <div className="card">
        <h2>M-Pesa → NetPay</h2>
        <p className="muted" style={{ marginTop: 0 }}>
          These are the addresses Safaricom should use so results reach NetPay via the NetHub edge. This is{' '}
          <em>not</em> the same as notifying your own app (that’s Payment notifications).
        </p>
        <CopyField label="STK (customer phone prompt results)" value={urls.stk} />
        <CopyField label="Confirmation (paybill/till payment notice)" value={urls.confirmation} />
        <CopyField label="Validation (paybill/till check before accept)" value={urls.validation} />
        <p className="muted tiny">
          STK payments use the STK URL automatically when you request payment in NetPay. Paybill/till (C2B) usually
          needs <strong>Register URLs with Safaricom</strong> once per shortcode (or set the same URLs in the Daraja
          portal).
        </p>
        <button className="btn primary" type="button" disabled={busy} onClick={registerUrls}>
          {busy ? 'Registering…' : 'Register URLs with Safaricom'}
        </button>
      </div>

      <div className="card">
        <h2>Advanced</h2>
        <div className="muted tiny">NetHub routing id (for support)</div>
        <code className="mono">{item.public_id}</code>
      </div>
    </div>
  )
}
