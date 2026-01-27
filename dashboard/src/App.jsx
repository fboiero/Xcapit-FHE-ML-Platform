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
import ModelMetrics from './pages/ModelMetrics'
import ModelBuilder from './pages/ModelBuilder'
import DataUpload from './pages/DataUpload'
import TrainingDashboard from './pages/TrainingDashboard'
import ResultsVisualization from './pages/ResultsVisualization'
import ModelComparison from './pages/ModelComparison'
import DataExplorer from './pages/DataExplorer'
import UserSettings from './pages/UserSettings'
import RealtimeMonitoring from './pages/RealtimeMonitoring'
import ModelDeployment from './pages/ModelDeployment'
import AuditLogViewer from './pages/AuditLogViewer'
import ApiPlayground from './pages/ApiPlayground'
import NotificationCenter from './pages/NotificationCenter'
import TeamManagement from './pages/TeamManagement'
import Billing from './pages/Billing'

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
        {/* Sandbox entry point - requires email capture */}
        <Route path="/sandbox-demo" element={<SandboxDemo />} />
        {/* Demo routes accessible after sandbox access */}
        <Route path="/demo-consorcio" element={<DemoConsorcio />} />

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
        <Route path="/metrics" element={<ModelMetrics />} />
        <Route path="/metrics/:consortiumId" element={<ModelMetrics />} />
        <Route path="/model-builder" element={<ModelBuilder />} />
        <Route path="/model-builder/:consortiumId" element={<ModelBuilder />} />
        <Route path="/data-upload" element={<DataUpload />} />
        <Route path="/data-upload/:consortiumId" element={<DataUpload />} />
        <Route path="/training" element={<TrainingDashboard />} />
        <Route path="/training/:consortiumId" element={<TrainingDashboard />} />
        <Route path="/results" element={<ResultsVisualization />} />
        <Route path="/results/:consortiumId" element={<ResultsVisualization />} />
        <Route path="/comparison" element={<ModelComparison />} />
        <Route path="/comparison/:consortiumId" element={<ModelComparison />} />
        <Route path="/data-explorer" element={<DataExplorer />} />
        <Route path="/data-explorer/:consortiumId" element={<DataExplorer />} />
        <Route path="/monitoring" element={<RealtimeMonitoring />} />
        <Route path="/monitoring/:consortiumId" element={<RealtimeMonitoring />} />
        <Route path="/settings" element={<UserSettings />} />
        <Route path="/deployment" element={<ModelDeployment />} />
        <Route path="/deployment/:consortiumId" element={<ModelDeployment />} />
        <Route path="/audit-log" element={<AuditLogViewer />} />
        <Route path="/api-playground" element={<ApiPlayground />} />
        <Route path="/notifications" element={<NotificationCenter />} />
        <Route path="/team" element={<TeamManagement />} />
        <Route path="/billing" element={<Billing />} />
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
