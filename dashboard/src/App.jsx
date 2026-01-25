import { Routes, Route, Navigate } from 'react-router-dom'
import { isAuthenticated } from './api/client'
import { DemoProvider } from './context/DemoContext'
import Layout from './components/Layout'
import Register from './pages/Register'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import ConsortiumCreate from './pages/ConsortiumCreate'
import ConsortiumDetail from './pages/ConsortiumDetail'
import JoinConsortium from './pages/JoinConsortium'
import UploadData from './pages/UploadData'
import Demo from './pages/Demo'
import DemoConsorcio from './pages/DemoConsorcio'
import Governance from './pages/Governance'
import Compliance from './pages/Compliance'
import DataQuality from './pages/DataQuality'
import Marketplace from './pages/Marketplace'
import Sandbox from './pages/Sandbox'
import SandboxDemo from './pages/SandboxDemo'
import FederatedInference from './pages/FederatedInference'
import ModelExplainability from './pages/ModelExplainability'
import CompetitiveInsights from './pages/CompetitiveInsights'
import MultiModelEnsemble from './pages/MultiModelEnsemble'
import Demos from './pages/Demos'
import ClientsDemo from './pages/ClientsDemo'
import BankConsortiumDemo from './pages/BankConsortiumDemo'
import InsuranceClaimsDemo from './pages/InsuranceClaimsDemo'
import RetailChurnDemo from './pages/RetailChurnDemo'

// Protected route wrapper
const ProtectedRoute = ({ children }) => {
  if (!isAuthenticated()) {
    return <Navigate to="/" replace />
  }
  return children
}

// Public route (redirects to dashboard if logged in)
const PublicRoute = ({ children }) => {
  if (isAuthenticated()) {
    return <Navigate to="/dashboard" replace />
  }
  return children
}

function App() {
  return (
    <DemoProvider>
      <Routes>
        {/* Redirect to login or dashboard */}
        <Route path="/" element={
          isAuthenticated() ? <Navigate to="/dashboard" replace /> : <Navigate to="/login" replace />
        } />
        <Route path="/register" element={
          <PublicRoute><Register /></PublicRoute>
        } />
        <Route path="/login" element={
          <PublicRoute><Login /></PublicRoute>
        } />
        <Route path="/join" element={<JoinConsortium />} />
        <Route path="/sandbox-demo" element={<SandboxDemo />} />
        <Route path="/demo-consorcio" element={<DemoConsorcio />} />
        <Route path="/demo-governance" element={<Governance />} />
        <Route path="/demo-compliance" element={<Compliance />} />
        <Route path="/demo-quality" element={<DataQuality />} />
        <Route path="/demo-marketplace" element={<Marketplace />} />
        <Route path="/demo-sandbox" element={<Sandbox />} />
        <Route path="/demo-federated" element={<FederatedInference />} />
        <Route path="/demo-explainability" element={<ModelExplainability />} />
        <Route path="/demo-competitive" element={<CompetitiveInsights />} />
        <Route path="/demo-ensemble" element={<MultiModelEnsemble />} />
        <Route path="/demos" element={<Demos />} />
        <Route path="/clients-demo" element={<ClientsDemo />} />
        <Route path="/demo/bank-consortium" element={<BankConsortiumDemo />} />
        <Route path="/demo-bank" element={<BankConsortiumDemo />} />
        <Route path="/demo-insurance" element={<InsuranceClaimsDemo />} />
        <Route path="/demo-retail" element={<RetailChurnDemo />} />

      {/* Protected routes with Layout */}
      <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/demo" element={<Demo />} />
        <Route path="/governance" element={<Governance />} />
        <Route path="/governance/:consortiumId" element={<Governance />} />
        <Route path="/compliance" element={<Compliance />} />
        <Route path="/compliance/:consortiumId" element={<Compliance />} />
        <Route path="/quality" element={<DataQuality />} />
        <Route path="/quality/:consortiumId" element={<DataQuality />} />
        <Route path="/marketplace" element={<Marketplace />} />
        <Route path="/marketplace/:consortiumId" element={<Marketplace />} />
        <Route path="/sandbox" element={<Sandbox />} />
        <Route path="/sandbox/:consortiumId" element={<Sandbox />} />
        <Route path="/federated" element={<FederatedInference />} />
        <Route path="/federated/:consortiumId" element={<FederatedInference />} />
        <Route path="/explainability" element={<ModelExplainability />} />
        <Route path="/explainability/:consortiumId" element={<ModelExplainability />} />
        <Route path="/competitive" element={<CompetitiveInsights />} />
        <Route path="/competitive/:consortiumId" element={<CompetitiveInsights />} />
        <Route path="/ensemble" element={<MultiModelEnsemble />} />
        <Route path="/ensemble/:consortiumId" element={<MultiModelEnsemble />} />
        <Route path="/consortiums/new" element={<ConsortiumCreate />} />
        <Route path="/consortiums/:id" element={<ConsortiumDetail />} />
        <Route path="/consortiums/:id/upload" element={<UploadData />} />
      </Route>

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </DemoProvider>
  )
}

export default App
