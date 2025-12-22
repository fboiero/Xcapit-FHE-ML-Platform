import { useState, useEffect } from 'react'
import {
  LockClosedIcon,
  ServerIcon,
  ShieldCheckIcon,
  EyeSlashIcon,
  ArrowRightIcon,
  PlayIcon,
  CheckCircleIcon,
  BuildingOffice2Icon,
  ExclamationTriangleIcon,
  ChartBarIcon,
  CpuChipIcon,
  ArrowPathIcon,
  UserGroupIcon,
  ShoppingBagIcon,
  HeartIcon,
  ScaleIcon,
  SparklesIcon,
  ArrowTrendingDownIcon,
  GiftIcon
} from '@heroicons/react/24/outline'

// Retailer configuration
const RETAILERS = {
  norte: {
    name: 'Retail Norte',
    shortName: 'Norte',
    region: 'Buenos Aires',
    records: 4000,
    churnRate: '18.2%',
    patterns: ['Low frequency + High recency', 'Multiple complaints', 'No loyalty program'],
    baseAccuracy: 72,
    borderColor: 'border-indigo-500',
    bgColor: 'bg-indigo-50',
    textColor: 'text-indigo-600',
    logoColor: 'bg-indigo-600',
    barColor: 'bg-indigo-500',
    gradientFrom: 'from-indigo-500',
    gradientTo: 'to-indigo-600',
  },
  centro: {
    name: 'Retail Centro',
    shortName: 'Centro',
    region: 'Cordoba',
    records: 3000,
    churnRate: '17.5%',
    patterns: ['Declining purchase frequency', 'High returns', 'Price sensitivity'],
    baseAccuracy: 69,
    borderColor: 'border-teal-500',
    bgColor: 'bg-teal-50',
    textColor: 'text-teal-600',
    logoColor: 'bg-teal-600',
    barColor: 'bg-teal-500',
    gradientFrom: 'from-teal-500',
    gradientTo: 'to-teal-600',
  },
  sur: {
    name: 'Retail Sur',
    shortName: 'Sur',
    region: 'Patagonia',
    records: 3000,
    churnRate: '19.1%',
    patterns: ['Long recency periods', 'Low engagement', 'Seasonal only purchases'],
    baseAccuracy: 66,
    borderColor: 'border-violet-500',
    bgColor: 'bg-violet-50',
    textColor: 'text-violet-600',
    logoColor: 'bg-violet-600',
    barColor: 'bg-violet-500',
    gradientFrom: 'from-violet-500',
    gradientTo: 'to-violet-600',
  }
}

// Generate random ciphertext for display
const generateCiphertext = (length = 64) => {
  const chars = '0123456789abcdef'
  return Array.from({ length }, () => chars[Math.floor(Math.random() * chars.length)]).join('')
}

// Sample customer data
const SAMPLE_CUSTOMERS = {
  norte: [
    { id: 'CUS-N001', tenure: 3, recency: 120, frequency: 2, value: 150, returns: 4, complaints: 3, loyalty: false, churned: true, reason: 'Low engagement + High complaints' },
    { id: 'CUS-N002', tenure: 36, recency: 7, frequency: 28, value: 2800, returns: 1, complaints: 0, loyalty: true, churned: false, reason: null },
    { id: 'CUS-N003', tenure: 6, recency: 90, frequency: 3, value: 180, returns: 5, complaints: 2, loyalty: false, churned: true, reason: 'Multiple returns + Recent inactivity' },
    { id: 'CUS-N004', tenure: 48, recency: 14, frequency: 35, value: 3500, returns: 2, complaints: 0, loyalty: true, churned: false, reason: null },
  ],
  centro: [
    { id: 'CUS-C001', tenure: 4, recency: 150, frequency: 2, value: 95, returns: 3, complaints: 2, loyalty: false, churned: true, reason: 'Very low frequency + High recency' },
    { id: 'CUS-C002', tenure: 24, recency: 5, frequency: 22, value: 1900, returns: 0, complaints: 0, loyalty: true, churned: false, reason: null },
    { id: 'CUS-C003', tenure: 8, recency: 180, frequency: 4, value: 320, returns: 6, complaints: 1, loyalty: false, churned: true, reason: 'High return rate + Long absence' },
    { id: 'CUS-C004', tenure: 60, recency: 3, frequency: 50, value: 5200, returns: 1, complaints: 0, loyalty: true, churned: false, reason: null },
  ],
  sur: [
    { id: 'CUS-S001', tenure: 2, recency: 200, frequency: 1, value: 50, returns: 2, complaints: 4, loyalty: false, churned: true, reason: 'Single purchase + Many complaints' },
    { id: 'CUS-S002', tenure: 30, recency: 10, frequency: 18, value: 1500, returns: 1, complaints: 0, loyalty: true, churned: false, reason: null },
    { id: 'CUS-S003', tenure: 5, recency: 95, frequency: 3, value: 220, returns: 4, complaints: 3, loyalty: false, churned: true, reason: 'Low value + High complaints' },
    { id: 'CUS-S004', tenure: 42, recency: 8, frequency: 40, value: 4100, returns: 2, complaints: 0, loyalty: true, churned: false, reason: null },
  ]
}

// Dataset statistics
const DATASET_STATS = {
  norte: {
    totalCustomers: 4000,
    churnedCustomers: 728,
    avgTenure: 24,
    avgValue: 1850,
    features: ['tenure', 'recency', 'frequency', 'monetary', 'returns', 'complaints', 'loyalty'],
  },
  centro: {
    totalCustomers: 3000,
    churnedCustomers: 525,
    avgTenure: 28,
    avgValue: 2100,
    features: ['tenure', 'recency', 'frequency', 'monetary', 'returns', 'complaints', 'loyalty'],
  },
  sur: {
    totalCustomers: 3000,
    churnedCustomers: 573,
    avgTenure: 22,
    avgValue: 1650,
    features: ['tenure', 'recency', 'frequency', 'monetary', 'returns', 'complaints', 'loyalty'],
  }
}

// At-risk customer for prediction
const AT_RISK_CUSTOMER = {
  id: 'CUS-NEW-001',
  tenure: 6,
  recency: 85,
  frequency: 4,
  value: 280,
  avgOrderValue: 70,
  returns: 5,
  complaints: 3,
  loyalty: false,
  marketingOptIn: false,
  channel: 'store',
  featureVector: [6, 85, 4, 280, 70, 5, 3, 0, 0, 1],
  featureNames: ['tenure_months', 'recency_days', 'frequency', 'monetary', 'avg_order', 'returns', 'complaints', 'loyalty', 'marketing', 'channel_store'],
}

// Step definitions
const STEPS = [
  {
    number: 0,
    title: 'El Problema',
    description: 'Retailers pierden clientes sin entender por que. El churn cuesta millones.',
    icon: ExclamationTriangleIcon,
  },
  {
    number: 1,
    title: 'Consorcio',
    description: 'Tres cadenas de retail unen fuerzas manteniendo sus datos privados.',
    icon: BuildingOffice2Icon,
  },
  {
    number: 2,
    title: 'Datos RFM',
    description: 'Cada retailer contribuye metricas RFM cifradas con CKKS.',
    icon: LockClosedIcon,
  },
  {
    number: 3,
    title: 'Votacion',
    description: 'Votacion commit-reveal para autorizar el modelo.',
    icon: ScaleIcon,
  },
  {
    number: 4,
    title: 'Entrenamiento FHE',
    description: 'Gradient Boosting sobre datos cifrados.',
    icon: ServerIcon,
  },
  {
    number: 5,
    title: 'Prediccion de Churn',
    description: 'Identificar clientes en riesgo antes de perderlos.',
    icon: CpuChipIcon,
  },
  {
    number: 6,
    title: 'Resultados',
    description: 'Metricas finales y estrategias de retencion.',
    icon: SparklesIcon,
  },
]

// Customer Table Component
function CustomerTable({ retailer }) {
  const customers = SAMPLE_CUSTOMERS[retailer]
  const config = RETAILERS[retailer]
  const stats = DATASET_STATS[retailer]

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      <div className={`px-4 py-3 ${config.bgColor} border-b border-gray-200`}>
        <div className="flex justify-between items-center">
          <span className="font-medium text-gray-700">
            Muestra de clientes - {stats.totalCustomers.toLocaleString()} registros
          </span>
          <span className={`text-sm ${config.textColor} font-medium`}>
            {stats.churnedCustomers} churned ({((stats.churnedCustomers/stats.totalCustomers)*100).toFixed(1)}%)
          </span>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-3 py-2 text-left font-medium text-gray-500">ID</th>
              <th className="px-3 py-2 text-left font-medium text-gray-500">Tenure</th>
              <th className="px-3 py-2 text-left font-medium text-gray-500">Recency</th>
              <th className="px-3 py-2 text-left font-medium text-gray-500">Freq</th>
              <th className="px-3 py-2 text-left font-medium text-gray-500">Value</th>
              <th className="px-3 py-2 text-left font-medium text-gray-500">Loyalty</th>
              <th className="px-3 py-2 text-left font-medium text-gray-500">Estado</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {customers.map((customer) => (
              <tr key={customer.id} className={customer.churned ? 'bg-red-50' : ''}>
                <td className="px-3 py-2 font-mono text-xs">{customer.id}</td>
                <td className="px-3 py-2">{customer.tenure}m</td>
                <td className="px-3 py-2">{customer.recency}d</td>
                <td className="px-3 py-2">{customer.frequency}</td>
                <td className="px-3 py-2">${customer.value}</td>
                <td className="px-3 py-2">
                  {customer.loyalty ? (
                    <HeartIcon className="w-4 h-4 text-pink-500" />
                  ) : (
                    <span className="text-gray-400">-</span>
                  )}
                </td>
                <td className="px-3 py-2">
                  {customer.churned ? (
                    <span className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs font-medium">
                      Churned
                    </span>
                  ) : (
                    <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-medium">
                      Activo
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// Retailer Card Component
function RetailerCard({ retailerKey, showEncrypted = false }) {
  const config = RETAILERS[retailerKey]
  const stats = DATASET_STATS[retailerKey]

  return (
    <div className={`rounded-xl border-2 ${config.borderColor} overflow-hidden`}>
      <div className={`${config.bgColor} px-4 py-3 border-b border-gray-200`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 ${config.logoColor} rounded-lg flex items-center justify-center text-white font-bold`}>
              <ShoppingBagIcon className="w-5 h-5" />
            </div>
            <div>
              <div className="font-bold text-gray-900">{config.name}</div>
              <div className="text-sm text-gray-500">{config.region}</div>
            </div>
          </div>
          <div className="text-right">
            <div className={`text-lg font-bold ${config.textColor}`}>{config.records.toLocaleString()}</div>
            <div className="text-xs text-gray-500">clientes</div>
          </div>
        </div>
      </div>

      <div className="p-4 bg-white">
        {!showEncrypted ? (
          <>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <div className="text-xs text-gray-500 uppercase">Churn Rate</div>
                <div className="font-bold text-red-600">{config.churnRate}</div>
              </div>
              <div>
                <div className="text-xs text-gray-500 uppercase">Valor Prom.</div>
                <div className="font-bold text-gray-900">${stats.avgValue}</div>
              </div>
            </div>
            <div className="text-xs text-gray-500 mb-2">Patrones de churn detectados:</div>
            <div className="space-y-1">
              {config.patterns.map((pattern, i) => (
                <div key={i} className="text-xs text-gray-600 flex items-center gap-1">
                  <span className={`w-1.5 h-1.5 ${config.logoColor} rounded-full`} />
                  {pattern}
                </div>
              ))}
            </div>
          </>
        ) : (
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-green-600">
              <LockClosedIcon className="w-4 h-4" />
              <span className="text-sm font-medium">Datos RFM cifrados con CKKS</span>
            </div>
            <div className="bg-gray-900 rounded p-2">
              <div className={`font-mono text-[8px] ${config.textColor} break-all`}>
                {generateCiphertext(80)}...
              </div>
            </div>
            <div className="text-xs text-gray-500">
              Seguridad: 128-bit | Poly degree: 8192
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// Server View Component
function ServerView({ isTraining, trainingProgress }) {
  return (
    <div className="bg-gray-900 rounded-xl p-6 text-white">
      <div className="flex items-center gap-3 mb-4">
        <ServerIcon className="w-6 h-6 text-teal-400" />
        <span className="font-bold">Servidor FHE del Consorcio</span>
      </div>

      <div className="bg-gray-800 rounded-lg p-4 mb-4">
        <div className="text-sm text-gray-400 mb-2">Vista del servidor:</div>
        <div className="space-y-2">
          {Object.keys(RETAILERS).map(key => (
            <div key={key} className="bg-gray-900 rounded p-2">
              <div className={`text-xs ${RETAILERS[key].textColor} mb-1`}>Ciphertext de {RETAILERS[key].name}:</div>
              <div className="font-mono text-[8px] text-gray-400 break-all">
                {generateCiphertext(64)}...
              </div>
            </div>
          ))}
        </div>
      </div>

      {isTraining && (
        <div className="mt-4">
          <div className="flex items-center gap-2 text-teal-400 mb-2">
            <ArrowPathIcon className="w-4 h-4 animate-spin" />
            <span className="text-sm font-medium">Entrenando Gradient Boosting sobre datos cifrados...</span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-3">
            <div
              className="h-full rounded-full bg-gradient-to-r from-teal-500 to-cyan-500 transition-all duration-500"
              style={{ width: `${trainingProgress}%` }}
            />
          </div>
          <div className="text-xs text-gray-400 mt-1">
            Epoch {Math.floor(trainingProgress / 10)}/10 - Optimizando sobre ciphertext
          </div>
        </div>
      )}
    </div>
  )
}

// Accuracy Comparison Component
function AccuracyComparison({ accuracies, consortiumAccuracy, animate = false }) {
  const [displayValues, setDisplayValues] = useState(
    animate ? Object.fromEntries(Object.keys(accuracies).map(k => [k, 0])) : accuracies
  )
  const [displayConsortium, setDisplayConsortium] = useState(animate ? 0 : consortiumAccuracy)

  useEffect(() => {
    if (animate) {
      const timer = setTimeout(() => {
        setDisplayValues(accuracies)
        setDisplayConsortium(consortiumAccuracy)
      }, 300)
      return () => clearTimeout(timer)
    }
  }, [animate, accuracies, consortiumAccuracy])

  const maxValue = 100

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <h3 className="font-bold text-gray-900 text-lg mb-6 flex items-center gap-2">
        <ChartBarIcon className="w-5 h-5 text-teal-600" />
        Comparacion de Accuracy
      </h3>

      <div className="space-y-4">
        {Object.entries(RETAILERS).map(([key, config]) => (
          <div key={key} className="flex items-center gap-4">
            <div className="w-28 text-right text-sm font-medium text-gray-600">{config.name}:</div>
            <div className="flex-1 flex items-center gap-3">
              <div className="w-full max-w-md bg-gray-100 rounded-full h-7 relative overflow-hidden">
                <div
                  className={`h-full ${config.barColor} rounded-full transition-all duration-1000 ease-out`}
                  style={{ width: `${(displayValues[key] || 0) / maxValue * 100}%` }}
                />
                <div className="absolute inset-0 flex items-center px-3">
                  <span className="text-sm font-bold text-white drop-shadow">{displayValues[key] || 0}%</span>
                </div>
              </div>
            </div>
          </div>
        ))}

        <div className="flex items-center gap-4 pt-2 border-t border-gray-200">
          <div className="w-28 text-right text-sm font-bold text-gray-800">CONSORCIO:</div>
          <div className="flex-1 flex items-center gap-3">
            <div className="w-full max-w-md bg-gray-100 rounded-full h-9 relative overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-teal-500 to-cyan-600 rounded-full transition-all duration-1000 ease-out"
                style={{ width: `${displayConsortium / maxValue * 100}%` }}
              />
              <div className="absolute inset-0 flex items-center px-3">
                <span className="text-sm font-bold text-white drop-shadow">{displayConsortium}%</span>
              </div>
            </div>
            <div className="bg-green-100 text-green-700 px-3 py-1 rounded-full text-sm font-medium whitespace-nowrap">
              +{consortiumAccuracy - Math.max(...Object.values(accuracies))}% mejora
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// Prediction Result Component
function PredictionResult({ probability, isLoading = false }) {
  const isChurn = probability > 0.5
  const confidence = Math.abs(probability - 0.5) * 200

  if (isLoading) {
    return (
      <div className="bg-gray-50 rounded-xl border border-gray-200 p-6 text-center">
        <ArrowPathIcon className="w-8 h-8 text-teal-500 animate-spin mx-auto mb-2" />
        <div className="text-gray-600">Analizando comportamiento del cliente...</div>
      </div>
    )
  }

  return (
    <div className={`rounded-xl border-2 p-6 ${isChurn ? 'border-red-500 bg-red-50' : 'border-green-500 bg-green-50'}`}>
      <div className="text-center mb-4">
        <div className={`text-4xl font-bold ${isChurn ? 'text-red-600' : 'text-green-600'}`}>
          {(probability * 100).toFixed(1)}%
        </div>
        <div className="text-lg font-medium text-gray-700">Probabilidad de churn</div>
      </div>

      <div className={`text-center py-3 rounded-lg ${isChurn ? 'bg-red-100' : 'bg-green-100'}`}>
        <div className={`text-xl font-bold ${isChurn ? 'text-red-700' : 'text-green-700'}`}>
          {isChurn ? 'ALTO RIESGO DE CHURN' : 'CLIENTE ESTABLE'}
        </div>
        <div className="text-sm text-gray-600">Confianza: {confidence.toFixed(1)}%</div>
      </div>

      <div className="mt-4 space-y-2">
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <ShieldCheckIcon className="w-4 h-4 text-teal-500" />
          <span>Prediccion realizada sobre datos cifrados</span>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <EyeSlashIcon className="w-4 h-4 text-teal-500" />
          <span>Historial de compras nunca expuesto</span>
        </div>
      </div>
    </div>
  )
}

// Voting Display Component
function VotingDisplay({ phase, votes }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <h3 className="font-bold text-gray-900 text-lg mb-4 flex items-center gap-2">
        <ScaleIcon className="w-5 h-5 text-teal-600" />
        Votacion Commit-Reveal
      </h3>

      <div className="space-y-4">
        {Object.entries(RETAILERS).map(([key, config]) => (
          <div key={key} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-3">
              <div className={`w-8 h-8 ${config.logoColor} rounded-lg flex items-center justify-center text-white`}>
                <ShoppingBagIcon className="w-4 h-4" />
              </div>
              <span className="font-medium">{config.name}</span>
            </div>
            <div>
              {phase === 'commit' && (
                <div className="flex items-center gap-2">
                  <LockClosedIcon className="w-4 h-4 text-indigo-500" />
                  <span className="text-sm text-indigo-600 font-mono">
                    0x{generateCiphertext(8)}...
                  </span>
                </div>
              )}
              {phase === 'reveal' && votes[key] && (
                <div className="flex items-center gap-2">
                  <CheckCircleIcon className="w-5 h-5 text-green-500" />
                  <span className="text-green-600 font-medium">APRUEBA</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="flex justify-between items-center">
          <span className="text-gray-600">
            {phase === 'commit' ? 'Fase: Commit (votos ocultos)' : 'Fase: Reveal (votos verificados)'}
          </span>
          {phase === 'reveal' && (
            <span className="text-green-600 font-bold">3/3 - APROBADO</span>
          )}
        </div>
      </div>
    </div>
  )
}

// Retention Strategy Component
function RetentionStrategy({ customer, probability }) {
  const strategies = []

  if (probability > 0.7) {
    strategies.push({ icon: GiftIcon, text: 'Oferta exclusiva 30% descuento', priority: 'URGENTE' })
  }
  if (customer.recency > 60) {
    strategies.push({ icon: ShoppingBagIcon, text: 'Campana de reactivacion personalizada', priority: 'ALTA' })
  }
  if (customer.complaints > 2) {
    strategies.push({ icon: HeartIcon, text: 'Contacto de customer success', priority: 'ALTA' })
  }
  if (!customer.loyalty) {
    strategies.push({ icon: HeartIcon, text: 'Invitacion a programa de fidelidad', priority: 'MEDIA' })
  }
  if (customer.returns > 3) {
    strategies.push({ icon: UserGroupIcon, text: 'Revision de calidad de productos', priority: 'MEDIA' })
  }

  return (
    <div className="bg-teal-50 rounded-xl border border-teal-200 p-4">
      <h4 className="font-bold text-gray-900 mb-3 flex items-center gap-2">
        <SparklesIcon className="w-5 h-5 text-teal-600" />
        Estrategias de Retencion Recomendadas
      </h4>
      <div className="space-y-2">
        {strategies.map((strategy, i) => {
          const Icon = strategy.icon
          return (
            <div key={i} className="flex items-center justify-between p-2 bg-white rounded-lg">
              <div className="flex items-center gap-2">
                <Icon className="w-4 h-4 text-teal-600" />
                <span className="text-sm">{strategy.text}</span>
              </div>
              <span className={`text-xs font-medium px-2 py-1 rounded ${
                strategy.priority === 'URGENTE' ? 'bg-red-100 text-red-700' :
                strategy.priority === 'ALTA' ? 'bg-amber-100 text-amber-700' :
                'bg-gray-100 text-gray-600'
              }`}>
                {strategy.priority}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// Main Component
export default function RetailChurnDemo() {
  const [step, setStep] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [trainingProgress, setTrainingProgress] = useState(0)
  const [showPrediction, setShowPrediction] = useState(false)
  const [predictionLoading, setPredictionLoading] = useState(false)
  const [votingPhase, setVotingPhase] = useState('commit')

  // Accuracies
  const individualAccuracies = { norte: 72, centro: 69, sur: 66 }
  const consortiumAccuracy = 88

  // Auto-advance logic
  useEffect(() => {
    if (isPlaying && step < 6) {
      const timer = setTimeout(() => {
        setStep(s => s + 1)
      }, 4000)
      return () => clearTimeout(timer)
    } else if (step === 6) {
      setIsPlaying(false)
    }
  }, [isPlaying, step])

  // Voting phase animation
  useEffect(() => {
    if (step === 3) {
      setVotingPhase('commit')
      const timer = setTimeout(() => {
        setVotingPhase('reveal')
      }, 2000)
      return () => clearTimeout(timer)
    }
  }, [step])

  // Training animation
  useEffect(() => {
    if (step === 4 && trainingProgress < 100) {
      const timer = setInterval(() => {
        setTrainingProgress(p => Math.min(p + 5, 100))
      }, 200)
      return () => clearInterval(timer)
    }
  }, [step, trainingProgress])

  // Reset training progress when leaving step 4
  useEffect(() => {
    if (step !== 4) {
      setTrainingProgress(0)
    }
  }, [step])

  // Prediction animation
  useEffect(() => {
    if (step === 5) {
      setPredictionLoading(true)
      const timer = setTimeout(() => {
        setPredictionLoading(false)
        setShowPrediction(true)
      }, 2000)
      return () => clearTimeout(timer)
    } else {
      setShowPrediction(false)
      setPredictionLoading(false)
    }
  }, [step])

  const handleNextStep = () => {
    if (step < 6) setStep(step + 1)
  }

  const handlePrevStep = () => {
    if (step > 0) setStep(step - 1)
  }

  const handlePlayPause = () => {
    setIsPlaying(!isPlaying)
  }

  const handleReset = () => {
    setStep(0)
    setIsPlaying(false)
    setTrainingProgress(0)
    setShowPrediction(false)
    setVotingPhase('commit')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-600 via-teal-600 to-cyan-600 text-white py-8 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center gap-3 mb-2">
            <ShoppingBagIcon className="w-8 h-8" />
            <h1 className="text-3xl font-bold">Demo: Consorcio Retail - Prediccion de Churn</h1>
          </div>
          <p className="text-indigo-100 text-lg">
            Tres cadenas de retail predicen y previenen la fuga de clientes sin compartir datos
          </p>
        </div>
      </div>

      {/* Progress Steps */}
      <div className="bg-white border-b border-gray-200 py-4 px-6 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <button
                onClick={handlePlayPause}
                className={`px-4 py-2 rounded-lg font-medium flex items-center gap-2 ${
                  isPlaying
                    ? 'bg-red-100 text-red-600 hover:bg-red-200'
                    : 'bg-teal-100 text-teal-600 hover:bg-teal-200'
                }`}
              >
                {isPlaying ? (
                  <>
                    <span className="w-4 h-4 bg-red-600 rounded-sm" />
                    Pausar
                  </>
                ) : (
                  <>
                    <PlayIcon className="w-4 h-4" />
                    Auto-play
                  </>
                )}
              </button>
              <button
                onClick={handleReset}
                className="px-4 py-2 rounded-lg font-medium bg-gray-100 text-gray-600 hover:bg-gray-200"
              >
                Reiniciar
              </button>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handlePrevStep}
                disabled={step === 0}
                className="px-3 py-2 rounded-lg bg-gray-100 text-gray-600 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Anterior
              </button>
              <button
                onClick={handleNextStep}
                disabled={step === 6}
                className="px-3 py-2 rounded-lg bg-teal-600 text-white hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
              >
                Siguiente
                <ArrowRightIcon className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Step indicators */}
          <div className="flex items-center gap-2 overflow-x-auto pb-2">
            {STEPS.map((s, i) => {
              const Icon = s.icon
              const isActive = step === i
              const isCompleted = step > i
              return (
                <button
                  key={i}
                  onClick={() => setStep(i)}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg whitespace-nowrap transition-all ${
                    isActive
                      ? 'bg-teal-100 text-teal-700 ring-2 ring-teal-500'
                      : isCompleted
                      ? 'bg-green-50 text-green-600'
                      : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                  }`}
                >
                  {isCompleted ? (
                    <CheckCircleIcon className="w-5 h-5 text-green-500" />
                  ) : (
                    <Icon className="w-5 h-5" />
                  )}
                  <span className="text-sm font-medium">{s.title}</span>
                </button>
              )
            })}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Step 0: The Problem */}
        {step === 0 && (
          <div className="space-y-8">
            <div className="bg-gradient-to-r from-red-50 to-orange-50 rounded-xl border border-red-200 p-8">
              <div className="flex items-start gap-4">
                <ArrowTrendingDownIcon className="w-12 h-12 text-red-500 flex-shrink-0" />
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">El Costo del Churn en Retail</h2>
                  <p className="text-gray-700 text-lg mb-4">
                    Adquirir un nuevo cliente cuesta <span className="font-bold text-red-600">5-7x mas</span> que retener uno existente.
                    Los retailers pierden millones por no poder predecir que clientes estan por abandonarlos.
                  </p>
                  <div className="grid grid-cols-3 gap-4 mt-6">
                    <div className="bg-white rounded-lg p-4 border border-red-200">
                      <div className="text-red-600 font-bold mb-1">18% promedio</div>
                      <div className="text-sm text-gray-500">Tasa de churn anual en retail</div>
                    </div>
                    <div className="bg-white rounded-lg p-4 border border-red-200">
                      <div className="text-red-600 font-bold mb-1">Datos fragmentados</div>
                      <div className="text-sm text-gray-500">Cada cadena solo ve su parte</div>
                    </div>
                    <div className="bg-white rounded-lg p-4 border border-red-200">
                      <div className="text-red-600 font-bold mb-1">Competencia directa</div>
                      <div className="text-sm text-gray-500">No pueden compartir insights</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-r from-teal-50 to-cyan-50 rounded-xl border border-teal-200 p-8">
              <div className="flex items-start gap-4">
                <ShieldCheckIcon className="w-12 h-12 text-teal-500 flex-shrink-0" />
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">La Solucion: Consorcio FHE</h2>
                  <p className="text-gray-700 text-lg">
                    Con Fully Homomorphic Encryption, los retailers colaboran para predecir churn usando datos <span className="font-bold text-teal-600">CIFRADOS</span>.
                    Nadie ve los datos de los demas, pero todos se benefician del modelo colaborativo.
                  </p>
                  <div className="mt-4 flex items-center gap-6">
                    <div className="flex items-center gap-2">
                      <CheckCircleIcon className="w-5 h-5 text-green-500" />
                      <span>Metricas RFM privadas</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircleIcon className="w-5 h-5 text-green-500" />
                      <span>Prediccion mejorada</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircleIcon className="w-5 h-5 text-green-500" />
                      <span>Estrategias de retencion</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Step 1: Consortium Setup */}
        {step === 1 && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Consorcio de Retailers Argentina</h2>
            <div className="grid grid-cols-3 gap-6">
              {Object.keys(RETAILERS).map(key => (
                <RetailerCard key={key} retailerKey={key} showEncrypted={false} />
              ))}
            </div>
            <div className="bg-teal-50 rounded-xl border border-teal-200 p-6">
              <h3 className="font-bold text-gray-900 mb-4">Datos combinados del consorcio:</h3>
              <div className="grid grid-cols-4 gap-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-teal-600">10,000</div>
                  <div className="text-sm text-gray-500">Total clientes</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-red-600">1,826</div>
                  <div className="text-sm text-gray-500">Clientes churned</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-indigo-600">18.3%</div>
                  <div className="text-sm text-gray-500">Tasa de churn</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-600">$1,867</div>
                  <div className="text-sm text-gray-500">Valor promedio</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Step 2: Encrypted Data */}
        {step === 2 && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Datos RFM Contribuidos (Cifrados con CKKS)</h2>
            <div className="grid grid-cols-3 gap-6">
              {Object.keys(RETAILERS).map(key => (
                <RetailerCard key={key} retailerKey={key} showEncrypted={true} />
              ))}
            </div>
            <div className="bg-gray-900 rounded-xl p-6 text-white">
              <div className="flex items-center gap-2 mb-4">
                <EyeSlashIcon className="w-5 h-5 text-teal-400" />
                <span className="font-medium">El servidor ve SOLO ciphertext (datos RFM protegidos):</span>
              </div>
              <div className="grid grid-cols-3 gap-4">
                {Object.entries(RETAILERS).map(([key, config]) => (
                  <div key={key} className="bg-gray-800 rounded p-3">
                    <div className={`text-xs ${config.textColor} mb-1`}>{config.name}:</div>
                    <div className="font-mono text-[7px] text-gray-400 break-all">
                      {generateCiphertext(100)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Step 3: Voting */}
        {step === 3 && (
          <div className="grid grid-cols-2 gap-8">
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-gray-900">Votacion para Entrenamiento</h2>
              <div className="bg-teal-50 rounded-xl border border-teal-200 p-6">
                <h3 className="font-bold text-gray-900 mb-2">Propuesta #001</h3>
                <p className="text-gray-700 mb-4">
                  Entrenar modelo Gradient Boosting de prediccion de churn con datos RFM cifrados de los 3 miembros.
                </p>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Quorum requerido:</span>
                    <span className="font-bold ml-2">51%</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Fecha limite:</span>
                    <span className="font-bold ml-2">24h</span>
                  </div>
                </div>
              </div>
              <VotingDisplay phase={votingPhase} votes={{ norte: true, centro: true, sur: true }} />
            </div>
            <div className="space-y-6">
              <h3 className="font-bold text-gray-900 text-lg">Proceso Commit-Reveal</h3>
              <div className="space-y-4">
                <div className={`p-4 rounded-lg border-2 ${votingPhase === 'commit' ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200 bg-gray-50'}`}>
                  <div className="flex items-center gap-2 mb-2">
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center ${votingPhase === 'commit' ? 'bg-indigo-500 text-white' : 'bg-gray-300 text-gray-600'}`}>1</div>
                    <span className="font-bold">Fase Commit</span>
                  </div>
                  <p className="text-sm text-gray-600 ml-8">
                    Cada retailer envia un hash de su voto. Nadie puede ver como votaron los demas.
                  </p>
                </div>
                <div className={`p-4 rounded-lg border-2 ${votingPhase === 'reveal' ? 'border-green-500 bg-green-50' : 'border-gray-200 bg-gray-50'}`}>
                  <div className="flex items-center gap-2 mb-2">
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center ${votingPhase === 'reveal' ? 'bg-green-500 text-white' : 'bg-gray-300 text-gray-600'}`}>2</div>
                    <span className="font-bold">Fase Reveal</span>
                  </div>
                  <p className="text-sm text-gray-600 ml-8">
                    Los votos se revelan y verifican. Resultado inmutable en blockchain.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Step 4: Training */}
        {step === 4 && (
          <div className="grid grid-cols-2 gap-8">
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-gray-900">Entrenamiento sobre Datos Cifrados</h2>
              <ServerView isTraining={trainingProgress < 100} trainingProgress={trainingProgress} />
            </div>
            <div className="space-y-6">
              <div className="bg-teal-50 rounded-xl border border-teal-200 p-6">
                <h3 className="font-bold text-gray-900 mb-4">Configuracion del Modelo</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Algoritmo:</span>
                    <span className="font-medium">Gradient Boosting Classifier</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Estimadores:</span>
                    <span className="font-medium">100</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Learning rate:</span>
                    <span className="font-medium">0.1</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Esquema FHE:</span>
                    <span className="font-medium">CKKS 128-bit</span>
                  </div>
                </div>
              </div>
              {trainingProgress === 100 && (
                <div className="bg-green-50 rounded-xl border border-green-200 p-6">
                  <div className="flex items-center gap-2 text-green-600 mb-2">
                    <CheckCircleIcon className="w-6 h-6" />
                    <span className="font-bold">Entrenamiento Completado</span>
                  </div>
                  <p className="text-gray-600">
                    El modelo fue entrenado exitosamente sobre 10,000 perfiles de clientes cifrados.
                    Los datos de compras nunca fueron expuestos.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Step 5: Prediction */}
        {step === 5 && (
          <div className="grid grid-cols-2 gap-8">
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-gray-900">Analisis de Cliente en Riesgo</h2>
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <UserGroupIcon className="w-5 h-5 text-teal-600" />
                  Cliente: {AT_RISK_CUSTOMER.id}
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <span className="text-xs text-gray-500 uppercase">Antiguedad</span>
                    <div className="font-bold">{AT_RISK_CUSTOMER.tenure} meses</div>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500 uppercase">Ultima compra</span>
                    <div className="font-bold text-red-600">{AT_RISK_CUSTOMER.recency} dias</div>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500 uppercase">Frecuencia</span>
                    <div className="font-bold text-red-600">{AT_RISK_CUSTOMER.frequency} compras</div>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500 uppercase">Valor total</span>
                    <div className="font-bold">${AT_RISK_CUSTOMER.value}</div>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500 uppercase">Devoluciones</span>
                    <div className="font-bold text-red-600">{AT_RISK_CUSTOMER.returns}</div>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500 uppercase">Quejas</span>
                    <div className="font-bold text-red-600">{AT_RISK_CUSTOMER.complaints}</div>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500 uppercase">Programa fidelidad</span>
                    <div className="font-bold text-red-600">No</div>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500 uppercase">Marketing</span>
                    <div className="font-bold text-red-600">Opt-out</div>
                  </div>
                </div>
              </div>
              <div className="bg-gray-900 rounded-xl p-4 text-white">
                <div className="text-sm text-gray-400 mb-2">Vector RFM cifrado:</div>
                <div className="font-mono text-xs text-teal-400 break-all">
                  {generateCiphertext(128)}
                </div>
              </div>
            </div>
            <div className="space-y-6">
              <h3 className="font-bold text-gray-900 text-lg">Resultado del Modelo</h3>
              <PredictionResult probability={0.82} isLoading={predictionLoading} />
              {showPrediction && (
                <RetentionStrategy customer={AT_RISK_CUSTOMER} probability={0.82} />
              )}
            </div>
          </div>
        )}

        {/* Step 6: Results */}
        {step === 6 && (
          <div className="space-y-8">
            <h2 className="text-2xl font-bold text-gray-900">Resultados: Individual vs Consorcio</h2>
            <AccuracyComparison
              accuracies={individualAccuracies}
              consortiumAccuracy={consortiumAccuracy}
              animate={true}
            />
            <div className="grid grid-cols-3 gap-6">
              <div className="bg-green-50 rounded-xl border border-green-200 p-6 text-center">
                <div className="text-4xl font-bold text-green-600 mb-2">+16%</div>
                <div className="text-gray-700 font-medium">Mejora en prediccion</div>
                <div className="text-sm text-gray-500">vs mejor modelo individual</div>
              </div>
              <div className="bg-teal-50 rounded-xl border border-teal-200 p-6 text-center">
                <div className="text-4xl font-bold text-teal-600 mb-2">~30%</div>
                <div className="text-gray-700 font-medium">Clientes retenibles</div>
                <div className="text-sm text-gray-500">Con estrategias personalizadas</div>
              </div>
              <div className="bg-indigo-50 rounded-xl border border-indigo-200 p-6 text-center">
                <div className="text-4xl font-bold text-indigo-600 mb-2">$2.5M</div>
                <div className="text-gray-700 font-medium">Potencial ahorro anual</div>
                <div className="text-sm text-gray-500">Por retailer estimado</div>
              </div>
            </div>
            <div className="bg-gradient-to-r from-teal-50 to-cyan-50 rounded-xl border border-teal-200 p-6">
              <h3 className="font-bold text-gray-900 mb-4">Resumen de Privacidad</h3>
              <div className="grid grid-cols-2 gap-6">
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <CheckCircleIcon className="w-5 h-5 text-green-500" />
                    <span>Historial de compras nunca compartido</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircleIcon className="w-5 h-5 text-green-500" />
                    <span>Metricas RFM cifradas con CKKS</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircleIcon className="w-5 h-5 text-green-500" />
                    <span>Votacion commit-reveal verificable</span>
                  </div>
                </div>
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <CheckCircleIcon className="w-5 h-5 text-green-500" />
                    <span>Audit trail en Arbitrum blockchain</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircleIcon className="w-5 h-5 text-green-500" />
                    <span>Cumplimiento Ley 25.326 (Argentina)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircleIcon className="w-5 h-5 text-green-500" />
                    <span>Cada retailer controla sus datos</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
