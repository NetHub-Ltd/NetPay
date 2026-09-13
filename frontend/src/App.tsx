import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './auth/AuthContext'
import { Layout } from './components/Layout'
import { Login } from './pages/Login'
import { Health } from './pages/Health'
import { Home } from './pages/Home'
import { Tenants } from './pages/Tenants'
import { TenantDetail } from './pages/TenantDetail'
import { Integrations } from './pages/Integrations'
import { IntegrationDetail } from './pages/IntegrationDetail'
import { Webhooks } from './pages/Webhooks'
import { PaymentIntents } from './pages/PaymentIntents'
import { Docs } from './pages/Docs'
import { Reconciliation } from './pages/Reconciliation'
import { PaymentIntentDetail } from './pages/PaymentIntentDetail'
import { Events } from './pages/Events'
import { OAuthClients } from './pages/OAuthClients'
import { Forbidden } from './pages/Forbidden'
import { NotFound } from './pages/NotFound'

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="login-page"><p className="muted">Loading…</p></div>
  if (!user) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <RequireAuth>
            <Layout />
          </RequireAuth>
        }
      >
        <Route index element={<Home />} />
        <Route path="status" element={<Health />} />
        <Route path="tenants" element={<Tenants />} />
        <Route path="tenants/:id" element={<TenantDetail />} />
        <Route path="integrations" element={<Integrations />} />
        <Route path="integrations/:id" element={<IntegrationDetail />} />
        <Route path="webhooks" element={<Webhooks />} />
        <Route path="intents" element={<PaymentIntents />} />
        <Route path="intents/:id" element={<PaymentIntentDetail />} />
        <Route path="reconciliation" element={<Reconciliation />} />
        <Route path="docs" element={<Docs />} />
        <Route path="events" element={<Events />} />
        <Route path="oauth-clients" element={<OAuthClients />} />
        <Route path="forbidden" element={<Forbidden />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  )
}
