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
  DocumentTextIcon,
  ClockIcon,
  UserGroupIcon,
  ScaleIcon,
  SparklesIcon
} from '@heroicons/react/24/outline'

// Insurance company configuration
const INSURERS = {
  alpha: {
    name: 'Seguro Alpha',
    shortName: 'Alpha',
    country: 'Argentina',
    records: 6000,
    fraudRate: '5.2%',
    patterns: ['High claim + New policy', 'No witnesses + Late report', 'Theft + No police report'],
    baseAccuracy: 71,
    borderColor: 'border-amber-500',
    bgColor: 'bg-amber-50',
    textColor: 'text-amber-600',
    logoColor: 'bg-amber-600',
    barColor: 'bg-amber-500',
    gradientFrom: 'from-amber-500',
    gradientTo: 'to-amber-600',
  },
  beta: {
    name: 'Seguro Beta',
    shortName: 'Beta',
    country: 'Chile',
    records: 5000,
    fraudRate: '4.8%',
    patterns: ['Injury + Quick payout request', 'Multiple claims history', 'Inconsistent documentation'],
    baseAccuracy: 68,
    borderColor: 'border-rose-500',
    bgColor: 'bg-rose-50',
    textColor: 'text-rose-600',
    logoColor: 'bg-rose-600',
    barColor: 'bg-rose-500',
    gradientFrom: 'from-rose-500',
    gradientTo: 'to-rose-600',
  },
  gamma: {
    name: 'Seguro Gamma',
    shortName: 'Gamma',
    country: 'Mexico',
    records: 4000,
    fraudRate: '5.5%',
    patterns: ['Property damage + Exaggerated value', 'Staged accidents', 'Ghost claims'],
    baseAccuracy: 65,
    borderColor: 'border-cyan-500',
    bgColor: 'bg-cyan-50',
    textColor: 'text-cyan-600',
    logoColor: 'bg-cyan-600',
    barColor: 'bg-cyan-500',
    gradientFrom: 'from-cyan-500',
    gradientTo: 'to-cyan-600',
  }
}

// Generate random ciphertext for display
const generateCiphertext = (length = 64) => {
  const chars = '0123456789abcdef'
  return Array.from({ length }, () => chars[Math.floor(Math.random() * chars.length)]).join('')
}

// Sample claims data
const SAMPLE_CLAIMS = {
  alpha: [
    { id: 'CLM-A001', amount: 45000, type: 'Theft', policyAge: 3, daysToReport: 45, witnesses: false, policeReport: false, flagged: true, reason: 'High amount + New policy + No evidence' },
    { id: 'CLM-A002', amount: 2500, type: 'Collision', policyAge: 36, daysToReport: 2, witnesses: true, policeReport: true, flagged: false, reason: null },
    { id: 'CLM-A003', amount: 78000, type: 'Injury', policyAge: 6, daysToReport: 90, witnesses: false, policeReport: false, flagged: true, reason: 'Very high amount + Late report + No witnesses' },
    { id: 'CLM-A004', amount: 1200, type: 'Property', policyAge: 48, daysToReport: 5, witnesses: true, policeReport: true, flagged: false, reason: null },
  ],
  beta: [
    { id: 'CLM-B001', amount: 55000, type: 'Injury', policyAge: 2, daysToReport: 30, witnesses: false, policeReport: true, flagged: true, reason: 'Quick injury claim + New policy' },
    { id: 'CLM-B002', amount: 3200, type: 'Collision', policyAge: 24, daysToReport: 1, witnesses: true, policeReport: true, flagged: false, reason: null },
    { id: 'CLM-B003', amount: 42000, type: 'Theft', policyAge: 8, daysToReport: 60, witnesses: false, policeReport: false, flagged: true, reason: 'Theft + Late report + No documentation' },
    { id: 'CLM-B004', amount: 890, type: 'Property', policyAge: 60, daysToReport: 3, witnesses: true, policeReport: true, flagged: false, reason: null },
  ],
  gamma: [
    { id: 'CLM-G001', amount: 85000, type: 'Property', policyAge: 4, daysToReport: 75, witnesses: false, policeReport: false, flagged: true, reason: 'Exaggerated property claim + No evidence' },
    { id: 'CLM-G002', amount: 1800, type: 'Collision', policyAge: 30, daysToReport: 2, witnesses: true, policeReport: true, flagged: false, reason: null },
    { id: 'CLM-G003', amount: 62000, type: 'Injury', policyAge: 5, daysToReport: 55, witnesses: false, policeReport: true, flagged: true, reason: 'High injury claim + New policy + Late report' },
    { id: 'CLM-G004', amount: 2100, type: 'Other', policyAge: 42, daysToReport: 7, witnesses: true, policeReport: true, flagged: false, reason: null },
  ]
}

// Dataset statistics
const DATASET_STATS = {
  alpha: {
    totalClaims: 6000,
    fraudCases: 312,
    avgClaimAmount: 15200,
    avgDaysToReport: 18,
    features: ['claim_amount', 'policy_age', 'days_to_report', 'witnesses', 'police_report', 'claim_type'],
  },
  beta: {
    totalClaims: 5000,
    fraudCases: 240,
    avgClaimAmount: 12800,
    avgDaysToReport: 22,
    features: ['claim_amount', 'policy_age', 'days_to_report', 'previous_claims', 'documentation_score'],
  },
  gamma: {
    totalClaims: 4000,
    fraudCases: 220,
    avgClaimAmount: 18500,
    avgDaysToReport: 25,
    features: ['claim_amount', 'policy_age', 'claimed_vs_actual', 'witness_count', 'investigation_flag'],
  }
}

// Suspicious claim for prediction
const SUSPICIOUS_CLAIM = {
  id: 'CLM-NEW-001',
  amount: 72000,
  type: 'Theft',
  policyAge: 4,
  daysToReport: 65,
  witnesses: false,
  policeReport: false,
  previousClaims: 3,
  customerAge: 32,
  featureVector: [72000, 4, 65, 0, 0, 3, 32, 1, 0, 0],
  featureNames: ['amount', 'policy_months', 'days_report', 'witnesses', 'police', 'prev_claims', 'age', 'type_theft', 'type_injury', 'type_collision'],
}

// Step definitions
const STEPS = [
  {
    number: 0,
    title: 'El Problema',
    description: 'Tres aseguradoras quieren combatir el fraude, pero no pueden compartir datos de clientes.',
    icon: ExclamationTriangleIcon,
  },
  {
    number: 1,
    title: 'Consorcio',
    description: 'Crear consorcio con aseguradoras de Argentina, Chile y Mexico.',
    icon: BuildingOffice2Icon,
  },
  {
    number: 2,
    title: 'Datos Encriptados',
    description: 'Cada aseguradora contribuye sus datos cifrados con CKKS.',
    icon: LockClosedIcon,
  },
  {
    number: 3,
    title: 'Votacion',
    description: 'Votacion commit-reveal para autorizar el entrenamiento.',
    icon: ScaleIcon,
  },
  {
    number: 4,
    title: 'Entrenamiento FHE',
    description: 'El modelo se entrena sobre datos cifrados sin verlos.',
    icon: ServerIcon,
  },
  {
    number: 5,
    title: 'Analisis de Reclamo',
    description: 'Nuevo reclamo sospechoso analizado de forma privada.',
    icon: CpuChipIcon,
  },
  {
    number: 6,
    title: 'Resultados',
    description: 'Comparacion de accuracy individual vs consorcio.',
    icon: SparklesIcon,
  },
]

// Claims Table Component
function ClaimsTable({ insurer }) {
  const claims = SAMPLE_CLAIMS[insurer]
  const config = INSURERS[insurer]
  const stats = DATASET_STATS[insurer]

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      <div className={`px-4 py-3 ${config.bgColor} border-b border-gray-200`}>
        <div className="flex justify-between items-center">
          <span className="font-medium text-gray-700">
            Muestra de reclamos - {stats.totalClaims.toLocaleString()} registros
          </span>
          <span className={`text-sm ${config.textColor} font-medium`}>
            {stats.fraudCases} fraudes ({((stats.fraudCases/stats.totalClaims)*100).toFixed(1)}%)
          </span>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-3 py-2 text-left font-medium text-gray-500">ID</th>
              <th className="px-3 py-2 text-left font-medium text-gray-500">Monto</th>
              <th className="px-3 py-2 text-left font-medium text-gray-500">Tipo</th>
              <th className="px-3 py-2 text-left font-medium text-gray-500">Poliza</th>
              <th className="px-3 py-2 text-left font-medium text-gray-500">Dias</th>
              <th className="px-3 py-2 text-left font-medium text-gray-500">Testigos</th>
              <th className="px-3 py-2 text-left font-medium text-gray-500">Estado</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {claims.map((claim) => (
              <tr key={claim.id} className={claim.flagged ? 'bg-red-50' : ''}>
                <td className="px-3 py-2 font-mono text-xs">{claim.id}</td>
                <td className="px-3 py-2">${claim.amount.toLocaleString()}</td>
                <td className="px-3 py-2">{claim.type}</td>
                <td className="px-3 py-2">{claim.policyAge}m</td>
                <td className="px-3 py-2">{claim.daysToReport}d</td>
                <td className="px-3 py-2">{claim.witnesses ? 'Si' : 'No'}</td>
                <td className="px-3 py-2">
                  {claim.flagged ? (
                    <span className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs font-medium">
                      Sospechoso
                    </span>
                  ) : (
                    <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-medium">
                      Normal
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

// Insurer Card Component
function InsurerCard({ insurerKey, showEncrypted = false }) {
  const config = INSURERS[insurerKey]
  const stats = DATASET_STATS[insurerKey]

  return (
    <div className={`rounded-xl border-2 ${config.borderColor} overflow-hidden`}>
      <div className={`${config.bgColor} px-4 py-3 border-b border-gray-200`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 ${config.logoColor} rounded-lg flex items-center justify-center text-white font-bold`}>
              {config.shortName[0]}
            </div>
            <div>
              <div className="font-bold text-gray-900">{config.name}</div>
              <div className="text-sm text-gray-500">{config.country}</div>
            </div>
          </div>
          <div className="text-right">
            <div className={`text-lg font-bold ${config.textColor}`}>{config.records.toLocaleString()}</div>
            <div className="text-xs text-gray-500">reclamos</div>
          </div>
        </div>
      </div>

      <div className="p-4 bg-white">
        {!showEncrypted ? (
          <>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <div className="text-xs text-gray-500 uppercase">Fraudes</div>
                <div className="font-bold text-gray-900">{stats.fraudCases}</div>
              </div>
              <div>
                <div className="text-xs text-gray-500 uppercase">Monto Prom.</div>
                <div className="font-bold text-gray-900">${stats.avgClaimAmount.toLocaleString()}</div>
              </div>
            </div>
            <div className="text-xs text-gray-500 mb-2">Patrones de fraude detectados:</div>
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
              <span className="text-sm font-medium">Datos cifrados con CKKS</span>
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
        <ServerIcon className="w-6 h-6 text-purple-400" />
        <span className="font-bold">Servidor FHE del Consorcio</span>
      </div>

      <div className="bg-gray-800 rounded-lg p-4 mb-4">
        <div className="text-sm text-gray-400 mb-2">Vista del servidor:</div>
        <div className="space-y-2">
          {Object.keys(INSURERS).map(key => (
            <div key={key} className="bg-gray-900 rounded p-2">
              <div className={`text-xs ${INSURERS[key].textColor} mb-1`}>Ciphertext de {INSURERS[key].name}:</div>
              <div className="font-mono text-[8px] text-gray-400 break-all">
                {generateCiphertext(64)}...
              </div>
            </div>
          ))}
        </div>
      </div>

      {isTraining && (
        <div className="mt-4">
          <div className="flex items-center gap-2 text-purple-400 mb-2">
            <ArrowPathIcon className="w-4 h-4 animate-spin" />
            <span className="text-sm font-medium">Entrenando Random Forest sobre datos cifrados...</span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-3">
            <div
              className="h-full rounded-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-500"
              style={{ width: `${trainingProgress}%` }}
            />
          </div>
          <div className="text-xs text-gray-400 mt-1">
            Epoch {Math.floor(trainingProgress / 10)}/10 - {stats.totalTrees || 100} arboles entrenados
          </div>
        </div>
      )}
    </div>
  )
}

// Stats for training
const stats = { totalTrees: 100 }

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
        <ChartBarIcon className="w-5 h-5 text-purple-600" />
        Comparacion de Accuracy
      </h3>

      <div className="space-y-4">
        {Object.entries(INSURERS).map(([key, config]) => (
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
                className="h-full bg-gradient-to-r from-purple-500 to-pink-600 rounded-full transition-all duration-1000 ease-out"
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
  const isFraud = probability > 0.5
  const confidence = Math.abs(probability - 0.5) * 200

  if (isLoading) {
    return (
      <div className="bg-gray-50 rounded-xl border border-gray-200 p-6 text-center">
        <ArrowPathIcon className="w-8 h-8 text-purple-500 animate-spin mx-auto mb-2" />
        <div className="text-gray-600">Analizando reclamo cifrado...</div>
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
          {isFraud ? 'RECLAMO FRAUDULENTO' : 'RECLAMO LEGITIMO'}
        </div>
        <div className="text-sm text-gray-600">Confianza: {confidence.toFixed(1)}%</div>
      </div>

      <div className="mt-4 space-y-2">
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <ShieldCheckIcon className="w-4 h-4 text-purple-500" />
          <span>Analisis realizado sobre datos cifrados</span>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <EyeSlashIcon className="w-4 h-4 text-purple-500" />
          <span>Solo la aseguradora puede ver detalles del cliente</span>
        </div>
      </div>
    </div>
  )
}

// Voting Animation Component
function VotingDisplay({ phase, votes }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <h3 className="font-bold text-gray-900 text-lg mb-4 flex items-center gap-2">
        <ScaleIcon className="w-5 h-5 text-purple-600" />
        Votacion Commit-Reveal
      </h3>

      <div className="space-y-4">
        {Object.entries(INSURERS).map(([key, config]) => (
          <div key={key} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-3">
              <div className={`w-8 h-8 ${config.logoColor} rounded-lg flex items-center justify-center text-white font-bold text-sm`}>
                {config.shortName[0]}
              </div>
              <span className="font-medium">{config.name}</span>
            </div>
            <div>
              {phase === 'commit' && (
                <div className="flex items-center gap-2">
                  <LockClosedIcon className="w-4 h-4 text-amber-500" />
                  <span className="text-sm text-amber-600 font-mono">
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

// Main Component
export default function InsuranceClaimsDemo() {
  const [step, setStep] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [trainingProgress, setTrainingProgress] = useState(0)
  const [showPrediction, setShowPrediction] = useState(false)
  const [predictionLoading, setPredictionLoading] = useState(false)
  const [votingPhase, setVotingPhase] = useState('commit')

  // Accuracies
  const individualAccuracies = { alpha: 71, beta: 68, gamma: 65 }
  const consortiumAccuracy = 89

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
      <div className="bg-gradient-to-r from-amber-600 via-rose-600 to-pink-600 text-white py-8 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center gap-3 mb-2">
            <ShieldCheckIcon className="w-8 h-8" />
            <h1 className="text-3xl font-bold">Demo: Consorcio de Seguros - Deteccion de Fraude</h1>
          </div>
          <p className="text-amber-100 text-lg">
            Tres aseguradoras colaboran para detectar fraude en reclamos sin compartir datos de clientes
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
                    : 'bg-amber-100 text-amber-600 hover:bg-amber-200'
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
                className="px-3 py-2 rounded-lg bg-amber-600 text-white hover:bg-amber-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
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
                      ? 'bg-amber-100 text-amber-700 ring-2 ring-amber-500'
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
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">El Problema del Fraude en Seguros</h2>
                  <p className="text-gray-700 text-lg mb-4">
                    El fraude en reclamos de seguros representa perdidas de <span className="font-bold text-red-600">$80 mil millones anuales</span> globalmente.
                    Modelos de ML colaborativos detectan mas fraude, pero compartir datos de clientes es ilegal.
                  </p>
                  <div className="grid grid-cols-3 gap-4 mt-6">
                    <div className="bg-white rounded-lg p-4 border border-red-200">
                      <div className="text-red-600 font-bold mb-1">Privacidad del Cliente</div>
                      <div className="text-sm text-gray-500">Datos medicos, financieros y personales</div>
                    </div>
                    <div className="bg-white rounded-lg p-4 border border-red-200">
                      <div className="text-red-600 font-bold mb-1">Competencia</div>
                      <div className="text-sm text-gray-500">Las aseguradoras compiten entre si</div>
                    </div>
                    <div className="bg-white rounded-lg p-4 border border-red-200">
                      <div className="text-red-600 font-bold mb-1">Regulaciones</div>
                      <div className="text-sm text-gray-500">GDPR, HIPAA, leyes locales de datos</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-r from-amber-50 to-rose-50 rounded-xl border border-amber-200 p-8">
              <div className="flex items-start gap-4">
                <ShieldCheckIcon className="w-12 h-12 text-amber-500 flex-shrink-0" />
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">La Solucion: Consorcio FHE</h2>
                  <p className="text-gray-700 text-lg">
                    Con Fully Homomorphic Encryption, las aseguradoras entrenan un modelo colaborativo sobre datos <span className="font-bold text-amber-600">CIFRADOS</span>.
                    Cada aseguradora mantiene control total de sus datos.
                  </p>
                  <div className="mt-4 flex items-center gap-6">
                    <div className="flex items-center gap-2">
                      <CheckCircleIcon className="w-5 h-5 text-green-500" />
                      <span>Datos siempre cifrados</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircleIcon className="w-5 h-5 text-green-500" />
                      <span>Gobernanza descentralizada</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircleIcon className="w-5 h-5 text-green-500" />
                      <span>Audit trail en blockchain</span>
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
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Consorcio de Aseguradoras LATAM</h2>
            <div className="grid grid-cols-3 gap-6">
              {Object.keys(INSURERS).map(key => (
                <InsurerCard key={key} insurerKey={key} showEncrypted={false} />
              ))}
            </div>
            <div className="bg-purple-50 rounded-xl border border-purple-200 p-6">
              <h3 className="font-bold text-gray-900 mb-4">Datos combinados del consorcio:</h3>
              <div className="grid grid-cols-4 gap-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-purple-600">15,000</div>
                  <div className="text-sm text-gray-500">Total reclamos</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-red-600">772</div>
                  <div className="text-sm text-gray-500">Fraudes detectados</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-amber-600">5.1%</div>
                  <div className="text-sm text-gray-500">Tasa de fraude</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-600">3</div>
                  <div className="text-sm text-gray-500">Paises</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Step 2: Encrypted Data */}
        {step === 2 && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Datos Contribuidos (Cifrados con CKKS)</h2>
            <div className="grid grid-cols-3 gap-6">
              {Object.keys(INSURERS).map(key => (
                <InsurerCard key={key} insurerKey={key} showEncrypted={true} />
              ))}
            </div>
            <div className="bg-gray-900 rounded-xl p-6 text-white">
              <div className="flex items-center gap-2 mb-4">
                <EyeSlashIcon className="w-5 h-5 text-purple-400" />
                <span className="font-medium">El servidor ve SOLO ciphertext:</span>
              </div>
              <div className="grid grid-cols-3 gap-4">
                {Object.entries(INSURERS).map(([key, config]) => (
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
              <div className="bg-amber-50 rounded-xl border border-amber-200 p-6">
                <h3 className="font-bold text-gray-900 mb-2">Propuesta #001</h3>
                <p className="text-gray-700 mb-4">
                  Entrenar modelo Random Forest de deteccion de fraude con datos cifrados de los 3 miembros.
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
              <VotingDisplay phase={votingPhase} votes={{ alpha: true, beta: true, gamma: true }} />
            </div>
            <div className="space-y-6">
              <h3 className="font-bold text-gray-900 text-lg">Proceso Commit-Reveal</h3>
              <div className="space-y-4">
                <div className={`p-4 rounded-lg border-2 ${votingPhase === 'commit' ? 'border-amber-500 bg-amber-50' : 'border-gray-200 bg-gray-50'}`}>
                  <div className="flex items-center gap-2 mb-2">
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center ${votingPhase === 'commit' ? 'bg-amber-500 text-white' : 'bg-gray-300 text-gray-600'}`}>1</div>
                    <span className="font-bold">Fase Commit</span>
                  </div>
                  <p className="text-sm text-gray-600 ml-8">
                    Cada aseguradora envia un hash de su voto. Nadie puede ver como votaron los demas.
                  </p>
                </div>
                <div className={`p-4 rounded-lg border-2 ${votingPhase === 'reveal' ? 'border-green-500 bg-green-50' : 'border-gray-200 bg-gray-50'}`}>
                  <div className="flex items-center gap-2 mb-2">
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center ${votingPhase === 'reveal' ? 'bg-green-500 text-white' : 'bg-gray-300 text-gray-600'}`}>2</div>
                    <span className="font-bold">Fase Reveal</span>
                  </div>
                  <p className="text-sm text-gray-600 ml-8">
                    Los votos se revelan y verifican contra los hashes. Resultado registrado en blockchain.
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
              <div className="bg-purple-50 rounded-xl border border-purple-200 p-6">
                <h3 className="font-bold text-gray-900 mb-4">Configuracion del Modelo</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Algoritmo:</span>
                    <span className="font-medium">Random Forest Classifier</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Arboles:</span>
                    <span className="font-medium">100</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Profundidad maxima:</span>
                    <span className="font-medium">10</span>
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
                    El modelo fue entrenado exitosamente sobre 15,000 reclamos cifrados de 3 aseguradoras.
                    Los datos originales nunca fueron expuestos.
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
              <h2 className="text-2xl font-bold text-gray-900">Analisis de Reclamo Sospechoso</h2>
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <DocumentTextIcon className="w-5 h-5 text-amber-600" />
                  Reclamo: {SUSPICIOUS_CLAIM.id}
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <span className="text-xs text-gray-500 uppercase">Monto</span>
                    <div className="font-bold text-xl text-red-600">${SUSPICIOUS_CLAIM.amount.toLocaleString()}</div>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500 uppercase">Tipo</span>
                    <div className="font-bold">{SUSPICIOUS_CLAIM.type}</div>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500 uppercase">Edad Poliza</span>
                    <div className="font-bold">{SUSPICIOUS_CLAIM.policyAge} meses</div>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500 uppercase">Dias para Reportar</span>
                    <div className="font-bold text-red-600">{SUSPICIOUS_CLAIM.daysToReport} dias</div>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500 uppercase">Testigos</span>
                    <div className="font-bold text-red-600">No</div>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500 uppercase">Reporte Policial</span>
                    <div className="font-bold text-red-600">No</div>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500 uppercase">Reclamos Previos</span>
                    <div className="font-bold">{SUSPICIOUS_CLAIM.previousClaims}</div>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500 uppercase">Edad Cliente</span>
                    <div className="font-bold">{SUSPICIOUS_CLAIM.customerAge} anos</div>
                  </div>
                </div>
              </div>
              <div className="bg-gray-900 rounded-xl p-4 text-white">
                <div className="text-sm text-gray-400 mb-2">Vector de features cifrado:</div>
                <div className="font-mono text-xs text-purple-400 break-all">
                  {generateCiphertext(128)}
                </div>
              </div>
            </div>
            <div className="space-y-6">
              <h3 className="font-bold text-gray-900 text-lg">Resultado del Modelo</h3>
              <PredictionResult probability={0.87} isLoading={predictionLoading} />
              {showPrediction && (
                <div className="bg-amber-50 rounded-xl border border-amber-200 p-4">
                  <h4 className="font-bold text-gray-900 mb-2">Factores de Riesgo Detectados:</h4>
                  <ul className="space-y-2 text-sm">
                    <li className="flex items-center gap-2">
                      <ExclamationTriangleIcon className="w-4 h-4 text-red-500" />
                      <span>Monto muy alto ($72,000) para tipo de reclamo</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <ExclamationTriangleIcon className="w-4 h-4 text-red-500" />
                      <span>Poliza nueva (4 meses)</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <ExclamationTriangleIcon className="w-4 h-4 text-red-500" />
                      <span>Reporte tardio (65 dias)</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <ExclamationTriangleIcon className="w-4 h-4 text-red-500" />
                      <span>Sin testigos ni reporte policial</span>
                    </li>
                  </ul>
                </div>
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
                <div className="text-4xl font-bold text-green-600 mb-2">+18%</div>
                <div className="text-gray-700 font-medium">Mejora en deteccion</div>
                <div className="text-sm text-gray-500">vs mejor modelo individual</div>
              </div>
              <div className="bg-purple-50 rounded-xl border border-purple-200 p-6 text-center">
                <div className="text-4xl font-bold text-purple-600 mb-2">0</div>
                <div className="text-gray-700 font-medium">Datos compartidos</div>
                <div className="text-sm text-gray-500">Todo cifrado con CKKS</div>
              </div>
              <div className="bg-amber-50 rounded-xl border border-amber-200 p-6 text-center">
                <div className="text-4xl font-bold text-amber-600 mb-2">$12M</div>
                <div className="text-gray-700 font-medium">Potencial ahorro anual</div>
                <div className="text-sm text-gray-500">Por aseguradora estimado</div>
              </div>
            </div>
            <div className="bg-gradient-to-r from-amber-50 to-rose-50 rounded-xl border border-amber-200 p-6">
              <h3 className="font-bold text-gray-900 mb-4">Resumen de Privacidad</h3>
              <div className="grid grid-cols-2 gap-6">
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <CheckCircleIcon className="w-5 h-5 text-green-500" />
                    <span>Datos de clientes nunca expuestos</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircleIcon className="w-5 h-5 text-green-500" />
                    <span>Encriptacion CKKS 128-bit</span>
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
                    <span>Cumplimiento GDPR / regulaciones locales</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircleIcon className="w-5 h-5 text-green-500" />
                    <span>Control total de datos por cada aseguradora</span>
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
