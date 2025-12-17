import { useState, useEffect, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import {
  ChartBarIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  BellAlertIcon,
  Cog6ToothIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  BuildingOffice2Icon,
  CircleStackIcon,
  DocumentCheckIcon,
  AdjustmentsHorizontalIcon,
} from '@heroicons/react/24/outline'
import * as dataQualityApi from '../api/dataQuality'
import { isDemoMode } from '../api/client'
import { Sentry } from '../lib/sentry'

// Metric configuration
const MetricConfig = {
  completeness: {
    name: 'Completitud',
    description: 'Porcentaje de campos sin valores nulos',
    icon: CircleStackIcon,
    color: 'blue',
    bgColor: 'bg-blue-50',
    textColor: 'text-blue-600',
    borderColor: 'border-blue-200',
  },
  consistency: {
    name: 'Consistencia',
    description: 'Coherencia de datos a traves del tiempo',
    icon: DocumentCheckIcon,
    color: 'purple',
    bgColor: 'bg-purple-50',
    textColor: 'text-purple-600',
    borderColor: 'border-purple-200',
  },
  uniqueness: {
    name: 'Unicidad',
    description: 'Porcentaje de registros unicos',
    icon: ChartBarIcon,
    color: 'green',
    bgColor: 'bg-green-50',
    textColor: 'text-green-600',
    borderColor: 'border-green-200',
  },
  validity: {
    name: 'Validez',
    description: 'Datos dentro de rangos esperados',
    icon: CheckCircleIcon,
    color: 'orange',
    bgColor: 'bg-orange-50',
    textColor: 'text-orange-600',
    borderColor: 'border-orange-200',
  },
  freshness: {
    name: 'Frescura',
    description: 'Que tan recientes son los datos',
    icon: ClockIcon,
    color: 'teal',
    bgColor: 'bg-teal-50',
    textColor: 'text-teal-600',
    borderColor: 'border-teal-200',
  },
}

// Mock data for demo
const MOCK_DASHBOARD = {
  consortium_id: 'cons_demo123',
  overall_score: 92.3,
  completeness_avg: 96.5,
  consistency_avg: 88.2,
  uniqueness_avg: 94.8,
  validity_avg: 91.5,
  freshness_avg: 90.5,
  total_records: 125000,
  total_companies: 3,
  total_assessments: 12,
  active_alerts: 2,
  last_assessment: '2024-12-08T15:30:00Z',
  companies: [
    {
      company_id: 'comp_1',
      company_name: 'Banco Alpha',
      overall_score: 95.2,
      completeness_score: 98.5,
      consistency_score: 92.0,
      uniqueness_score: 96.5,
      validity_score: 93.0,
      freshness_score: 96.0,
      total_records: 50000,
      assessments_count: 4,
      last_assessment: '2024-12-08T15:30:00Z',
    },
    {
      company_id: 'comp_2',
      company_name: 'Banco Beta',
      overall_score: 88.5,
      completeness_score: 94.0,
      consistency_score: 85.0,
      uniqueness_score: 91.5,
      validity_score: 88.0,
      freshness_score: 84.0,
      total_records: 45000,
      assessments_count: 4,
      last_assessment: '2024-12-08T14:00:00Z',
    },
    {
      company_id: 'comp_3',
      company_name: 'Fintech Gamma',
      overall_score: 93.2,
      completeness_score: 97.0,
      consistency_score: 88.0,
      uniqueness_score: 96.5,
      validity_score: 93.5,
      freshness_score: 91.0,
      total_records: 30000,
      assessments_count: 4,
      last_assessment: '2024-12-08T15:00:00Z',
    },
  ],
}

const MOCK_ALERTS = [
  {
    id: 'alert_1',
    company_id: 'comp_2',
    company_name: 'Banco Beta',
    metric: 'freshness',
    current_value: 84.0,
    threshold: 85.0,
    severity: 'warning',
    status: 'active',
    message: 'Freshness score por debajo del umbral de advertencia',
    created_at: '2024-12-08T14:00:00Z',
  },
  {
    id: 'alert_2',
    company_id: 'comp_2',
    company_name: 'Banco Beta',
    metric: 'consistency',
    current_value: 85.0,
    threshold: 87.0,
    severity: 'warning',
    status: 'active',
    message: 'Consistency score por debajo del umbral de advertencia',
    created_at: '2024-12-08T14:00:00Z',
  },
]

const MOCK_RULES = [
  { id: 'rule_1', metric: 'completeness', warning_threshold: 90, critical_threshold: 80, enabled: true },
  { id: 'rule_2', metric: 'consistency', warning_threshold: 87, critical_threshold: 75, enabled: true },
  { id: 'rule_3', metric: 'uniqueness', warning_threshold: 90, critical_threshold: 80, enabled: true },
  { id: 'rule_4', metric: 'validity', warning_threshold: 88, critical_threshold: 78, enabled: true },
  { id: 'rule_5', metric: 'freshness', warning_threshold: 85, critical_threshold: 70, enabled: true },
]

const MOCK_HISTORY = [
  { date: '2024-12-01', overall: 90.5, completeness: 95.0, consistency: 86.0, uniqueness: 93.0, validity: 89.5, freshness: 89.0 },
  { date: '2024-12-02', overall: 91.0, completeness: 95.5, consistency: 87.0, uniqueness: 93.5, validity: 90.0, freshness: 89.0 },
  { date: '2024-12-03', overall: 91.5, completeness: 96.0, consistency: 87.5, uniqueness: 94.0, validity: 90.5, freshness: 89.5 },
  { date: '2024-12-04', overall: 91.8, completeness: 96.0, consistency: 87.5, uniqueness: 94.5, validity: 91.0, freshness: 90.0 },
  { date: '2024-12-05', overall: 92.0, completeness: 96.5, consistency: 88.0, uniqueness: 94.5, validity: 91.0, freshness: 90.0 },
  { date: '2024-12-06', overall: 92.1, completeness: 96.5, consistency: 88.0, uniqueness: 94.5, validity: 91.5, freshness: 90.5 },
  { date: '2024-12-07', overall: 92.2, completeness: 96.5, consistency: 88.0, uniqueness: 94.5, validity: 91.5, freshness: 90.5 },
  { date: '2024-12-08', overall: 92.3, completeness: 96.5, consistency: 88.2, uniqueness: 94.8, validity: 91.5, freshness: 90.5 },
]

const SeverityConfig = {
  warning: { label: 'Advertencia', color: 'text-yellow-600', bgColor: 'bg-yellow-100', icon: ExclamationTriangleIcon },
  critical: { label: 'Critico', color: 'text-red-600', bgColor: 'bg-red-100', icon: XCircleIcon },
}

const StatusConfig = {
  active: { label: 'Activa', color: 'text-red-600', bgColor: 'bg-red-100' },
  acknowledged: { label: 'Reconocida', color: 'text-yellow-600', bgColor: 'bg-yellow-100' },
  resolved: { label: 'Resuelta', color: 'text-green-600', bgColor: 'bg-green-100' },
}

function ScoreRing({ score, size = 120, strokeWidth = 8 }) {
  const radius = (size - strokeWidth) / 2
  const circumference = radius * 2 * Math.PI
  const offset = circumference - (score / 100) * circumference

  const getColor = (score) => {
    if (score >= 90) return '#10B981' // green
    if (score >= 75) return '#F59E0B' // yellow
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
        <span className="text-2xl font-bold text-gray-900">{score.toFixed(1)}%</span>
        <span className="text-xs text-gray-500">Score</span>
      </div>
    </div>
  )
}

function MetricCard({ metric, value, trend = null }) {
  const config = MetricConfig[metric] || {
    name: metric,
    icon: ChartBarIcon,
    bgColor: 'bg-gray-50',
    textColor: 'text-gray-600',
    borderColor: 'border-gray-200',
  }
  const Icon = config.icon

  const getScoreColor = (value) => {
    if (value >= 90) return 'text-green-600'
    if (value >= 75) return 'text-yellow-600'
    return 'text-red-600'
  }

  return (
    <div className={`bg-white rounded-xl border ${config.borderColor} p-6 hover:shadow-lg transition`}>
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className={`p-3 rounded-lg ${config.bgColor}`}>
            <Icon className={`w-6 h-6 ${config.textColor}`} />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">{config.name}</h3>
            <p className="text-xs text-gray-500">{config.description}</p>
          </div>
        </div>
      </div>
      <div className="mt-4 flex items-end justify-between">
        <div className={`text-3xl font-bold ${getScoreColor(value)}`}>
          {value.toFixed(1)}%
        </div>
        {trend !== null && (
          <div className={`flex items-center gap-1 text-sm ${trend >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {trend >= 0 ? (
              <ArrowTrendingUpIcon className="w-4 h-4" />
            ) : (
              <ArrowTrendingDownIcon className="w-4 h-4" />
            )}
            {Math.abs(trend).toFixed(1)}%
          </div>
        )}
      </div>
    </div>
  )
}

function CompanyRow({ company }) {
  const getScoreColor = (value) => {
    if (value >= 90) return 'text-green-600'
    if (value >= 75) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getScoreBg = (value) => {
    if (value >= 90) return 'bg-green-100'
    if (value >= 75) return 'bg-yellow-100'
    return 'bg-red-100'
  }

  return (
    <tr className="hover:bg-gray-50">
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          <BuildingOffice2Icon className="w-5 h-5 text-gray-400" />
          <span className="font-medium text-gray-900">{company.company_name}</span>
        </div>
      </td>
      <td className="px-4 py-3">
        <span className={`px-2 py-1 rounded-full text-sm font-semibold ${getScoreBg(company.overall_score)} ${getScoreColor(company.overall_score)}`}>
          {company.overall_score.toFixed(1)}%
        </span>
      </td>
      <td className="px-4 py-3 text-sm text-gray-600">{company.completeness_score.toFixed(1)}%</td>
      <td className="px-4 py-3 text-sm text-gray-600">{company.consistency_score.toFixed(1)}%</td>
      <td className="px-4 py-3 text-sm text-gray-600">{company.uniqueness_score.toFixed(1)}%</td>
      <td className="px-4 py-3 text-sm text-gray-600">{company.validity_score.toFixed(1)}%</td>
      <td className="px-4 py-3 text-sm text-gray-600">{company.freshness_score.toFixed(1)}%</td>
      <td className="px-4 py-3 text-sm text-gray-500">
        {company.total_records.toLocaleString()}
      </td>
    </tr>
  )
}

function AlertCard({ alert, onAcknowledge }) {
  const severityConfig = SeverityConfig[alert.severity] || SeverityConfig.warning
  const statusConfig = StatusConfig[alert.status] || StatusConfig.active
  const SeverityIcon = severityConfig.icon
  const metricConfig = MetricConfig[alert.metric]

  return (
    <div className="bg-white rounded-lg border p-4 hover:shadow-md transition">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className={`p-2 rounded-lg ${severityConfig.bgColor}`}>
            <SeverityIcon className={`w-5 h-5 ${severityConfig.color}`} />
          </div>
          <div>
            <span className={`px-2 py-0.5 text-xs rounded-full ${metricConfig?.bgColor || 'bg-gray-100'} ${metricConfig?.textColor || 'text-gray-600'}`}>
              {metricConfig?.name || alert.metric}
            </span>
            <span className={`ml-2 px-2 py-0.5 text-xs rounded-full ${statusConfig.bgColor} ${statusConfig.color}`}>
              {statusConfig.label}
            </span>
          </div>
        </div>
      </div>
      <p className="text-sm text-gray-700 mb-2">{alert.message}</p>
      <div className="flex items-center justify-between text-sm">
        <div>
          <span className="text-gray-500">Empresa:</span>{' '}
          <span className="font-medium">{alert.company_name}</span>
        </div>
        <div className="text-gray-500">
          Valor: <span className="font-medium text-red-600">{alert.current_value}%</span>
          {' < '}
          <span className="text-gray-400">{alert.threshold}%</span>
        </div>
      </div>
      <div className="mt-3 pt-3 border-t flex items-center justify-between">
        <span className="text-xs text-gray-500">
          {new Date(alert.created_at).toLocaleString()}
        </span>
        {alert.status === 'active' && (
          <button
            onClick={() => onAcknowledge(alert.id)}
            className="text-xs text-brand-600 hover:text-brand-700 font-medium"
          >
            Reconocer
          </button>
        )}
      </div>
    </div>
  )
}

function RuleRow({ rule, onToggle }) {
  const metricConfig = MetricConfig[rule.metric]

  return (
    <tr className="hover:bg-gray-50">
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          <span className={`px-2 py-0.5 text-xs rounded-full ${metricConfig?.bgColor || 'bg-gray-100'} ${metricConfig?.textColor || 'text-gray-600'}`}>
            {metricConfig?.name || rule.metric}
          </span>
        </div>
      </td>
      <td className="px-4 py-3">
        <span className="text-yellow-600 font-medium">{rule.warning_threshold}%</span>
      </td>
      <td className="px-4 py-3">
        <span className="text-red-600 font-medium">{rule.critical_threshold}%</span>
      </td>
      <td className="px-4 py-3">
        <button
          onClick={() => onToggle(rule.id)}
          className={`relative inline-flex h-6 w-11 items-center rounded-full transition ${
            rule.enabled ? 'bg-brand-600' : 'bg-gray-300'
          }`}
        >
          <span
            className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
              rule.enabled ? 'translate-x-6' : 'translate-x-1'
            }`}
          />
        </button>
      </td>
    </tr>
  )
}

function MiniChart({ data, metric }) {
  const values = data.map(d => d[metric])
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1

  return (
    <div className="flex items-end gap-1 h-12">
      {values.map((value, i) => (
        <div
          key={i}
          className="w-2 bg-brand-500 rounded-t"
          style={{ height: `${((value - min) / range) * 100}%`, minHeight: '4px' }}
          title={`${data[i].date}: ${value.toFixed(1)}%`}
        />
      ))}
    </div>
  )
}

export default function DataQuality() {
  const { consortiumId } = useParams()
  const [activeTab, setActiveTab] = useState('dashboard')
  const [dashboard, setDashboard] = useState(MOCK_DASHBOARD)
  const [alerts, setAlerts] = useState(MOCK_ALERTS)
  const [rules, setRules] = useState(MOCK_RULES)
  const [history, setHistory] = useState(MOCK_HISTORY)
  const [loading, setLoading] = useState(false)
  const [usingMockData, setUsingMockData] = useState(true)

  // Fetch data quality data from API with fallback to mock
  const fetchQualityData = useCallback(async () => {
    // Use mock data if no consortiumId or in demo mode
    if (!consortiumId || isDemoMode()) {
      setDashboard(MOCK_DASHBOARD)
      setAlerts(MOCK_ALERTS)
      setRules(MOCK_RULES)
      setHistory(MOCK_HISTORY)
      setUsingMockData(true)
      return
    }

    setLoading(true)
    try {
      // Fetch all data in parallel
      const [dashboardData, alertsData, rulesData, historyData] = await Promise.all([
        dataQualityApi.getQualityDashboard(consortiumId),
        dataQualityApi.getQualityAlerts(consortiumId),
        dataQualityApi.getQualityRules(consortiumId),
        dataQualityApi.getQualityHistory(consortiumId, null, null, 7),
      ])

      setDashboard(dashboardData)
      setAlerts(alertsData.alerts || alertsData || [])
      setRules(rulesData.rules || rulesData || [])
      setHistory(historyData.history || historyData || [])
      setUsingMockData(false)
    } catch (error) {
      setDashboard(MOCK_DASHBOARD)
      setAlerts(MOCK_ALERTS)
      setRules(MOCK_RULES)
      setHistory(MOCK_HISTORY)
      setUsingMockData(true)
    } finally {
      setLoading(false)
    }
  }, [consortiumId])

  useEffect(() => {
    fetchQualityData()
  }, [fetchQualityData])

  const handleAcknowledgeAlert = async (alertId) => {
    if (!consortiumId || isDemoMode()) {
      // Local update for demo mode
      setAlerts(alerts.map(a =>
        a.id === alertId ? { ...a, status: 'acknowledged' } : a
      ))
      return
    }

    try {
      await dataQualityApi.acknowledgeAlert(alertId)
      await fetchQualityData() // Refresh data
    } catch (error) {
      Sentry.captureException(error)
      // Still update locally on error
      setAlerts(alerts.map(a =>
        a.id === alertId ? { ...a, status: 'acknowledged' } : a
      ))
    }
  }

  const handleToggleRule = async (ruleId) => {
    const rule = rules.find(r => r.id === ruleId)
    if (!rule) return

    // Local update first for responsiveness
    setRules(rules.map(r =>
      r.id === ruleId ? { ...r, enabled: !r.enabled } : r
    ))

    if (!consortiumId || isDemoMode()) return

    try {
      await dataQualityApi.setQualityRule({
        consortium_id: consortiumId,
        metric: rule.metric,
        warning_threshold: rule.warning_threshold,
        critical_threshold: rule.critical_threshold,
        enabled: !rule.enabled,
      })
    } catch (error) {
      Sentry.captureException(error)
      // Revert on error
      setRules(rules.map(r =>
        r.id === ruleId ? { ...r, enabled: rule.enabled } : r
      ))
    }
  }

  // Handle new assessment
  const handleNewAssessment = async () => {
    if (!consortiumId || isDemoMode()) {
      alert('Demo mode: Las evaluaciones requieren un consorcio activo')
      return
    }

    setLoading(true)
    try {
      await dataQualityApi.assessQuality({ consortium_id: consortiumId })
      await fetchQualityData() // Refresh data
    } catch (error) {
      Sentry.captureException(error)
      alert('Error ejecutando evaluacion: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: ChartBarIcon },
    { id: 'companies', label: 'Por Empresa', icon: BuildingOffice2Icon },
    { id: 'alerts', label: 'Alertas', icon: BellAlertIcon, badge: alerts.filter(a => a.status === 'active').length },
    { id: 'rules', label: 'Reglas', icon: Cog6ToothIcon },
  ]

  const getOverallColor = (score) => {
    if (score >= 90) return 'text-green-600'
    if (score >= 75) return 'text-yellow-600'
    return 'text-red-600'
  }

  // Calculate trends from history
  const getTrend = (metric) => {
    if (history.length < 2) return 0
    const current = history[history.length - 1][metric]
    const previous = history[history.length - 2][metric]
    return current - previous
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
          <AdjustmentsHorizontalIcon className="w-8 h-8 text-brand-600" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Data Quality Score</h1>
          <p className="text-gray-600">Metricas de calidad de datos sin acceso al contenido</p>
        </div>
      </div>

      {/* Overall Status Card */}
      <div className="bg-white rounded-xl border shadow-sm p-6 mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            <ScoreRing score={dashboard.overall_score} size={140} strokeWidth={10} />
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className={`text-lg font-semibold ${getOverallColor(dashboard.overall_score)}`}>
                  Calidad General: {dashboard.overall_score >= 90 ? 'Excelente' : dashboard.overall_score >= 75 ? 'Buena' : 'Necesita Mejora'}
                </span>
              </div>
              <div className="text-sm text-gray-600 space-y-1">
                <p>{dashboard.total_companies} empresas | {dashboard.total_records.toLocaleString()} registros</p>
                <p>{dashboard.total_assessments} evaluaciones realizadas</p>
                {dashboard.last_assessment && (
                  <p>Ultima evaluacion: {new Date(dashboard.last_assessment).toLocaleString()}</p>
                )}
              </div>
            </div>
          </div>
          <div className="flex flex-col gap-2">
            {dashboard.active_alerts > 0 && (
              <div className="flex items-center gap-2 px-3 py-2 bg-yellow-50 border border-yellow-200 rounded-lg">
                <BellAlertIcon className="w-5 h-5 text-yellow-600" />
                <span className="text-sm font-medium text-yellow-700">
                  {dashboard.active_alerts} alertas activas
                </span>
              </div>
            )}
            <button
              onClick={handleNewAssessment}
              disabled={loading}
              className="px-4 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition flex items-center gap-2 disabled:opacity-50"
            >
              <AdjustmentsHorizontalIcon className="w-5 h-5" />
              Nueva Evaluacion
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
            {tab.badge > 0 && (
              <span className="ml-1 px-2 py-0.5 text-xs bg-red-100 text-red-600 rounded-full">
                {tab.badge}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'dashboard' && (
        <div>
          {/* Metric Cards */}
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Metricas de Calidad</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4 mb-8">
            <MetricCard metric="completeness" value={dashboard.completeness_avg} trend={getTrend('completeness')} />
            <MetricCard metric="consistency" value={dashboard.consistency_avg} trend={getTrend('consistency')} />
            <MetricCard metric="uniqueness" value={dashboard.uniqueness_avg} trend={getTrend('uniqueness')} />
            <MetricCard metric="validity" value={dashboard.validity_avg} trend={getTrend('validity')} />
            <MetricCard metric="freshness" value={dashboard.freshness_avg} trend={getTrend('freshness')} />
          </div>

          {/* History Chart */}
          <div className="bg-white rounded-xl border p-6 mb-6">
            <h3 className="font-semibold text-gray-900 mb-4">Tendencia de Calidad (Ultimos 7 dias)</h3>
            <div className="grid grid-cols-6 gap-4">
              <div>
                <div className="text-sm text-gray-500 mb-2">General</div>
                <MiniChart data={history} metric="overall" />
              </div>
              <div>
                <div className="text-sm text-gray-500 mb-2">Completitud</div>
                <MiniChart data={history} metric="completeness" />
              </div>
              <div>
                <div className="text-sm text-gray-500 mb-2">Consistencia</div>
                <MiniChart data={history} metric="consistency" />
              </div>
              <div>
                <div className="text-sm text-gray-500 mb-2">Unicidad</div>
                <MiniChart data={history} metric="uniqueness" />
              </div>
              <div>
                <div className="text-sm text-gray-500 mb-2">Validez</div>
                <MiniChart data={history} metric="validity" />
              </div>
              <div>
                <div className="text-sm text-gray-500 mb-2">Frescura</div>
                <MiniChart data={history} metric="freshness" />
              </div>
            </div>
          </div>

          {/* Quick Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-lg border p-4 text-center">
              <div className="text-3xl font-bold text-brand-600">{dashboard.total_companies}</div>
              <div className="text-sm text-gray-500">Empresas</div>
            </div>
            <div className="bg-white rounded-lg border p-4 text-center">
              <div className="text-3xl font-bold text-brand-600">{dashboard.total_records.toLocaleString()}</div>
              <div className="text-sm text-gray-500">Registros Totales</div>
            </div>
            <div className="bg-white rounded-lg border p-4 text-center">
              <div className="text-3xl font-bold text-brand-600">{dashboard.total_assessments}</div>
              <div className="text-sm text-gray-500">Evaluaciones</div>
            </div>
            <div className="bg-white rounded-lg border p-4 text-center">
              <div className={`text-3xl font-bold ${dashboard.active_alerts > 0 ? 'text-yellow-600' : 'text-green-600'}`}>
                {dashboard.active_alerts}
              </div>
              <div className="text-sm text-gray-500">Alertas Activas</div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'companies' && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Calidad por Empresa</h2>
          <div className="bg-white rounded-lg border overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Empresa</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Score</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Completitud</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Consistencia</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Unicidad</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Validez</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Frescura</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Registros</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {dashboard.companies.map((company) => (
                  <CompanyRow key={company.company_id} company={company} />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'alerts' && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Alertas de Calidad</h2>
            <div className="flex gap-2">
              <select className="px-3 py-2 border rounded-lg text-sm">
                <option value="">Todas las severidades</option>
                <option value="warning">Advertencia</option>
                <option value="critical">Critico</option>
              </select>
              <select className="px-3 py-2 border rounded-lg text-sm">
                <option value="">Todos los estados</option>
                <option value="active">Activas</option>
                <option value="acknowledged">Reconocidas</option>
                <option value="resolved">Resueltas</option>
              </select>
            </div>
          </div>
          {alerts.length > 0 ? (
            <div className="grid md:grid-cols-2 gap-4">
              {alerts.map((alert) => (
                <AlertCard
                  key={alert.id}
                  alert={alert}
                  onAcknowledge={handleAcknowledgeAlert}
                />
              ))}
            </div>
          ) : (
            <div className="bg-white rounded-lg border p-8 text-center">
              <CheckCircleIcon className="w-12 h-12 text-green-500 mx-auto mb-3" />
              <p className="text-gray-600">No hay alertas activas</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'rules' && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Reglas de Calidad</h2>
            <button className="px-4 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition flex items-center gap-2">
              <Cog6ToothIcon className="w-5 h-5" />
              Nueva Regla
            </button>
          </div>
          <div className="bg-white rounded-lg border overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Metrica</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Umbral Advertencia</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Umbral Critico</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Habilitada</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {rules.map((rule) => (
                  <RuleRow key={rule.id} rule={rule} onToggle={handleToggleRule} />
                ))}
              </tbody>
            </table>
          </div>
          <div className="mt-4 bg-blue-50 rounded-lg p-4">
            <p className="text-sm text-blue-800">
              Las alertas se generan cuando una metrica cae por debajo del umbral configurado.
              El umbral de advertencia genera una alerta de severidad baja, mientras que el umbral critico genera una alerta de alta severidad.
            </p>
          </div>
        </div>
      )}

      {/* Info Section */}
      <div className="mt-8 bg-blue-50 rounded-lg p-6">
        <h3 className="font-semibold text-blue-900 mb-2">Sobre Data Quality Score</h3>
        <p className="text-blue-800 text-sm mb-4">
          Las metricas de calidad se calculan sobre metadatos de los datos encriptados, sin acceder nunca al contenido real.
          Esto permite evaluar la calidad de los datos preservando la privacidad total mediante FHE (Fully Homomorphic Encryption).
        </p>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {Object.entries(MetricConfig).map(([key, config]) => (
            <div key={key} className="text-center">
              <config.icon className={`w-8 h-8 mx-auto ${config.textColor}`} />
              <div className="text-sm font-medium text-blue-900 mt-1">{config.name}</div>
              <div className="text-xs text-blue-700">{config.description}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
