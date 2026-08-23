import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api, ApiError, type Integration } from '../api/client'
import { StatusBadge } from '../components/StatusBadge'

export function IntegrationDetail() {
  const { id } = useParams()
  const [item, setItem] = useState<Integration | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [msg, setMsg] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function load() {
    try {
      const list = await api.get<Integration[]>('/v1/integrations')
      const found = list.find((x) => x.id === id)
      if (!found) setError('Integration not found')
      else setItem(found)
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Load failed')
    }
  }

  useEffect(() => { load() }, [id])

  async function registerUrls() {
    if (!item) return
    setBusy(true)
    setError(null)
    setMsg(null)
    try {
      const base = `https://gateway.nethub.co.ke/mpesa/cb/${item.public_id}`
      const res = await api.post<{ message?: string; ok?: boolean }>(`/v1/integrations/${item.id}/register-urls`, {
        confirmation_url: `${base}/confirmation`,
        validation_url: `${base}/validation`,
        response_type: 'Completed',
      })
      setMsg(res.message || 'Daraja URLs registered')
      await load()
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Register failed')
    } finally {
      setBusy(false)
    }
  }

  if (error && !item) return <div className="alert error" data-testid="integration-detail-page">{error}</div>
  if (!item) return <div data-testid="integration-detail-page">Loading…</div>

  return (
    <div data-testid="integration-detail-page">
      <div className="page-header">
        <div>
          <h1>Integration {item.public_id}</h1>
          <p>Shortcode {item.shortcode} · {item.type}</p>
        </div>
        <div className="btn-row">
          <StatusBadge value={item.environment} />
          <StatusBadge value={item.status} />
        </div>
      </div>
      {error && <div className="alert error">{error}</div>}
      {msg && <div className="alert ok">{msg}</div>}

      <div className="card">
        <h2>Daraja C2B URL register</h2>
        <p className="muted">Registers validation + confirmation URLs for this shortcode via the gateway.</p>
        <dl className="mono tiny">
          <div><dt className="muted">Confirmation</dt><dd>{item.confirmation_url || '—'}</dd></div>
          <div><dt className="muted">Validation</dt><dd>{item.validation_url || '—'}</dd></div>
          <div><dt className="muted">STK callback</dt><dd>{item.stk_callback_url || '—'}</dd></div>
        </dl>
        <button className="btn primary" type="button" onClick={registerUrls} disabled={busy}>
          {busy ? 'Registering…' : 'Register Daraja URLs'}
        </button>
      </div>
    </div>
  )
}
