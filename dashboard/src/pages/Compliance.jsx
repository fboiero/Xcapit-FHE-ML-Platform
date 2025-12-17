import { useState, useEffect, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import {
  ShieldCheckIcon,
  DocumentTextIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
  DocumentMagnifyingGlassIcon,
  ClipboardDocumentCheckIcon,
  GlobeAltIcon,
  BuildingOfficeIcon,
  ServerStackIcon,
  CreditCardIcon,
} from '@heroicons/react/24/outline'
import * as complianceApi from '../api/compliance'
import { isDemoMode } from '../api/client'
import { Sentry } from '../lib/sentry'

// Framework icons and colors
const FrameworkConfig = {
  framework_gdpr: {
    name: 'GDPR',
    icon: GlobeAltIcon,
    color: 'blue',
    bgColor: 'bg-blue-50',
    textColor: 'text-blue-600',
    borderColor: 'border-blue-200',
  },
  framework_hipaa: {
    name: 'HIPAA',
    icon: BuildingOfficeIcon,
    color: 'purple',
    bgColor: 'bg-purple-50',
    textColor: 'text-purple-600',
    borderColor: 'border-purple-200',
  },
  framework_soc2: {
    name: 'SOC2',
    icon: ServerStackIcon,
    color: 'green',
    bgColor: 'bg-green-50',
    textColor: 'text-green-600',
    borderColor: 'border-green-200',
  },
  framework_pci_dss: {
    name: 'PCI-DSS',
    icon: CreditCardIcon,
    color: 'orange',
    bgColor: 'bg-orange-50',
    textColor: 'text-orange-600',
    borderColor: 'border-orange-200',
  },
}

// Mock data for demo
const MOCK_DASHBOARD = {
  consortium_id: 'cons_demo123',
  overall_score: 87.5,
  overall_status: 'partial',
  enabled_frameworks_count: 3,
  frameworks: [
    { framework_id: 'framework_gdpr', framework_name: 'GDPR', score: 100, status: 'compliant', passed: 8, failed: 0, pending: 0, total: 8 },
    { framework_id: 'framework_hipaa', framework_name: 'HIPAA', score: 75, status: 'non_compliant', passed: 6, failed: 2, pending: 0, total: 8 },
    { framework_id: 'framework_soc2', framework_name: 'SOC2', score: 87.5, status: 'partial', passed: 7, failed: 0, pending: 1, total: 8 },
  ],
  last_check_at: '2024-12-08T14:30:00Z',
}

const MOCK_CHECKS = [
  { id: 'check_1', framework_id: 'framework_gdpr', control_id: 'gdpr_encryption', status: 'passed', result: 'Todos los datos estan encriptados con FHE', checked_at: '2024-12-08T14:30:00Z' },
  { id: 'check_2', framework_id: 'framework_gdpr', control_id: 'gdpr_access_control', status: 'passed', result: 'Control de acceso implementado correctamente', checked_at: '2024-12-08T14:30:00Z' },
  { id: 'check_3', framework_id: 'framework_gdpr', control_id: 'gdpr_data_minimization', status: 'passed', result: 'Solo se procesan datos necesarios', checked_at: '2024-12-08T14:30:00Z' },
  { id: 'check_4', framework_id: 'framework_hipaa', control_id: 'hipaa_phi_protection', status: 'passed', result: 'PHI protegido con encriptacion', checked_at: '2024-12-08T14:30:00Z' },
  { id: 'check_5', framework_id: 'framework_hipaa', control_id: 'hipaa_audit_controls', status: 'failed', result: 'Audit trail incompleto', checked_at: '2024-12-08T14:30:00Z' },
  { id: 'check_6', framework_id: 'framework_soc2', control_id: 'soc2_availability', status: 'pending', result: 'Pendiente verificacion de SLA', checked_at: '2024-12-08T14:30:00Z' },
]

const MOCK_REPORTS = [
  { id: 'report_1', framework_id: 'framework_gdpr', framework_name: 'GDPR', overall_score: 100, status: 'compliant', generated_at: '2024-12-08T14:35:00Z', valid_until: '2025-03-08T14:35:00Z' },
  { id: 'report_2', framework_id: 'framework_hipaa', framework_name: 'HIPAA', overall_score: 75, status: 'non_compliant', generated_at: '2024-12-08T14:35:00Z', valid_until: '2025-03-08T14:35:00Z' },
]

const MOCK_ATTESTATIONS = [
  { id: 'attest_1', framework_id: 'framework_gdpr', statement: 'Confirmamos que todos los datos personales se procesan con encriptacion FHE', attester_name: 'Banco Alpha', attester_role: 'DPO', valid_from: '2024-12-01T00:00:00Z', valid_until: '2025-12-01T00:00:00Z' },
  { id: 'attest_2', framework_id: 'framework_soc2', statement: 'Los controles de seguridad cumplen con SOC2 Type II', attester_name: 'Banco Beta', attester_role: 'CISO', valid_from: '2024-11-15T00:00:00Z', valid_until: '2025-11-15T00:00:00Z' },
]

const StatusConfig = {
  compliant: { label: 'Compliant', color: 'text-green-600', bgColor: 'bg-green-100', icon: CheckCircleIcon },
  non_compliant: { label: 'No Compliant', color: 'text-red-600', bgColor: 'bg-red-100', icon: XCircleIcon },
  partial: { label: 'Parcial', color: 'text-yellow-600', bgColor: 'bg-yellow-100', icon: ExclamationTriangleIcon },
  pending: { label: 'Pendiente', color: 'text-gray-600', bgColor: 'bg-gray-100', icon: ClockIcon },
  passed: { label: 'Aprobado', color: 'text-green-600', bgColor: 'bg-green-100', icon: CheckCircleIcon },
  failed: { label: 'Fallido', color: 'text-red-600', bgColor: 'bg-red-100', icon: XCircleIcon },
}

function ScoreRing({ score, size = 120, strokeWidth = 8 }) {
  const radius = (size - strokeWidth) / 2
  const circumference = radius * 2 * Math.PI
  const offset = circumference - (score / 100) * circumference

  const getColor = (score) => {
    if (score >= 90) return '#10B981' // green
    if (score >= 70) return '#F59E0B' // yellow
    return '#EF4444' // red
  }

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg className="transform -rotate-90" width={size} height={size}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#E5E7EB"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={getColor(score)}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-500"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold text-gray-900">{score.toFixed(0)}%</span>
        <span className="text-xs text-gray-500">Score</span>
      </div>
    </div>
  )
}

function FrameworkCard({ framework }) {
  const config = FrameworkConfig[framework.framework_id] || {
    name: framework.framework_name,
    icon: ShieldCheckIcon,
    bgColor: 'bg-gray-50',
    textColor: 'text-gray-600',
    borderColor: 'border-gray-200',
  }
  const Icon = config.icon
  const statusConfig = StatusConfig[framework.status] || StatusConfig.pending
  const StatusIcon = statusConfig.icon

  return (
    <div className={`bg-white rounded-xl border ${config.borderColor} p-6 hover:shadow-lg transition`}>
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`p-3 rounded-lg ${config.bgColor}`}>
            <Icon className={`w-6 h-6 ${config.textColor}`} />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">{config.name}</h3>
            <div className="flex items-center gap-1 mt-1">
              <StatusIcon className={`w-4 h-4 ${statusConfig.color}`} />
              <span className={`text-sm ${statusConfig.color}`}>{statusConfig.label}</span>
            </div>
          </div>
        </div>
        <ScoreRing score={framework.score} size={80} strokeWidth={6} />
      </div>
      <div className="grid grid-cols-3 gap-2 mt-4">
        <div className="text-center p-2 bg-green-50 rounded-lg">
          <div className="text-lg font-semibold text-green-600">{framework.passed}</div>
          <div className="text-xs text-gray-500">Aprobados</div>
        </div>
        <div className="text-center p-2 bg-red-50 rounded-lg">
          <div className="text-lg font-semibold text-red-600">{framework.failed}</div>
          <div className="text-xs text-gray-500">Fallidos</div>
        </div>
        <div className="text-center p-2 bg-yellow-50 rounded-lg">
          <div className="text-lg font-semibold text-yellow-600">{framework.pending}</div>
          <div className="text-xs text-gray-500">Pendientes</div>
        </div>
      </div>
      <div className="mt-4 pt-4 border-t">
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">Total controles</span>
          <span className="font-medium">{framework.total}</span>
        </div>
      </div>
    </div>
  )
}

function CheckRow({ check }) {
  const statusConfig = StatusConfig[check.status] || StatusConfig.pending
  const StatusIcon = statusConfig.icon
  const frameworkConfig = FrameworkConfig[check.framework_id]

  return (
    <tr className="hover:bg-gray-50">
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          <span className={`px-2 py-0.5 text-xs rounded-full ${frameworkConfig?.bgColor || 'bg-gray-100'} ${frameworkConfig?.textColor || 'text-gray-600'}`}>
            {frameworkConfig?.name || check.framework_id}
          </span>
        </div>
      </td>
      <td className="px-4 py-3 text-sm text-gray-900">{check.control_id}</td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-1">
          <StatusIcon className={`w-4 h-4 ${statusConfig.color}`} />
          <span className={`text-sm ${statusConfig.color}`}>{statusConfig.label}</span>
        </div>
      </td>
      <td className="px-4 py-3 text-sm text-gray-600 max-w-xs truncate">{check.result}</td>
      <td className="px-4 py-3 text-sm text-gray-500">
        {new Date(check.checked_at).toLocaleDateString()}
      </td>
    </tr>
  )
}

function ReportCard({ report }) {
  const statusConfig = StatusConfig[report.status] || StatusConfig.pending
  const StatusIcon = statusConfig.icon
  const frameworkConfig = FrameworkConfig[report.framework_id]

  return (
    <div className="bg-white rounded-lg border p-4 hover:shadow-md transition">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <DocumentTextIcon className={`w-5 h-5 ${frameworkConfig?.textColor || 'text-gray-600'}`} />
          <span className="font-medium">{report.framework_name}</span>
        </div>
        <div className="flex items-center gap-1">
          <StatusIcon className={`w-4 h-4 ${statusConfig.color}`} />
          <span className={`text-sm ${statusConfig.color}`}>{statusConfig.label}</span>
        </div>
      </div>
      <div className="flex items-center justify-between">
        <div>
          <div className="text-2xl font-bold text-gray-900">{report.overall_score}%</div>
          <div className="text-xs text-gray-500">Score de compliance</div>
        </div>
        <div className="text-right text-sm">
          <div className="text-gray-500">Generado</div>
          <div className="text-gray-900">{new Date(report.generated_at).toLocaleDateString()}</div>
        </div>
      </div>
      <div className="mt-3 pt-3 border-t text-xs text-gray-500">
        Valido hasta: {new Date(report.valid_until).toLocaleDateString()}
      </div>
    </div>
  )
}

function AttestationCard({ attestation }) {
  const frameworkConfig = FrameworkConfig[attestation.framework_id]
  const isValid = new Date(attestation.valid_until) > new Date()

  return (
    <div className="bg-white rounded-lg border p-4 hover:shadow-md transition">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <ClipboardDocumentCheckIcon className={`w-5 h-5 ${frameworkConfig?.textColor || 'text-gray-600'}`} />
          <span className={`px-2 py-0.5 text-xs rounded-full ${frameworkConfig?.bgColor || 'bg-gray-100'} ${frameworkConfig?.textColor || 'text-gray-600'}`}>
            {frameworkConfig?.name || attestation.framework_id}
          </span>
        </div>
        {isValid ? (
          <span className="flex items-center gap-1 text-xs text-green-600 bg-green-50 px-2 py-1 rounded-full">
            <CheckCircleIcon className="w-3 h-3" />
            Vigente
          </span>
        ) : (
          <span className="flex items-center gap-1 text-xs text-red-600 bg-red-50 px-2 py-1 rounded-full">
            <XCircleIcon className="w-3 h-3" />
            Expirado
          </span>
        )}
      </div>
      <p className="text-sm text-gray-700 mb-3 line-clamp-2">{attestation.statement}</p>
      <div className="flex items-center justify-between text-sm">
        <div>
          <span className="text-gray-500">Por:</span>{' '}
          <span className="font-medium">{attestation.attester_name}</span>
          {attestation.attester_role && (
            <span className="text-gray-500"> ({attestation.attester_role})</span>
          )}
        </div>
      </div>
      <div className="mt-2 text-xs text-gray-500">
        Valido: {new Date(attestation.valid_from).toLocaleDateString()} - {new Date(attestation.valid_until).toLocaleDateString()}
      </div>
    </div>
  )
}

export default function Compliance() {
  const { consortiumId } = useParams()
  const [activeTab, setActiveTab] = useState('dashboard')
  const [dashboard, setDashboard] = useState(MOCK_DASHBOARD)
  const [checks, setChecks] = useState(MOCK_CHECKS)
  const [reports, setReports] = useState(MOCK_REPORTS)
  const [attestations, setAttestations] = useState(MOCK_ATTESTATIONS)
  const [loading, setLoading] = useState(false)
  const [usingMockData, setUsingMockData] = useState(true)

  // Fetch compliance data from API with fallback to mock
  const fetchComplianceData = useCallback(async () => {
    // Use mock data if no consortiumId or in demo mode
    if (!consortiumId || isDemoMode()) {
      setDashboard(MOCK_DASHBOARD)
      setChecks(MOCK_CHECKS)
      setReports(MOCK_REPORTS)
      setAttestations(MOCK_ATTESTATIONS)
      setUsingMockData(true)
      return
    }

    setLoading(true)
    try {
      // Fetch all data in parallel
      const [dashboardData, checksData, reportsData, attestationsData] = await Promise.all([
        complianceApi.getComplianceDashboard(consortiumId),
        complianceApi.getChecks(consortiumId),
        complianceApi.getReports(consortiumId),
        complianceApi.getAttestations(consortiumId),
      ])

      setDashboard(dashboardData)
      setChecks(checksData.checks || checksData || [])
      setReports(reportsData.reports || reportsData || [])
      setAttestations(attestationsData.attestations || attestationsData || [])
      setUsingMockData(false)
    } catch (error) {
      setDashboard(MOCK_DASHBOARD)
      setChecks(MOCK_CHECKS)
      setReports(MOCK_REPORTS)
      setAttestations(MOCK_ATTESTATIONS)
      setUsingMockData(true)
    } finally {
      setLoading(false)
    }
  }, [consortiumId])

  useEffect(() => {
    fetchComplianceData()
  }, [fetchComplianceData])

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: ChartBarIcon },
    { id: 'checks', label: 'Verificaciones', icon: DocumentMagnifyingGlassIcon },
    { id: 'reports', label: 'Reportes', icon: DocumentTextIcon },
    { id: 'attestations', label: 'Attestations', icon: ClipboardDocumentCheckIcon },
  ]

  const overallStatusConfig = StatusConfig[dashboard.overall_status] || StatusConfig.pending
  const OverallStatusIcon = overallStatusConfig.icon

  // Handle running automated checks
  const handleRunChecks = async () => {
    if (!consortiumId || isDemoMode()) {
      alert('Demo mode: Las verificaciones automaticas requieren un consorcio activo')
      return
    }

    setLoading(true)
    try {
      await complianceApi.runAutomatedChecks(consortiumId, null) // null = all frameworks
      await fetchComplianceData() // Refresh data
    } catch (error) {
      Sentry.captureException(error)
      alert('Error ejecutando verificaciones: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  // Handle generating report
  const handleGenerateReport = async (frameworkId = null) => {
    if (!consortiumId || isDemoMode()) {
      alert('Demo mode: La generacion de reportes requiere un consorcio activo')
      return
    }

    setLoading(true)
    try {
      await complianceApi.generateReport(consortiumId, frameworkId)
      await fetchComplianceData() // Refresh data
    } catch (error) {
      Sentry.captureException(error)
      alert('Error generando reporte: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Demo Mode Indicator */}
      {usingMockData && (
        <div className="mb-4 bg-amber-50 border border-amber-200 rounded-lg p-3 flex items-center gap-2">
          <ExclamationTriangleIcon className="w-5 h-5 text-amber-600" />
          <span className="text-sm text-amber-800">
            <strong>Modo Demo:</strong> Mostrando datos de ejemplo. Conecta un backend para ver datos reales.
          </span>
        </div>
      )}

      {/* Loading Overlay */}
      {loading && (
        <div className="fixed inset-0 bg-black/20 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 shadow-xl flex items-center gap-3">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-brand-600"></div>
            <span>Procesando...</span>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="p-3 bg-brand-100 rounded-lg">
          <ShieldCheckIcon className="w-8 h-8 text-brand-600" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Compliance Dashboard</h1>
          <p className="text-gray-600">Verificacion automatica GDPR/HIPAA/SOC2/PCI-DSS</p>
        </div>
      </div>

      {/* Overall Status Card */}
      <div className="bg-white rounded-xl border shadow-sm p-6 mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            <ScoreRing score={dashboard.overall_score} size={140} strokeWidth={10} />
            <div>
              <div className="flex items-center gap-2 mb-2">
                <OverallStatusIcon className={`w-6 h-6 ${overallStatusConfig.color}`} />
                <span className={`text-lg font-semibold ${overallStatusConfig.color}`}>
                  {overallStatusConfig.label}
                </span>
              </div>
              <div className="text-sm text-gray-600">
                <p>{dashboard.enabled_frameworks_count} frameworks habilitados</p>
                {dashboard.last_check_at && (
                  <p className="mt-1">
                    Ultima verificacion: {new Date(dashboard.last_check_at).toLocaleString()}
                  </p>
                )}
              </div>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleRunChecks}
              disabled={loading}
              className="px-4 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition flex items-center gap-2 disabled:opacity-50"
            >
              <DocumentMagnifyingGlassIcon className="w-5 h-5" />
              Ejecutar Verificacion
            </button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b mb-6">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 border-b-2 transition ${
              activeTab === tab.id
                ? 'border-brand-600 text-brand-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <tab.icon className="w-5 h-5" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'dashboard' && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Frameworks Habilitados</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {dashboard.frameworks.map((framework) => (
              <FrameworkCard key={framework.framework_id} framework={framework} />
            ))}
          </div>

          {/* Quick Stats */}
          <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-lg border p-4 text-center">
              <div className="text-3xl font-bold text-green-600">
                {dashboard.frameworks.reduce((sum, f) => sum + f.passed, 0)}
              </div>
              <div className="text-sm text-gray-500">Controles Aprobados</div>
            </div>
            <div className="bg-white rounded-lg border p-4 text-center">
              <div className="text-3xl font-bold text-red-600">
                {dashboard.frameworks.reduce((sum, f) => sum + f.failed, 0)}
              </div>
              <div className="text-sm text-gray-500">Controles Fallidos</div>
            </div>
            <div className="bg-white rounded-lg border p-4 text-center">
              <div className="text-3xl font-bold text-yellow-600">
                {dashboard.frameworks.reduce((sum, f) => sum + f.pending, 0)}
              </div>
              <div className="text-sm text-gray-500">Pendientes</div>
            </div>
            <div className="bg-white rounded-lg border p-4 text-center">
              <div className="text-3xl font-bold text-brand-600">
                {dashboard.frameworks.reduce((sum, f) => sum + f.total, 0)}
              </div>
              <div className="text-sm text-gray-500">Total Controles</div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'checks' && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Verificaciones de Compliance</h2>
            <div className="flex gap-2">
              <select className="px-3 py-2 border rounded-lg text-sm">
                <option value="">Todos los frameworks</option>
                <option value="framework_gdpr">GDPR</option>
                <option value="framework_hipaa">HIPAA</option>
                <option value="framework_soc2">SOC2</option>
                <option value="framework_pci_dss">PCI-DSS</option>
              </select>
              <select className="px-3 py-2 border rounded-lg text-sm">
                <option value="">Todos los estados</option>
                <option value="passed">Aprobados</option>
                <option value="failed">Fallidos</option>
                <option value="pending">Pendientes</option>
              </select>
            </div>
          </div>
          <div className="bg-white rounded-lg border overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Framework</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Control</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Estado</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Resultado</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fecha</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {checks.map((check) => (
                  <CheckRow key={check.id} check={check} />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'reports' && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Reportes de Compliance</h2>
            <button
              onClick={() => handleGenerateReport()}
              disabled={loading}
              className="px-4 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition flex items-center gap-2 disabled:opacity-50"
            >
              <DocumentTextIcon className="w-5 h-5" />
              Generar Reporte
            </button>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {reports.map((report) => (
              <ReportCard key={report.id} report={report} />
            ))}
          </div>
        </div>
      )}

      {activeTab === 'attestations' && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Attestations</h2>
            <button className="px-4 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition flex items-center gap-2">
              <ClipboardDocumentCheckIcon className="w-5 h-5" />
              Nueva Attestation
            </button>
          </div>
          <div className="grid md:grid-cols-2 gap-4">
            {attestations.map((attestation) => (
              <AttestationCard key={attestation.id} attestation={attestation} />
            ))}
          </div>
        </div>
      )}

      {/* Info Section */}
      <div className="mt-8 bg-blue-50 rounded-lg p-6">
        <h3 className="font-semibold text-blue-900 mb-2">Sobre Compliance</h3>
        <p className="text-blue-800 text-sm">
          El dashboard de compliance verifica automaticamente el cumplimiento de regulaciones internacionales.
          Los datos nunca salen de la plataforma - todas las verificaciones se realizan sobre datos encriptados
          con FHE (Fully Homomorphic Encryption), garantizando la privacidad total.
        </p>
        <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <GlobeAltIcon className="w-8 h-8 mx-auto text-blue-600" />
            <div className="text-sm font-medium text-blue-900 mt-1">GDPR</div>
            <div className="text-xs text-blue-700">Proteccion de datos UE</div>
          </div>
          <div className="text-center">
            <BuildingOfficeIcon className="w-8 h-8 mx-auto text-purple-600" />
            <div className="text-sm font-medium text-blue-900 mt-1">HIPAA</div>
            <div className="text-xs text-blue-700">Datos de salud US</div>
          </div>
          <div className="text-center">
            <ServerStackIcon className="w-8 h-8 mx-auto text-green-600" />
            <div className="text-sm font-medium text-blue-900 mt-1">SOC2</div>
            <div className="text-xs text-blue-700">Seguridad cloud</div>
          </div>
          <div className="text-center">
            <CreditCardIcon className="w-8 h-8 mx-auto text-orange-600" />
            <div className="text-sm font-medium text-blue-900 mt-1">PCI-DSS</div>
            <div className="text-xs text-blue-700">Datos de pago</div>
          </div>
        </div>
      </div>
    </div>
  )
}
