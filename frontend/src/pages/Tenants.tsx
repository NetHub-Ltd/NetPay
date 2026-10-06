import { Navigate } from 'react-router-dom'

/** Business CRUD lives on the choose/switch screen — keep deep links working. */
export function Tenants() {
  return <Navigate to="/select-business?switch=1" replace />
}
