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
  BanknotesIcon,
  ClockIcon,
  GlobeAltIcon,
  MapPinIcon,
  SparklesIcon
} from '@heroicons/react/24/outline'

// Bank configuration
const BANKS = {
  bankA: {
    name: 'Banco A',
    shortName: 'A',
    records: 5000,
    fraudRate: '4.2%',
    patterns: ['Late-night + high value', 'Rapid velocity (>5 txn/hr)', 'Online + international'],
    baseAccuracy: 72,
    borderColor: 'border-blue-500',
    bgColor: 'bg-blue-50',
    textColor: 'text-blue-600',
    logoColor: 'bg-blue-600',
    barColor: 'bg-blue-500',
    gradientFrom: 'from-blue-500',
    gradientTo: 'to-blue-600',
  },
  bankB: {
    name: 'Banco B',
    shortName: 'B',
    records: 3000,
    fraudRate: '3.8%',
    patterns: ['Travel + unusual distance', 'Gas station + high amount', 'Weekend + multiple merchants'],
    baseAccuracy: 68,
    borderColor: 'border-emerald-500',
    bgColor: 'bg-emerald-50',
    textColor: 'text-emerald-600',
    logoColor: 'bg-emerald-600',
    barColor: 'bg-emerald-500',
    gradientFrom: 'from-emerald-500',
    gradientTo: 'to-emerald-600',
  }
}

// Generate random ciphertext for display
const generateCiphertext = (length = 64) => {
  const chars = '0123456789abcdef'
  return Array.from({ length }, () => chars[Math.floor(Math.random() * chars.length)]).join('')
}

// Realistic sample transaction data with more details
const SAMPLE_TRANSACTIONS = {
  bankA: [
    { id: 'TXN-58847', amount: 2420.00, category: 'Online', merchant: 'Amazon.com', time: '2:15 AM', hour: 2, intl: true, distance: 0, velocity: 6, flagged: true, reason: 'Late night + International + High velocity' },
    { id: 'TXN-58848', amount: 89.50, category: 'Food', merchant: 'Starbucks #1842', time: '12:30 PM', hour: 12, intl: false, distance: 2, velocity: 2, flagged: false, reason: null },
    { id: 'TXN-58849', amount: 1850.00, category: 'Online', merchant: 'BestBuy.com', time: '3:45 AM', hour: 3, intl: true, distance: 0, velocity: 8, flagged: true, reason: 'Late night + International + High velocity' },
    { id: 'TXN-58850', amount: 156.00, category: 'Retail', merchant: 'Target Store', time: '6:20 PM', hour: 18, intl: false, distance: 5, velocity: 1, flagged: false, reason: null },
    { id: 'TXN-58851', amount: 3200.00, category: 'Online', merchant: 'Alibaba.com', time: '1:00 AM', hour: 1, intl: true, distance: 0, velocity: 5, flagged: true, reason: 'Late night + International + High velocity' },
    { id: 'TXN-58852', amount: 45.00, category: 'Food', merchant: 'McDonalds', time: '7:30 PM', hour: 19, intl: false, distance: 3, velocity: 2, flagged: false, reason: null },
  ],
  bankB: [
    { id: 'BB-42201', amount: 285.00, category: 'Gas', merchant: 'Shell Station', time: '9:00 AM', hour: 9, intl: false, distance: 120, velocity: 2, flagged: true, reason: 'Gas + High amount + Far from home' },
    { id: 'BB-42202', amount: 89.00, category: 'Food', merchant: 'Olive Garden', time: '1:15 PM', hour: 13, intl: false, distance: 5, velocity: 1, flagged: false, reason: null },
    { id: 'BB-42203', amount: 1450.00, category: 'Travel', merchant: 'Delta Airlines', time: '11:30 AM', hour: 11, intl: false, distance: 250, velocity: 1, flagged: true, reason: 'Travel + Far from home' },
    { id: 'BB-42204', amount: 45.00, category: 'Retail', merchant: 'Walgreens', time: '4:45 PM', hour: 16, intl: false, distance: 8, velocity: 2, flagged: false, reason: null },
    { id: 'BB-42205', amount: 320.00, category: 'Gas', merchant: 'Chevron', time: '6:00 AM', hour: 6, intl: false, distance: 85, velocity: 3, flagged: true, reason: 'Gas + High amount + Far from home' },
    { id: 'BB-42206', amount: 2100.00, category: 'Travel', merchant: 'Marriott Hotel', time: '3:00 PM', hour: 15, intl: false, distance: 180, velocity: 2, flagged: true, reason: 'Travel + Far from home' },
  ]
}

// Dataset statistics
const DATASET_STATS = {
  bankA: {
    totalTransactions: 5000,
    fraudCases: 315,
    fraudRate: 6.3,
    avgAmount: 245.50,
    avgVelocity: 3.2,
    intlRate: 15,
    features: ['hour_of_day', 'is_international', 'num_txns_24h', 'amount', 'ratio_to_avg'],
  },
  bankB: {
    totalTransactions: 3000,
    fraudCases: 189,
    fraudRate: 6.3,
    avgAmount: 198.30,
    avgDistance: 28.5,
    gasRate: 12,
    features: ['distance_from_home', 'merchant_category', 'amount', 'day_of_week'],
  }
}

// Suspicious transaction for prediction - with full feature vector
const SUSPICIOUS_TRANSACTION = {
  id: 'TXN-NEW-001',
  amount: 2500.00,
  category: 'Online',
  merchant: 'Unknown Merchant - HK',
  time: '2:00 AM',
  hour: 2,
  isInternational: true,
  distanceFromHome: 0,
  txnsLast24h: 7,
  ratioToAvg: 2.08,
  avgMonthlySpend: 1200,
  // Feature vector for model input
  featureVector: [2500.0, 2, 1, 0, 1200.0, 7, 2.08, 0, 0, 0, 1, 0, 0],
  featureNames: ['amount', 'hour', 'is_intl', 'distance', 'avg_spend', 'velocity', 'ratio', 'cat_food', 'cat_gas', 'cat_retail', 'cat_online', 'cat_travel', 'cat_entertainment'],
}

// Step definitions
const STEPS = [
  {
    number: 0,
    title: 'El Problema',
    description: 'Dos bancos quieren mejorar su deteccion de fraude, pero no pueden compartir datos de clientes.',
    icon: ExclamationTriangleIcon,
  },
  {
    number: 1,
    title: 'Setup',
    description: 'Crear empresas y consorcio con datos sinteticos.',
    icon: BuildingOffice2Icon,
  },
  {
    number: 2,
    title: 'Entrenamiento Individual',
    description: 'Cada banco entrena su modelo con sus propios datos.',
    icon: ChartBarIcon,
  },
  {
    number: 3,
    title: 'Cifrado FHE',
    description: 'Los datos se cifran con CKKS (128-bit security). Los datos nunca salen del banco.',
    icon: LockClosedIcon,
  },
  {
    number: 4,
    title: 'Entrenamiento Consorcio',
    description: 'El servidor entrena sobre datos cifrados sin poder verlos.',
    icon: ServerIcon,
  },
  {
    number: 5,
    title: 'Inferencia Cifrada',
    description: 'Nueva transaccion sospechosa analizada sin exponer datos.',
    icon: CpuChipIcon,
  },
  {
    number: 6,
    title: 'Resultados',
    description: 'Comparacion final: modelos individuales vs consorcio.',
    icon: SparklesIcon,
  },
]

// Progress bar component
function ProgressBar({ value, maxValue, colorClass, label }) {
  const percentage = (value / maxValue) * 100
  return (
    <div className="w-full">
      {label && <div className="text-sm font-medium text-gray-700 mb-1">{label}</div>}
      <div className="w-full bg-gray-200 rounded-full h-6 relative overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-1000 ease-out ${colorClass}`}
          style={{ width: `${percentage}%` }}
        />
        <div className="absolute inset-0 flex items-center justify-center text-sm font-bold text-gray-800">
          {value}%
        </div>
      </div>
    </div>
  )
}

// Detailed data table component
function DataTable({ bank, showFraudReason = false }) {
  const transactions = SAMPLE_TRANSACTIONS[bank]
  const config = BANKS[bank]
  const stats = DATASET_STATS[bank]

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      <div className={`px-4 py-3 ${config.bgColor} border-b border-gray-200`}>
        <div className="flex justify-between items-center">
          <span className="font-medium text-gray-700">Muestra de datos - {stats.totalTransactions.toLocaleString()} registros</span>
          <span className={`text-sm ${config.textColor} font-medium`}>{stats.fraudCases} fraudes ({stats.fraudRate}%)</span>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-3 py-2 text-left font-medium text-gray-500">ID</th>
              <th className="px-3 py-2 text-left font-medium text-gray-500">Monto</th>
              <th className="px-3 py-2 text-left font-medium text-gray-500">Comercio</th>
              <th className="px-3 py-2 text-left font-medium text-gray-500">Hora</th>
              {bank === 'bankA' && <th className="px-3 py-2 text-left font-medium text-gray-500">Intl</th>}
              {bank === 'bankA' && <th className="px-3 py-2 text-left font-medium text-gray-500">Veloc.</th>}
              {bank === 'bankB' && <th className="px-3 py-2 text-left font-medium text-gray-500">Dist.</th>}
              <th className="px-3 py-2 text-left font-medium text-gray-500">Fraude</th>
              {showFraudReason && <th className="px-3 py-2 text-left font-medium text-gray-500">Razon</th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {transactions.map((tx) => (
              <tr key={tx.id} className={tx.flagged ? 'bg-red-50' : 'hover:bg-gray-50'}>
                <td className="px-3 py-2 font-mono text-gray-600">{tx.id}</td>
                <td className="px-3 py-2 font-medium">${tx.amount.toLocaleString()}</td>
                <td className="px-3 py-2 text-gray-600">{tx.merchant}</td>
                <td className="px-3 py-2 text-gray-500">{tx.time}</td>
                {bank === 'bankA' && (
                  <td className="px-3 py-2">
                    {tx.intl ? <span className="text-orange-600 font-medium">Si</span> : <span className="text-gray-400">No</span>}
                  </td>
                )}
                {bank === 'bankA' && (
                  <td className="px-3 py-2">
                    <span className={tx.velocity > 4 ? 'text-red-600 font-medium' : 'text-gray-600'}>{tx.velocity}</span>
                  </td>
                )}
                {bank === 'bankB' && (
                  <td className="px-3 py-2">
                    <span className={tx.distance > 50 ? 'text-red-600 font-medium' : 'text-gray-600'}>{tx.distance} mi</span>
                  </td>
                )}
                <td className="px-3 py-2">
                  {tx.flagged ? (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-red-100 text-red-700 font-medium">
                      <ExclamationTriangleIcon className="w-3 h-3" /> Si
                    </span>
                  ) : (
                    <span className="text-gray-400">No</span>
                  )}
                </td>
                {showFraudReason && (
                  <td className="px-3 py-2 text-gray-500 text-[10px] max-w-[150px] truncate" title={tx.reason}>
                    {tx.reason || '-'}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// Bank card component
function BankCard({ bank, showData = false, showAccuracy = false, accuracy = null, encrypted = false, detailed = false }) {
  const config = BANKS[bank]
  const transactions = SAMPLE_TRANSACTIONS[bank]
  const stats = DATASET_STATS[bank]

  return (
    <div className={`rounded-xl border-2 ${config.borderColor} ${config.bgColor} p-5 transition-all duration-300`}>
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <div className={`w-12 h-12 ${config.logoColor} rounded-full flex items-center justify-center text-white font-bold text-xl`}>
          {config.shortName}
        </div>
        <div>
          <h3 className="font-bold text-gray-900 text-lg">{config.name}</h3>
          <p className="text-sm text-gray-500">{config.records.toLocaleString()} transacciones</p>
        </div>
      </div>

      {/* Detailed Stats */}
      <div className="grid grid-cols-3 gap-2 mb-4">
        <div className="bg-white/60 rounded-lg p-2 text-center">
          <div className="text-lg font-bold text-gray-800">{stats.fraudCases}</div>
          <div className="text-[10px] text-gray-500">Fraudes</div>
        </div>
        <div className="bg-white/60 rounded-lg p-2 text-center">
          <div className="text-lg font-bold text-red-600">{stats.fraudRate}%</div>
          <div className="text-[10px] text-gray-500">Tasa fraude</div>
        </div>
        <div className="bg-white/60 rounded-lg p-2 text-center">
          <div className="text-lg font-bold text-gray-800">${stats.avgAmount}</div>
          <div className="text-[10px] text-gray-500">Monto prom.</div>
        </div>
      </div>

      {/* Fraud patterns */}
      <div className="mb-4">
        <div className="text-xs font-medium text-gray-500 mb-2">Patrones de fraude detectables:</div>
        <div className="space-y-1">
          {config.patterns.map((pattern, i) => (
            <div key={i} className="text-xs bg-white/50 rounded px-2 py-1 flex items-center gap-1">
              <CheckCircleIcon className={`w-3 h-3 ${config.textColor}`} />
              {pattern}
            </div>
          ))}
        </div>
      </div>

      {/* Features used */}
      <div className="mb-4">
        <div className="text-xs font-medium text-gray-500 mb-1">Features principales:</div>
        <div className="flex flex-wrap gap-1">
          {stats.features.map((f, i) => (
            <span key={i} className="text-[10px] bg-gray-200 text-gray-600 px-1.5 py-0.5 rounded font-mono">{f}</span>
          ))}
        </div>
      </div>

      {/* Transaction data - simple view */}
      {showData && !encrypted && !detailed && (
        <div className="mt-4">
          <div className="text-xs font-medium text-gray-500 mb-2">Ultimas transacciones:</div>
          <div className="space-y-1">
            {transactions.slice(0, 4).map((tx) => (
              <div
                key={tx.id}
                className={`text-xs bg-white rounded px-2 py-1.5 flex justify-between items-center ${
                  tx.flagged ? 'border-l-2 border-red-500' : ''
                }`}
              >
                <span className="font-mono text-gray-500">{tx.id}</span>
                <span className="font-medium">${tx.amount.toLocaleString()}</span>
                <span className="text-gray-400 truncate max-w-[80px]">{tx.merchant}</span>
                <span className="text-gray-400">{tx.time}</span>
                {tx.flagged && <ExclamationTriangleIcon className="w-3 h-3 text-red-500" />}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Encrypted view */}
      {encrypted && (
        <div className="mt-4">
          <div className="text-xs font-medium text-gray-500 mb-2 flex items-center gap-1">
            <LockClosedIcon className="w-3 h-3" />
            Datos cifrados con CKKS (128-bit):
          </div>
          <div className="bg-gray-900 rounded p-2 font-mono text-[8px] text-green-400 break-all leading-relaxed">
            {generateCiphertext(128)}...
          </div>
          <div className="mt-2 text-xs text-gray-500 flex items-center gap-1">
            <EyeSlashIcon className="w-3 h-3" />
            Datos originales matematicamente irrecuperables
          </div>
        </div>
      )}

      {/* Accuracy */}
      {showAccuracy && (
        <div className="mt-4">
          <ProgressBar
            value={accuracy || config.baseAccuracy}
            maxValue={100}
            colorClass={config.barColor}
            label="Accuracy del modelo"
          />
        </div>
      )}
    </div>
  )
}

// Server view component
function ServerView({ showData = false, isTraining = false, trainingProgress = 0 }) {
  return (
    <div className="rounded-xl border-2 border-purple-500 bg-purple-50 p-5">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-full flex items-center justify-center text-white">
          <ServerIcon className="w-6 h-6" />
        </div>
        <div>
          <h3 className="font-bold text-gray-900 text-lg">Servidor del Consorcio</h3>
          <p className="text-sm text-gray-500">Computo sobre datos cifrados</p>
        </div>
      </div>

      {showData && (
        <>
          <div className="bg-yellow-100 border border-yellow-300 rounded-lg p-3 mb-4">
            <div className="flex items-center gap-2 text-yellow-800 text-sm font-medium">
              <EyeSlashIcon className="w-4 h-4" />
              El servidor NO puede ver los datos originales
            </div>
          </div>

          <div className="space-y-3">
            <div className="bg-gray-900 rounded p-3">
              <div className="text-xs text-gray-400 mb-1">Ciphertext de Banco A:</div>
              <div className="font-mono text-[8px] text-blue-400 break-all">
                {generateCiphertext(96)}...
              </div>
            </div>
            <div className="bg-gray-900 rounded p-3">
              <div className="text-xs text-gray-400 mb-1">Ciphertext de Banco B:</div>
              <div className="font-mono text-[8px] text-emerald-400 break-all">
                {generateCiphertext(96)}...
              </div>
            </div>
          </div>
        </>
      )}

      {isTraining && (
        <div className="mt-4">
          <div className="flex items-center gap-2 text-purple-600 mb-2">
            <ArrowPathIcon className="w-4 h-4 animate-spin" />
            <span className="text-sm font-medium">Entrenando sobre datos cifrados...</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className="h-full rounded-full bg-gradient-to-r from-purple-500 to-indigo-600 transition-all duration-500"
              style={{ width: `${trainingProgress}%` }}
            />
          </div>
          <div className="text-xs text-gray-500 mt-1">
            Epoch {Math.floor(trainingProgress / 10)}/10 - Gradientes computados sobre ciphertext
          </div>
        </div>
      )}
    </div>
  )
}

// Comparison chart component
function AccuracyComparison({ bankAAccuracy, bankBAccuracy, consortiumAccuracy, animate = false }) {
  const [displayBankA, setDisplayBankA] = useState(animate ? 0 : bankAAccuracy)
  const [displayBankB, setDisplayBankB] = useState(animate ? 0 : bankBAccuracy)
  const [displayConsortium, setDisplayConsortium] = useState(animate ? 0 : consortiumAccuracy)

  useEffect(() => {
    if (animate) {
      const timer = setTimeout(() => {
        setDisplayBankA(bankAAccuracy)
        setDisplayBankB(bankBAccuracy)
        setDisplayConsortium(consortiumAccuracy)
      }, 300)
      return () => clearTimeout(timer)
    }
  }, [animate, bankAAccuracy, bankBAccuracy, consortiumAccuracy])

  const maxValue = 100
  const barWidth = 120

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <h3 className="font-bold text-gray-900 text-lg mb-6 flex items-center gap-2">
        <ChartBarIcon className="w-5 h-5 text-purple-600" />
        Comparacion de Accuracy
      </h3>

      <div className="space-y-6">
        {/* Bank A */}
        <div className="flex items-center gap-4">
          <div className="w-24 text-right text-sm font-medium text-gray-600">Banco A solo:</div>
          <div className="flex-1 flex items-center gap-3">
            <div className="w-full max-w-md bg-gray-100 rounded-full h-8 relative overflow-hidden">
              <div
                className="h-full bg-blue-500 rounded-full transition-all duration-1000 ease-out"
                style={{ width: `${(displayBankA / maxValue) * 100}%` }}
              />
              <div className="absolute inset-0 flex items-center px-3">
                <span className="text-sm font-bold text-white drop-shadow">{displayBankA}%</span>
              </div>
            </div>
          </div>
        </div>

        {/* Bank B */}
        <div className="flex items-center gap-4">
          <div className="w-24 text-right text-sm font-medium text-gray-600">Banco B solo:</div>
          <div className="flex-1 flex items-center gap-3">
            <div className="w-full max-w-md bg-gray-100 rounded-full h-8 relative overflow-hidden">
              <div
                className="h-full bg-emerald-500 rounded-full transition-all duration-1000 ease-out"
                style={{ width: `${(displayBankB / maxValue) * 100}%` }}
              />
              <div className="absolute inset-0 flex items-center px-3">
                <span className="text-sm font-bold text-white drop-shadow">{displayBankB}%</span>
              </div>
            </div>
          </div>
        </div>

        {/* Consortium */}
        <div className="flex items-center gap-4">
          <div className="w-24 text-right text-sm font-medium text-gray-600">CONSORCIO:</div>
          <div className="flex-1 flex items-center gap-3">
            <div className="w-full max-w-md bg-gray-100 rounded-full h-10 relative overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-purple-500 to-indigo-600 rounded-full transition-all duration-1000 ease-out"
                style={{ width: `${(displayConsortium / maxValue) * 100}%` }}
              />
              <div className="absolute inset-0 flex items-center px-3">
                <span className="text-sm font-bold text-white drop-shadow">{displayConsortium}%</span>
              </div>
            </div>
            <div className="bg-green-100 text-green-700 px-3 py-1 rounded-full text-sm font-medium whitespace-nowrap">
              +{consortiumAccuracy - Math.max(bankAAccuracy, bankBAccuracy)}% mejora
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// Prediction result component
function PredictionResult({ probability, isLoading = false }) {
  const isFraud = probability > 0.5
  const confidence = Math.abs(probability - 0.5) * 200

  if (isLoading) {
    return (
      <div className="bg-gray-50 rounded-xl border border-gray-200 p-6 text-center">
        <ArrowPathIcon className="w-8 h-8 text-purple-500 animate-spin mx-auto mb-2" />
        <div className="text-gray-600">Procesando inferencia cifrada...</div>
      </div>
    )
  }

  return (
    <div className={`rounded-xl border-2 p-6 ${isFraud ? 'border-red-500 bg-red-50' : 'border-green-500 bg-green-50'}`}>
      <div className="text-center mb-4">
        <div className={`text-4xl font-bold ${isFraud ? 'text-red-600' : 'text-green-600'}`}>
          {(probability * 100).toFixed(1)}%
        </div>
        <div className="text-lg font-medium text-gray-700">Probabilidad de fraude</div>
      </div>

      <div className={`text-center py-3 rounded-lg ${isFraud ? 'bg-red-100' : 'bg-green-100'}`}>
        <div className={`text-xl font-bold ${isFraud ? 'text-red-700' : 'text-green-700'}`}>
          {isFraud ? 'FRAUDE DETECTADO' : 'TRANSACCION LEGITIMA'}
        </div>
        <div className="text-sm text-gray-600">Confianza: {confidence.toFixed(1)}%</div>
      </div>

      <div className="mt-4 space-y-2">
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <ShieldCheckIcon className="w-4 h-4 text-purple-500" />
          <span>Prediccion realizada sobre datos cifrados</span>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <EyeSlashIcon className="w-4 h-4 text-purple-500" />
          <span>Solo el banco puede descifrar el resultado</span>
        </div>
      </div>
    </div>
  )
}

// Main component
export default function BankConsortiumDemo() {
  const [step, setStep] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [trainingProgress, setTrainingProgress] = useState(0)
  const [showPrediction, setShowPrediction] = useState(false)
  const [predictionLoading, setPredictionLoading] = useState(false)

  // Accuracies
  const bankAAccuracy = 72
  const bankBAccuracy = 68
  const consortiumAccuracy = 87

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
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 via-indigo-600 to-blue-600 text-white py-8 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center gap-3 mb-2">
            <ShieldCheckIcon className="w-8 h-8" />
            <h1 className="text-3xl font-bold">Demo: Consorcio Bancario de Deteccion de Fraude</h1>
          </div>
          <p className="text-purple-100 text-lg">
            Machine Learning colaborativo sin compartir datos sensibles usando FHE
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
                    : 'bg-purple-100 text-purple-600 hover:bg-purple-200'
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
                className="px-3 py-2 rounded-lg bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
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
                      ? 'bg-purple-100 text-purple-700 ring-2 ring-purple-500'
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
                <ExclamationTriangleIcon className="w-12 h-12 text-red-500 flex-shrink-0" />
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">El Dilema del Fraude Bancario</h2>
                  <p className="text-gray-700 text-lg mb-4">
                    Un modelo de ML entrenado con datos de multiples bancos detecta significativamente mas fraude.
                    <span className="font-bold text-red-600"> Pero compartir transacciones de clientes es ilegal y viola la privacidad.</span>
                  </p>
                  <div className="grid grid-cols-3 gap-4 mt-6">
                    <div className="bg-white rounded-lg p-4 border border-red-200">
                      <div className="text-red-600 font-bold mb-1">Secreto bancario</div>
                      <div className="text-sm text-gray-500">Los datos de transacciones son confidenciales</div>
                    </div>
                    <div className="bg-white rounded-lg p-4 border border-red-200">
                      <div className="text-red-600 font-bold mb-1">Competencia directa</div>
                      <div className="text-sm text-gray-500">Los bancos son competidores entre si</div>
                    </div>
                    <div className="bg-white rounded-lg p-4 border border-red-200">
                      <div className="text-red-600 font-bold mb-1">Regulacion financiera</div>
                      <div className="text-sm text-gray-500">GDPR, PCI-DSS, y regulaciones locales</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-xl border border-purple-200 p-8">
              <div className="flex items-start gap-4">
                <ShieldCheckIcon className="w-12 h-12 text-purple-500 flex-shrink-0" />
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">La Solucion: FHE (Fully Homomorphic Encryption)</h2>
                  <p className="text-gray-700 text-lg">
                    Con FHE, los bancos pueden entrenar un modelo de ML colaborativo sobre datos <span className="font-bold text-purple-600">CIFRADOS</span>.
                    El servidor procesa los datos pero <span className="font-bold text-purple-600">NUNCA</span> puede ver los datos originales.
                  </p>
                  <div className="mt-4 flex items-center gap-6">
                    <div className="flex items-center gap-2">
                      <CheckCircleIcon className="w-5 h-5 text-green-500" />
                      <span>Datos siempre cifrados</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircleIcon className="w-5 h-5 text-green-500" />
                      <span>Modelo aprende patrones</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircleIcon className="w-5 h-5 text-green-500" />
                      <span>Cumplimiento regulatorio</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Step 1: Setup */}
        {step === 1 && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-gray-900">Setup: Datos Reales de los Bancos</h2>

            {/* Bank cards side by side */}
            <div className="grid grid-cols-2 gap-6">
              <BankCard bank="bankA" showData={true} />
              <BankCard bank="bankB" showData={true} />
            </div>

            {/* Detailed data tables */}
            <div className="grid grid-cols-1 gap-6">
              <div>
                <h3 className="text-lg font-bold text-blue-600 mb-3 flex items-center gap-2">
                  <BuildingOffice2Icon className="w-5 h-5" />
                  Dataset Banco A - Transacciones con etiquetas de fraude
                </h3>
                <DataTable bank="bankA" showFraudReason={true} />
              </div>
              <div>
                <h3 className="text-lg font-bold text-emerald-600 mb-3 flex items-center gap-2">
                  <BuildingOffice2Icon className="w-5 h-5" />
                  Dataset Banco B - Transacciones con etiquetas de fraude
                </h3>
                <DataTable bank="bankB" showFraudReason={true} />
              </div>
            </div>

            {/* Key insight */}
            <div className="bg-yellow-50 rounded-xl border border-yellow-200 p-6">
              <div className="flex items-start gap-3">
                <ExclamationTriangleIcon className="w-6 h-6 text-yellow-600 flex-shrink-0 mt-1" />
                <div>
                  <h3 className="font-bold text-yellow-800 mb-1">Observa los patrones diferentes:</h3>
                  <ul className="text-yellow-700 text-sm space-y-1">
                    <li><strong>Banco A</strong> detecta fraude por: hora nocturna, transacciones internacionales, alta velocidad</li>
                    <li><strong>Banco B</strong> detecta fraude por: distancia del hogar, gasolineras, comercios de viaje</li>
                    <li className="font-bold mt-2">Problema: Cada banco NO VE los patrones del otro!</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Step 2: Individual Training */}
        {step === 2 && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-gray-900">Entrenamiento Individual: El Problema</h2>
            <div className="grid grid-cols-2 gap-6">
              <BankCard bank="bankA" showAccuracy={true} accuracy={bankAAccuracy} />
              <BankCard bank="bankB" showAccuracy={true} accuracy={bankBAccuracy} />
            </div>
            <div className="bg-yellow-50 rounded-xl border border-yellow-200 p-6">
              <div className="flex items-start gap-3">
                <ExclamationTriangleIcon className="w-6 h-6 text-yellow-600 flex-shrink-0 mt-1" />
                <div>
                  <h3 className="font-bold text-yellow-800 mb-1">Problema: Modelos Incompletos</h3>
                  <p className="text-yellow-700">
                    Banco A detecta sus patrones ({bankAAccuracy}%) pero NO los de Banco B.
                    Banco B detecta sus patrones ({bankBAccuracy}%) pero NO los de Banco A.
                    <span className="font-bold"> Solucion: Colaborar sin compartir datos!</span>
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Step 3: FHE Encryption */}
        {step === 3 && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-gray-900">Cifrado FHE: Transformacion de Datos</h2>

            {/* Before/After comparison */}
            <div className="grid grid-cols-2 gap-6">
              {/* Before - Plain data */}
              <div className="bg-white rounded-xl border-2 border-gray-300 p-5">
                <h3 className="font-bold text-gray-700 mb-3 flex items-center gap-2">
                  <EyeSlashIcon className="w-5 h-5 text-gray-500" />
                  ANTES: Datos en texto plano
                </h3>
                <div className="bg-gray-50 rounded p-3 font-mono text-xs space-y-1">
                  <div className="text-gray-600">TXN-58847 | $2,420.00 | Amazon.com | 2:15 AM | Intl: Yes</div>
                  <div className="text-gray-600">TXN-58849 | $1,850.00 | BestBuy.com | 3:45 AM | Intl: Yes</div>
                  <div className="text-gray-600">TXN-58851 | $3,200.00 | Alibaba.com | 1:00 AM | Intl: Yes</div>
                  <div className="text-red-500 text-[10px] mt-2">Datos sensibles visibles - NO se pueden compartir</div>
                </div>
              </div>

              {/* After - Encrypted */}
              <div className="bg-gray-900 rounded-xl border-2 border-green-500 p-5">
                <h3 className="font-bold text-green-400 mb-3 flex items-center gap-2">
                  <LockClosedIcon className="w-5 h-5" />
                  DESPUES: Ciphertext CKKS
                </h3>
                <div className="font-mono text-[9px] text-green-400 space-y-1 break-all">
                  <div>0x7f3a9b2c{generateCiphertext(24)}...</div>
                  <div>0x8e4b1d5f{generateCiphertext(24)}...</div>
                  <div>0x2c6a8e3d{generateCiphertext(24)}...</div>
                  <div className="text-green-300 text-[10px] mt-2">Matematicamente imposible de descifrar sin la clave</div>
                </div>
              </div>
            </div>

            {/* Both banks encrypted */}
            <div className="grid grid-cols-2 gap-6">
              <BankCard bank="bankA" encrypted={true} />
              <BankCard bank="bankB" encrypted={true} />
            </div>

            {/* CKKS Parameters */}
            <div className="bg-blue-50 rounded-xl border border-blue-200 p-6">
              <h3 className="font-bold text-blue-800 mb-3 flex items-center gap-2">
                <LockClosedIcon className="w-5 h-5" />
                Parametros CKKS (Cheon-Kim-Kim-Song)
              </h3>
              <div className="grid grid-cols-5 gap-3 text-sm">
                <div className="bg-white rounded p-3 text-center">
                  <div className="text-gray-500 text-xs">Security</div>
                  <div className="font-bold text-blue-600">128 bits</div>
                </div>
                <div className="bg-white rounded p-3 text-center">
                  <div className="text-gray-500 text-xs">Poly Degree</div>
                  <div className="font-bold text-blue-600">8192</div>
                </div>
                <div className="bg-white rounded p-3 text-center">
                  <div className="text-gray-500 text-xs">Coeff Modulus</div>
                  <div className="font-bold text-blue-600 text-xs">[60,40,40,60]</div>
                </div>
                <div className="bg-white rounded p-3 text-center">
                  <div className="text-gray-500 text-xs">Scale</div>
                  <div className="font-bold text-blue-600">2^40</div>
                </div>
                <div className="bg-white rounded p-3 text-center">
                  <div className="text-gray-500 text-xs">Slots</div>
                  <div className="font-bold text-blue-600">4096</div>
                </div>
              </div>
              <p className="text-sm text-blue-700 mt-3">
                Equivalente a AES-128. Romperia tomaria mas tiempo que la edad del universo.
              </p>
            </div>
          </div>
        )}

        {/* Step 4: Consortium Training */}
        {step === 4 && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-gray-900">Entrenamiento del Consorcio sobre Datos Cifrados</h2>
            <div className="grid grid-cols-3 gap-6">
              <div className="space-y-4">
                <BankCard bank="bankA" encrypted={true} />
                <div className="flex justify-center">
                  <ArrowRightIcon className="w-8 h-8 text-purple-500 rotate-90 lg:rotate-0" />
                </div>
              </div>
              <ServerView showData={true} isTraining={true} trainingProgress={trainingProgress} />
              <div className="space-y-4">
                <BankCard bank="bankB" encrypted={true} />
                <div className="flex justify-center">
                  <ArrowRightIcon className="w-8 h-8 text-purple-500 rotate-90 lg:rotate-180" />
                </div>
              </div>
            </div>
            {trainingProgress === 100 && (
              <div className="bg-green-50 rounded-xl border border-green-200 p-6">
                <div className="flex items-center gap-3">
                  <CheckCircleIcon className="w-8 h-8 text-green-500" />
                  <div>
                    <h3 className="font-bold text-green-800">Entrenamiento Completado!</h3>
                    <p className="text-green-700">
                      El modelo del consorcio ha aprendido patrones de AMBOS bancos sin ver ningun dato original.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Step 5: Encrypted Inference */}
        {step === 5 && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-gray-900">Inferencia Cifrada: Analisis en Tiempo Real</h2>

            <div className="grid grid-cols-2 gap-6">
              {/* Suspicious transaction with full details */}
              <div className="space-y-4">
                <div className="bg-white rounded-xl border-2 border-orange-400 p-5">
                  <h3 className="font-bold text-gray-900 mb-3 flex items-center gap-2">
                    <ExclamationTriangleIcon className="w-5 h-5 text-orange-500" />
                    Nueva Transaccion - {SUSPICIOUS_TRANSACTION.id}
                  </h3>

                  {/* Transaction details */}
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div className="flex items-center gap-2 p-2 bg-gray-50 rounded">
                      <BanknotesIcon className="w-4 h-4 text-gray-400" />
                      <span className="text-gray-500">Monto:</span>
                      <span className="font-bold">${SUSPICIOUS_TRANSACTION.amount.toLocaleString()}</span>
                    </div>
                    <div className="flex items-center gap-2 p-2 bg-gray-50 rounded">
                      <ServerIcon className="w-4 h-4 text-gray-400" />
                      <span className="text-gray-500">Comercio:</span>
                      <span className="font-bold text-xs">{SUSPICIOUS_TRANSACTION.merchant}</span>
                    </div>
                    <div className="flex items-center gap-2 p-2 bg-red-50 rounded border border-red-200">
                      <ClockIcon className="w-4 h-4 text-red-500" />
                      <span className="text-gray-500">Hora:</span>
                      <span className="font-bold text-red-600">{SUSPICIOUS_TRANSACTION.time}</span>
                    </div>
                    <div className="flex items-center gap-2 p-2 bg-red-50 rounded border border-red-200">
                      <GlobeAltIcon className="w-4 h-4 text-red-500" />
                      <span className="text-gray-500">Internacional:</span>
                      <span className="font-bold text-red-600">Si</span>
                    </div>
                    <div className="flex items-center gap-2 p-2 bg-gray-50 rounded">
                      <MapPinIcon className="w-4 h-4 text-gray-400" />
                      <span className="text-gray-500">Distancia:</span>
                      <span className="font-bold">{SUSPICIOUS_TRANSACTION.distanceFromHome} mi</span>
                    </div>
                    <div className="flex items-center gap-2 p-2 bg-red-50 rounded border border-red-200">
                      <ArrowPathIcon className="w-4 h-4 text-red-500" />
                      <span className="text-gray-500">Velocidad:</span>
                      <span className="font-bold text-red-600">{SUSPICIOUS_TRANSACTION.txnsLast24h} txn/24h</span>
                    </div>
                  </div>

                  {/* Red flags */}
                  <div className="mt-3 p-2 bg-red-100 rounded-lg border border-red-200">
                    <div className="text-xs font-bold text-red-700 mb-1">Alertas detectadas:</div>
                    <div className="flex flex-wrap gap-1">
                      <span className="text-[10px] bg-red-200 text-red-800 px-1.5 py-0.5 rounded">Hora nocturna (2 AM)</span>
                      <span className="text-[10px] bg-red-200 text-red-800 px-1.5 py-0.5 rounded">Internacional</span>
                      <span className="text-[10px] bg-red-200 text-red-800 px-1.5 py-0.5 rounded">Alta velocidad (7 txn)</span>
                      <span className="text-[10px] bg-red-200 text-red-800 px-1.5 py-0.5 rounded">2x monto promedio</span>
                    </div>
                  </div>
                </div>

                {/* Feature vector visualization */}
                <div className="bg-gray-900 rounded-xl p-4">
                  <h4 className="text-green-400 text-sm font-bold mb-2 flex items-center gap-2">
                    <CpuChipIcon className="w-4 h-4" />
                    Vector de Features (Entrada al Modelo)
                  </h4>
                  <div className="font-mono text-[10px] text-green-300 bg-black/30 rounded p-2 overflow-x-auto">
                    <div className="text-gray-500 mb-1"># Feature vector normalizado</div>
                    <div>X = [{SUSPICIOUS_TRANSACTION.featureVector.join(', ')}]</div>
                    <div className="text-gray-500 mt-2 text-[9px]">
                      # {SUSPICIOUS_TRANSACTION.featureNames.join(', ')}
                    </div>
                  </div>

                  {/* Encrypted version */}
                  <div className="mt-3">
                    <div className="text-yellow-400 text-xs mb-1">Cifrado CKKS:</div>
                    <div className="font-mono text-[8px] text-yellow-300/80 break-all">
                      ct = Enc(X) = 0x{generateCiphertext(48)}...
                    </div>
                  </div>
                </div>
              </div>

              {/* Prediction result */}
              <div className="space-y-4">
                {predictionLoading ? (
                  <PredictionResult probability={0} isLoading={true} />
                ) : showPrediction ? (
                  <>
                    <PredictionResult probability={0.89} />
                    {/* Model explanation */}
                    <div className="bg-purple-50 rounded-xl border border-purple-200 p-4">
                      <h4 className="font-bold text-purple-800 text-sm mb-2">Por que el modelo detecto fraude:</h4>
                      <div className="space-y-2 text-xs">
                        <div className="flex justify-between items-center">
                          <span className="text-gray-600">Hora nocturna (2 AM)</span>
                          <div className="w-24 bg-gray-200 rounded-full h-2">
                            <div className="bg-red-500 h-2 rounded-full" style={{width: '85%'}}></div>
                          </div>
                          <span className="text-red-600 font-bold">+35%</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-gray-600">Internacional</span>
                          <div className="w-24 bg-gray-200 rounded-full h-2">
                            <div className="bg-red-500 h-2 rounded-full" style={{width: '70%'}}></div>
                          </div>
                          <span className="text-red-600 font-bold">+28%</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-gray-600">Alta velocidad</span>
                          <div className="w-24 bg-gray-200 rounded-full h-2">
                            <div className="bg-red-500 h-2 rounded-full" style={{width: '60%'}}></div>
                          </div>
                          <span className="text-red-600 font-bold">+18%</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-gray-600">Categoria Online</span>
                          <div className="w-24 bg-gray-200 rounded-full h-2">
                            <div className="bg-orange-400 h-2 rounded-full" style={{width: '30%'}}></div>
                          </div>
                          <span className="text-orange-600 font-bold">+8%</span>
                        </div>
                      </div>
                      <p className="text-purple-600 text-[10px] mt-3">
                        El modelo del consorcio detecto patrones de AMBOS bancos que un modelo individual no hubiera visto.
                      </p>
                    </div>
                  </>
                ) : (
                  <div className="bg-gray-50 rounded-xl border border-gray-200 p-6 flex items-center justify-center h-full">
                    <div className="text-center text-gray-500">
                      <CpuChipIcon className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                      <p>Procesando inferencia cifrada...</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Step 6: Results */}
        {step === 6 && (
          <div className="space-y-8">
            <h2 className="text-2xl font-bold text-gray-900">Resultados: Privacidad Preservada + Mejor Deteccion</h2>

            <AccuracyComparison
              bankAAccuracy={bankAAccuracy}
              bankBAccuracy={bankBAccuracy}
              consortiumAccuracy={consortiumAccuracy}
              animate={true}
            />

            <div className="grid grid-cols-2 gap-6">
              <div className="bg-green-50 rounded-xl border border-green-200 p-6">
                <h3 className="font-bold text-green-800 mb-4 flex items-center gap-2">
                  <CheckCircleIcon className="w-5 h-5" />
                  Privacidad Garantizada
                </h3>
                <ul className="space-y-2">
                  <li className="flex items-center gap-2 text-green-700">
                    <CheckCircleIcon className="w-4 h-4" />
                    Datos originales NUNCA salieron de los bancos
                  </li>
                  <li className="flex items-center gap-2 text-green-700">
                    <CheckCircleIcon className="w-4 h-4" />
                    Solo ciphertext fue compartido
                  </li>
                  <li className="flex items-center gap-2 text-green-700">
                    <CheckCircleIcon className="w-4 h-4" />
                    El servidor NO puede descifrar los datos
                  </li>
                  <li className="flex items-center gap-2 text-green-700">
                    <CheckCircleIcon className="w-4 h-4" />
                    Cumplimiento GDPR/PCI-DSS garantizado
                  </li>
                </ul>
              </div>

              <div className="bg-purple-50 rounded-xl border border-purple-200 p-6">
                <h3 className="font-bold text-purple-800 mb-4 flex items-center gap-2">
                  <SparklesIcon className="w-5 h-5" />
                  Valor de Negocio
                </h3>
                <ul className="space-y-2">
                  <li className="flex items-center gap-2 text-purple-700">
                    <ChartBarIcon className="w-4 h-4" />
                    +{consortiumAccuracy - Math.max(bankAAccuracy, bankBAccuracy)}% mejora en deteccion
                  </li>
                  <li className="flex items-center gap-2 text-purple-700">
                    <BanknotesIcon className="w-4 h-4" />
                    Ahorro estimado: $15,000/mes por banco
                  </li>
                  <li className="flex items-center gap-2 text-purple-700">
                    <BuildingOffice2Icon className="w-4 h-4" />
                    Colaboracion entre competidores
                  </li>
                  <li className="flex items-center gap-2 text-purple-700">
                    <ShieldCheckIcon className="w-4 h-4" />
                    Ventaja competitiva sin exposicion
                  </li>
                </ul>
              </div>
            </div>

            <div className="bg-gradient-to-r from-purple-600 to-indigo-600 rounded-xl p-8 text-white text-center">
              <h3 className="text-2xl font-bold mb-2">
                El consorcio logro {consortiumAccuracy}% de accuracy
              </h3>
              <p className="text-purple-100 text-lg">
                Machine Learning colaborativo sin compartir datos sensibles - gracias a FHE
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="bg-gray-100 border-t border-gray-200 py-6 px-6 mt-8">
        <div className="max-w-7xl mx-auto text-center text-gray-500 text-sm">
          <p>Demo - Xcapit Privacy Platform | Fully Homomorphic Encryption para ML Colaborativo</p>
        </div>
      </div>
    </div>
  )
}
