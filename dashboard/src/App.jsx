import { lazy, Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { isAuthenticated } from './api/client'
import { DemoProvider } from './context/DemoContext'
import Layout from './components/Layout'
import { PageLoader } from './components/ui'

const Register = lazy(() => import('./pages/Register'))
const Login = lazy(() => import('./pages/Login'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const ConsortiumCreate = lazy(() => import('./pages/ConsortiumCreate'))
const ConsortiumDetail = lazy(() => import('./pages/ConsortiumDetail'))
const JoinConsortium = lazy(() => import('./pages/JoinConsortium'))
const UploadData = lazy(() => import('./pages/UploadData'))
const Demo = lazy(() => import('./pages/Demo'))
const DemoConsorcio = lazy(() => import('./pages/DemoConsorcio'))
const Governance = lazy(() => import('./pages/Governance'))
const Compliance = lazy(() => import('./pages/Compliance'))
const DataQuality = lazy(() => import('./pages/DataQuality'))
const Marketplace = lazy(() => import('./pages/Marketplace'))
const Sandbox = lazy(() => import('./pages/Sandbox'))
const SandboxDemo = lazy(() => import('./pages/SandboxDemo'))
const FederatedInference = lazy(() => import('./pages/FederatedInference'))
const ModelExplainability = lazy(() => import('./pages/ModelExplainability'))
const CompetitiveInsights = lazy(() => import('./pages/CompetitiveInsights'))
const MultiModelEnsemble = lazy(() => import('./pages/MultiModelEnsemble'))
const ModelMetrics = lazy(() => import('./pages/ModelMetrics'))
const ModelBuilder = lazy(() => import('./pages/ModelBuilder'))
const DataUpload = lazy(() => import('./pages/DataUpload'))
const TrainingDashboard = lazy(() => import('./pages/TrainingDashboard'))
const ResultsVisualization = lazy(() => import('./pages/ResultsVisualization'))
const ModelComparison = lazy(() => import('./pages/ModelComparison'))
const DataExplorer = lazy(() => import('./pages/DataExplorer'))
const UserSettings = lazy(() => import('./pages/UserSettings'))
const RealtimeMonitoring = lazy(() => import('./pages/RealtimeMonitoring'))
const ModelDeployment = lazy(() => import('./pages/ModelDeployment'))
const AuditLogViewer = lazy(() => import('./pages/AuditLogViewer'))
const ApiPlayground = lazy(() => import('./pages/ApiPlayground'))
const NotificationCenter = lazy(() => import('./pages/NotificationCenter'))
const TeamManagement = lazy(() => import('./pages/TeamManagement'))
const Billing = lazy(() => import('./pages/Billing'))
const ReportBuilder = lazy(() => import('./pages/ReportBuilder'))
const WorkflowAutomation = lazy(() => import('./pages/WorkflowAutomation'))
const AdminPanel = lazy(() => import('./pages/AdminPanel'))

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
      <Suspense fallback={<PageLoader />}>
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
          <Route path="/reports" element={<ReportBuilder />} />
          <Route path="/workflows" element={<WorkflowAutomation />} />
          <Route path="/admin" element={<AdminPanel />} />
          <Route path="/consortiums/new" element={<ConsortiumCreate />} />
          <Route path="/consortiums/:id" element={<ConsortiumDetail />} />
          <Route path="/consortiums/:id/upload" element={<UploadData />} />
        </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </DemoProvider>
  )
}

export default App
