import { useEffect, useState } from 'react'
import { api, type Health as HealthT } from '../api/client'
import { StatusBadge } from '../components/StatusBadge'

export function Health() {
  const [data, setData] = useState<HealthT | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.get<HealthT>('/health')
      .then(setData)
      .catch((e) => setError(e.message || 'Failed to load health'))
  }, [])

  return (
    <div data-testid="health-page">
      <div className="page-header">
        <div>
          <h1>System health</h1>
          <p>Startup probes: database, Redis, admin bootstrap</p>
        </div>
        {data && <StatusBadge value={data.status} />}
      </div>
      {error && <div className="alert error">{error}</div>}
      {data && (
        <div className="grid-3">
          <div className="stat"><div className="label">Database</div><div className="value">{data.database ? 'OK' : 'Down'}</div></div>
          <div className="stat"><div className="label">Redis</div><div className="value" style={{ fontSize: '1rem' }}>{data.redis}</div></div>
          <div className="stat"><div className="label">Admin ready</div><div className="value">{data.admin_ready ? 'Yes' : 'No'}</div></div>
          <div className="stat"><div className="label">Environment</div><div className="value" style={{ fontSize: '1rem' }}>{data.environment}</div></div>
          <div className="stat"><div className="label">Version</div><div className="value" style={{ fontSize: '1rem' }}>{data.version}</div></div>
          <div className="stat"><div className="label">Overall</div><div className="value"><StatusBadge value={data.status} /></div></div>
        </div>
      )}
    </div>
  )
}
