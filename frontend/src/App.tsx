import { Navigate, Outlet, Route, Routes } from 'react-router-dom'
import { useAuth } from './auth/authState'
import { WorkspaceProvider } from './workspace/WorkspaceContext'
import { useWorkspace } from './workspace/useWorkspace'
import { Layout } from './components/Layout'
import { Login } from './pages/Login'
import { Landing } from './pages/Landing'
import { AuthCallback } from './pages/AuthCallback'
import { Health } from './pages/Health'
import { Home } from './pages/Home'
import { Tenants } from './pages/Tenants'
import { TenantDetail } from './pages/TenantDetail'
import { Integrations } from './pages/Integrations'
import { IntegrationDetail } from './pages/IntegrationDetail'
import { IntegrationCreate } from './pages/IntegrationCreate'
import { Webhooks } from './pages/Webhooks'
import { PaymentIntents } from './pages/PaymentIntents'
import { Docs } from './pages/Docs'
import { Reconciliation } from './pages/Reconciliation'
import { PaymentIntentDetail } from './pages/PaymentIntentDetail'
import { Events } from './pages/Events'
import { OAuthClients } from './pages/OAuthClients'
import { Forbidden } from './pages/Forbidden'
import { SelectBusiness } from './pages/SelectBusiness'
import { NotFound } from './pages/NotFound'
import { ThemeLab } from './pages/ThemeLab'
import { PageLoader } from './components/primitives'

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return <PageLoader label="Loading your workspace…" />
  if (!user) return <Navigate to="/login" replace />
  return <>{children}</>
}

function RequireWorkspace({ children }: { children: React.ReactNode }) {
  const { loading, activeTenantId, needsSelection } = useWorkspace()
  if (loading) return <PageLoader label="Loading your businesses…" />
  if (needsSelection || !activeTenantId) return <Navigate to="/select-business" replace />
  return <>{children}</>
}

/** Auth + workspace context for all app shell routes. */
function AppShell() {
  return (
    <RequireAuth>
      <WorkspaceProvider>
        <Outlet />
      </WorkspaceProvider>
    </RequireAuth>
  )
}


export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/auth/callback" element={<AuthCallback />} />
      <Route element={<AppShell />}>
        <Route path="select-business" element={<SelectBusiness />} />
        <Route
          element={
            <RequireWorkspace>
              <Layout />
            </RequireWorkspace>
          }
        >
          <Route path="dashboard" element={<Home />} />
          <Route path="status" element={<Health />} />
          <Route path="tenants" element={<Tenants />} />
          <Route path="tenants/:id" element={<TenantDetail />} />
          <Route path="integrations" element={<Integrations />} />
          <Route path="integrations/new" element={<IntegrationCreate />} />
          <Route path="integrations/:id" element={<IntegrationDetail />} />
          <Route path="webhooks" element={<Webhooks />} />
          <Route path="intents" element={<PaymentIntents />} />
          <Route path="intents/:id" element={<PaymentIntentDetail />} />
          <Route path="reconciliation" element={<Reconciliation />} />
          <Route path="docs" element={<Docs />} />
          <Route path="theme-lab" element={<ThemeLab />} />
          <Route path="events" element={<Events />} />
          <Route path="oauth-clients" element={<OAuthClients />} />
          <Route path="forbidden" element={<Forbidden />} />
        </Route>
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}
