import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import {
  ChartBarIcon,
  ClockIcon,
  ShieldCheckIcon,
  UserGroupIcon,
  CubeIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  DocumentTextIcon,
  ArrowTrendingUpIcon,
  BeakerIcon
} from '@heroicons/react/24/outline'

// Animated counter hook
function useCounter(end, duration = 1500, startOnMount = true) {
  const [count, setCount] = useState(0)

  useEffect(() => {
    if (!startOnMount || !end) return
    let startTime = null
    const endValue = parseFloat(end) || 0

    const animate = (timestamp) => {
      if (!startTime) startTime = timestamp
      const progress = Math.min((timestamp - startTime) / duration, 1)
      setCount(progress * endValue)
      if (progress < 1) requestAnimationFrame(animate)
    }
    requestAnimationFrame(animate)
  }, [end, duration, startOnMount])

  return count
}

// Metric bar component
function MetricBar({ label, value, maxValue = 1, color = 'brand' }) {
  const percentage = (value / maxValue) * 100
  const animatedValue = useCounter(value, 1200, true)

  const colorClasses = {
    brand: 'bg-gradient-to-r from-brand-500 to-brand-600',
    green: 'bg-gradient-to-r from-green-500 to-emerald-600',
    blue: 'bg-gradient-to-r from-blue-500 to-indigo-600',
    amber: 'bg-gradient-to-r from-amber-500 to-orange-600',
    purple: 'bg-gradient-to-r from-purple-500 to-violet-600',
    red: 'bg-gradient-to-r from-red-500 to-rose-600'
  }

  return (
    <div className="mb-4">
      <div className="flex justify-between items-center mb-1">
        <span className="text-sm font-medium text-slate-700">{label}</span>
        <span className="text-sm font-bold text-slate-900">{(animatedValue * 100).toFixed(2)}%</span>
      </div>
      <div className="w-full bg-slate-200 rounded-full h-3 overflow-hidden">
        <div
          className={`h-3 rounded-full transition-all duration-1000 ease-out ${colorClasses[color]}`}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
    </div>
  )
}

// Stat card component
function StatCard({ icon: Icon, label, value, subtitle, color = 'brand' }) {
  const colorClasses = {
    brand: 'bg-brand-50 text-brand-600',
    green: 'bg-green-50 text-green-600',
    blue: 'bg-blue-50 text-blue-600',
    amber: 'bg-amber-50 text-amber-600',
    purple: 'bg-purple-50 text-purple-600'
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 hover:shadow-lg hover:border-brand-200 transition-all duration-300">
      <div className="flex items-start justify-between">
        <div className={`p-2 rounded-lg ${colorClasses[color]}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
      <div className="mt-3">
        <p className="text-2xl font-bold text-slate-900">{value}</p>
        <p className="text-sm text-slate-500">{label}</p>
        {subtitle && <p className="text-xs text-slate-400 mt-1">{subtitle}</p>}
      </div>
    </div>
  )
}

// Coefficient bar component
function CoefficientBar({ name, value, maxAbsValue }) {
  const percentage = (Math.abs(value) / maxAbsValue) * 50
  const isPositive = value >= 0

  return (
    <div className="flex items-center gap-3 py-2">
      <div className="w-32 text-right">
        <span className="text-sm font-medium text-slate-600">{name}</span>
      </div>
      <div className="flex-1 flex items-center">
        <div className="w-1/2 flex justify-end">
          {!isPositive && (
            <div
              className="h-6 bg-gradient-to-l from-red-400 to-red-500 rounded-l-md transition-all duration-700"
              style={{ width: `${percentage}%` }}
            />
          )}
        </div>
        <div className="w-px h-8 bg-slate-300" />
        <div className="w-1/2">
          {isPositive && (
            <div
              className="h-6 bg-gradient-to-r from-green-400 to-green-500 rounded-r-md transition-all duration-700"
              style={{ width: `${percentage}%` }}
            />
          )}
        </div>
      </div>
      <div className="w-20 text-left">
        <span className={`text-sm font-mono ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
          {isPositive ? '+' : ''}{value.toFixed(4)}
        </span>
      </div>
    </div>
  )
}

// Timeline step component
function TimelineStep({ step, isLast }) {
  return (
    <div className="flex gap-4">
      <div className="flex flex-col items-center">
        <div className="w-8 h-8 bg-brand-100 rounded-full flex items-center justify-center text-brand-600 font-bold text-sm">
          {step.step}
        </div>
        {!isLast && <div className="w-0.5 h-full bg-brand-200 my-1" />}
      </div>
      <div className="pb-6 flex-1">
        <div className="flex items-center justify-between">
          <h4 className="font-medium text-slate-900 capitalize">
            {step.action.replace(/_/g, ' ')}
          </h4>
          <span className="text-xs text-slate-400">+{step.elapsed_ms}ms</span>
        </div>
        <p className="text-sm text-slate-500 mt-1">
          {step.timestamp.split('T')[1].split('.')[0]}
        </p>
        {step.details && Object.keys(step.details).length > 0 && (
          <div className="mt-2 bg-slate-50 rounded-lg p-3 text-xs font-mono">
            {Object.entries(step.details).slice(0, 4).map(([key, val]) => (
              <div key={key} className="flex justify-between">
                <span className="text-slate-500">{key}:</span>
                <span className="text-slate-700">{typeof val === 'number' ? val.toLocaleString() : String(val)}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default function ModelMetrics() {
  const { t } = useTranslation()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    fetch('/data/consortium_evidence.json')
      .then(res => {
        if (!res.ok) throw new Error('Failed to load metrics data')
        return res.json()
      })
      .then(setData)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-slate-200 rounded w-1/3" />
          <div className="grid grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-32 bg-slate-200 rounded-xl" />
            ))}
          </div>
          <div className="h-64 bg-slate-200 rounded-xl" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
          <ExclamationTriangleIcon className="w-12 h-12 text-red-400 mx-auto mb-3" />
          <h3 className="text-lg font-medium text-red-800">Error Loading Metrics</h3>
          <p className="text-red-600 mt-1">{error}</p>
        </div>
      </div>
    )
  }

  const metrics = data.calculated_metrics
  const model = data.model
  const coefficients = model.coefficients
  const maxAbsCoef = Math.max(...Object.values(coefficients).map(Math.abs))

  const tabs = [
    { id: 'overview', label: 'Resumen', icon: ChartBarIcon },
    { id: 'model', label: 'Modelo', icon: CubeIcon },
    { id: 'timeline', label: 'Timeline', icon: ClockIcon },
    { id: 'contributions', label: 'Contribuciones', icon: UserGroupIcon },
  ]

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 bg-gradient-to-br from-brand-500 to-purple-600 rounded-xl text-white">
            <BeakerIcon className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Métricas del Modelo</h1>
            <p className="text-slate-500">Consorcio: {data.consortium}</p>
          </div>
        </div>
        <div className="flex items-center gap-4 mt-4">
          <span className="inline-flex items-center gap-1 px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm">
            <CheckCircleIcon className="w-4 h-4" />
            Valores Calculados
          </span>
          <span className="text-sm text-slate-500">
            Ejecutado: {new Date(data.execution_timestamp).toLocaleString()}
          </span>
          <span className="text-sm text-slate-500">
            Duración: {data.execution_duration_ms}ms
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b border-slate-200 pb-2">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
              activeTab === tab.id
                ? 'bg-brand-100 text-brand-700 font-medium'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Stats Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard
              icon={DocumentTextIcon}
              label="Total Registros"
              value={data.total_records.toLocaleString()}
              subtitle={`${data.total_fraud_cases.toLocaleString()} fraudes (${(data.fraud_rate * 100).toFixed(2)}%)`}
              color="blue"
            />
            <StatCard
              icon={UserGroupIcon}
              label="Miembros"
              value={data.members.length}
              subtitle={data.members.join(', ').substring(0, 30) + '...'}
              color="purple"
            />
            <StatCard
              icon={ArrowTrendingUpIcon}
              label="AUC-ROC"
              value={metrics['AUC-ROC'].toFixed(4)}
              subtitle="Capacidad discriminativa"
              color="green"
            />
            <StatCard
              icon={ShieldCheckIcon}
              label="Seguridad FHE"
              value={model.security_level}
              subtitle="CKKS Encryption"
              color="amber"
            />
          </div>

          {/* Metrics Chart */}
          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <h3 className="text-lg font-semibold text-slate-900 mb-6 flex items-center gap-2">
              <ChartBarIcon className="w-5 h-5 text-brand-500" />
              Métricas del Modelo (Valores Reales)
            </h3>
            <div className="max-w-2xl">
              <MetricBar label="Accuracy" value={metrics['Accuracy']} color="blue" />
              <MetricBar label="Precision" value={metrics['Precision']} color="amber" />
              <MetricBar label="Recall" value={metrics['Recall']} color="green" />
              <MetricBar label="F1-Score" value={metrics['F1-Score']} color="purple" />
              <MetricBar label="AUC-ROC" value={metrics['AUC-ROC']} color="brand" />
            </div>
            <div className="mt-6 p-4 bg-slate-50 rounded-lg">
              <h4 className="text-sm font-medium text-slate-700 mb-2">Interpretación</h4>
              <ul className="text-sm text-slate-600 space-y-1">
                <li>• <strong>Recall alto (67.48%)</strong>: Detecta la mayoría de los fraudes reales</li>
                <li>• <strong>Precision bajo (5.89%)</strong>: Muchas alertas son falsos positivos</li>
                <li>• <strong>AUC-ROC (0.6617)</strong>: El modelo tiene capacidad discriminativa moderada</li>
              </ul>
            </div>
          </div>

          {/* Predictions */}
          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Predicciones en Batch de Prueba</h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-4 bg-slate-50 rounded-lg">
                <p className="text-3xl font-bold text-slate-900">{data.predictions.batch_size.toLocaleString()}</p>
                <p className="text-sm text-slate-500">Transacciones evaluadas</p>
              </div>
              <div className="text-center p-4 bg-red-50 rounded-lg">
                <p className="text-3xl font-bold text-red-600">{data.predictions.fraud_detected}</p>
                <p className="text-sm text-slate-500">Fraudes detectados ({(data.predictions.fraud_rate * 100).toFixed(1)}%)</p>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <p className="text-3xl font-bold text-green-600">{data.predictions.batch_size - data.predictions.fraud_detected}</p>
                <p className="text-sm text-slate-500">Transacciones legítimas</p>
              </div>
            </div>

            {/* Confidence Distribution */}
            <div className="mt-6">
              <h4 className="text-sm font-medium text-slate-700 mb-3">Distribución por Confianza</h4>
              <div className="flex gap-2">
                <div className="flex-1 bg-green-100 rounded-lg p-3 text-center">
                  <p className="text-xl font-bold text-green-700">{data.predictions.confidence_distribution.high}</p>
                  <p className="text-xs text-green-600">Alta (&gt;80%)</p>
                </div>
                <div className="flex-1 bg-amber-100 rounded-lg p-3 text-center">
                  <p className="text-xl font-bold text-amber-700">{data.predictions.confidence_distribution.medium}</p>
                  <p className="text-xs text-amber-600">Media (50-80%)</p>
                </div>
                <div className="flex-1 bg-slate-100 rounded-lg p-3 text-center">
                  <p className="text-xl font-bold text-slate-700">{data.predictions.confidence_distribution.low}</p>
                  <p className="text-xs text-slate-600">Baja (30-50%)</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Model Tab */}
      {activeTab === 'model' && (
        <div className="space-y-6">
          {/* Model Info */}
          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
              <CubeIcon className="w-5 h-5 text-brand-500" />
              Información del Modelo
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-slate-500">Tipo</p>
                <p className="font-medium text-slate-900">{model.type}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Solver</p>
                <p className="font-medium text-slate-900">{model.parameters.solver}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Iteraciones</p>
                <p className="font-medium text-slate-900">{model.n_iterations}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Class Weight</p>
                <p className="font-medium text-slate-900">{model.parameters.class_weight}</p>
              </div>
            </div>
            <div className="mt-4 p-3 bg-slate-50 rounded-lg">
              <p className="text-sm text-slate-500">Model Hash</p>
              <p className="font-mono text-sm text-slate-700">{model.hash}</p>
            </div>
          </div>

          {/* Coefficients */}
          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <h3 className="text-lg font-semibold text-slate-900 mb-2">Coeficientes del Modelo</h3>
            <p className="text-sm text-slate-500 mb-6">
              Valores negativos (rojo) reducen probabilidad de fraude, positivos (verde) la aumentan
            </p>
            <div className="space-y-1">
              {Object.entries(coefficients).map(([name, value]) => (
                <CoefficientBar key={name} name={name} value={value} maxAbsValue={maxAbsCoef} />
              ))}
            </div>
            <div className="mt-4 flex items-center justify-center gap-2 text-sm text-slate-500">
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 bg-red-400 rounded" /> Reduce riesgo
              </div>
              <div className="w-px h-4 bg-slate-300" />
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 bg-green-400 rounded" /> Aumenta riesgo
              </div>
            </div>
            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <h4 className="text-sm font-medium text-blue-700 mb-2">Insights</h4>
              <ul className="text-sm text-blue-600 space-y-1">
                <li>• <strong>hour (-0.43)</strong>: Transacciones en horas tempranas tienen mayor riesgo</li>
                <li>• <strong>is_international (+0.20)</strong>: Transacciones internacionales aumentan el riesgo</li>
                <li>• <strong>amount (+0.15)</strong>: Montos más altos están asociados con más fraude</li>
              </ul>
            </div>
          </div>

          {/* Intercept */}
          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Intercepto</h3>
            <p className="text-3xl font-mono text-slate-700">{model.intercept.toFixed(6)}</p>
            <p className="text-sm text-slate-500 mt-2">
              Sesgo base del modelo antes de considerar las características
            </p>
          </div>
        </div>
      )}

      {/* Timeline Tab */}
      {activeTab === 'timeline' && (
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-6 flex items-center gap-2">
            <ClockIcon className="w-5 h-5 text-brand-500" />
            Log de Ejecución
          </h3>
          <div className="relative">
            {data.execution_log.map((step, idx) => (
              <TimelineStep
                key={step.step}
                step={step}
                isLast={idx === data.execution_log.length - 1}
              />
            ))}
          </div>
          <div className="mt-4 p-4 bg-green-50 rounded-lg flex items-center gap-3">
            <CheckCircleIcon className="w-6 h-6 text-green-600" />
            <div>
              <p className="font-medium text-green-800">Ejecución Completada</p>
              <p className="text-sm text-green-600">
                Duración total: {data.execution_duration_ms}ms |
                {data.execution_log.length} pasos ejecutados
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Contributions Tab */}
      {activeTab === 'contributions' && (
        <div className="space-y-6">
          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <h3 className="text-lg font-semibold text-slate-900 mb-6 flex items-center gap-2">
              <UserGroupIcon className="w-5 h-5 text-brand-500" />
              Contribuciones por Banco
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-500">Banco</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-slate-500">Registros</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-slate-500">Fraudes</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-slate-500">Tasa</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-500">Hash</th>
                    <th className="text-center py-3 px-4 text-sm font-medium text-slate-500">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {data.contributions.map((contrib, idx) => (
                    <tr key={contrib.id} className="border-b border-slate-100 hover:bg-slate-50">
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-white font-bold text-sm ${
                            ['bg-blue-500', 'bg-purple-500', 'bg-green-500', 'bg-amber-500'][idx % 4]
                          }`}>
                            {contrib.bank.charAt(0)}
                          </div>
                          <span className="font-medium text-slate-900">{contrib.bank}</span>
                        </div>
                      </td>
                      <td className="py-3 px-4 text-right font-mono text-slate-700">
                        {contrib.records.toLocaleString()}
                      </td>
                      <td className="py-3 px-4 text-right font-mono text-red-600">
                        {contrib.fraud_cases.toLocaleString()}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <span className="px-2 py-1 bg-slate-100 rounded text-sm font-mono">
                          {(contrib.fraud_rate * 100).toFixed(2)}%
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <code className="text-xs bg-slate-100 px-2 py-1 rounded text-slate-600">
                          {contrib.hash}
                        </code>
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs">
                          <CheckCircleIcon className="w-3 h-3" />
                          {contrib.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="bg-slate-50 font-medium">
                    <td className="py-3 px-4 text-slate-900">Total</td>
                    <td className="py-3 px-4 text-right font-mono text-slate-900">
                      {data.total_records.toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-red-600">
                      {data.total_fraud_cases.toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <span className="px-2 py-1 bg-slate-200 rounded text-sm font-mono">
                        {(data.fraud_rate * 100).toFixed(2)}%
                      </span>
                    </td>
                    <td colSpan="2" className="py-3 px-4 text-slate-500 text-sm">
                      4 contribuciones verificadas
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>

          {/* Verification */}
          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
              <ShieldCheckIcon className="w-5 h-5 text-green-500" />
              Verificación de Seguridad
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 bg-green-50 rounded-lg text-center">
                <CheckCircleIcon className="w-8 h-8 text-green-500 mx-auto mb-2" />
                <p className="text-sm font-medium text-green-800">Datos Encriptados</p>
                <p className="text-xs text-green-600">{data.verification.fhe_scheme}</p>
              </div>
              <div className="p-4 bg-green-50 rounded-lg text-center">
                <CheckCircleIcon className="w-8 h-8 text-green-500 mx-auto mb-2" />
                <p className="text-sm font-medium text-green-800">Nunca Desencriptados</p>
                <p className="text-xs text-green-600">Privacy preserved</p>
              </div>
              <div className="p-4 bg-blue-50 rounded-lg text-center">
                <ShieldCheckIcon className="w-8 h-8 text-blue-500 mx-auto mb-2" />
                <p className="text-sm font-medium text-blue-800">Compliance</p>
                <p className="text-xs text-blue-600">{data.verification.compliance.join(', ')}</p>
              </div>
              <div className="p-4 bg-purple-50 rounded-lg text-center">
                <CubeIcon className="w-8 h-8 text-purple-500 mx-auto mb-2" />
                <p className="text-sm font-medium text-purple-800">Seguridad FHE</p>
                <p className="text-xs text-purple-600">{model.security_level}</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
