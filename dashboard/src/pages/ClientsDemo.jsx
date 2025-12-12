import { useState, useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import {
  BuildingOffice2Icon,
  ShoppingBagIcon,
  LockClosedIcon,
  LockOpenIcon,
  CloudArrowUpIcon,
  CpuChipIcon,
  ChartBarIcon,
  CheckCircleIcon,
  PlayIcon,
  ArrowPathIcon,
  SparklesIcon,
  EyeIcon,
  EyeSlashIcon,
  ServerIcon
} from '@heroicons/react/24/outline'

// Mock data for clients
const FINBANK_DATA = [
  { id: 'FB001', age: 35, income: 75000, credit_score: 720, loan_amount: 25000, risk: 0 },
  { id: 'FB002', age: 28, income: 45000, credit_score: 650, loan_amount: 15000, risk: 1 },
  { id: 'FB003', age: 45, income: 120000, credit_score: 780, loan_amount: 50000, risk: 0 },
  { id: 'FB004', age: 52, income: 95000, credit_score: 710, loan_amount: 35000, risk: 0 },
  { id: 'FB005', age: 23, income: 32000, credit_score: 580, loan_amount: 10000, risk: 1 },
]

const RETAILCORP_DATA = [
  { id: 'RC001', age: 34, income: 71000, credit_score: 715, loan_amount: 24000, risk: 0 },
  { id: 'RC002', age: 29, income: 47000, credit_score: 645, loan_amount: 16000, risk: 1 },
  { id: 'RC003', age: 43, income: 115000, credit_score: 775, loan_amount: 48000, risk: 0 },
  { id: 'RC004', age: 51, income: 92000, credit_score: 705, loan_amount: 34000, risk: 0 },
  { id: 'RC005', age: 25, income: 34000, credit_score: 585, loan_amount: 11000, risk: 1 },
]

// Generate random encrypted value
const generateEncrypted = () => `ENC[${Math.random().toString(36).substring(2, 14)}]`

export default function ClientsDemo() {
  const { t, i18n } = useTranslation()
  const currentLang = i18n.language?.startsWith('es') ? 'es' : 'en'

  const [step, setStep] = useState(0)
  const [isRunning, setIsRunning] = useState(false)
  const [client1Encrypted, setClient1Encrypted] = useState(false)
  const [client2Encrypted, setClient2Encrypted] = useState(false)
  const [client1Sent, setClient1Sent] = useState(false)
  const [client2Sent, setClient2Sent] = useState(false)
  const [trainingProgress, setTrainingProgress] = useState(0)
  const [modelTrained, setModelTrained] = useState(false)
  const [encryptionProgress1, setEncryptionProgress1] = useState(0)
  const [encryptionProgress2, setEncryptionProgress2] = useState(0)
  const [showPrediction, setShowPrediction] = useState(false)

  const texts = {
    es: {
      title: 'Demo de Clientes FHE',
      subtitle: 'Simulación de cifrado homomórfico y entrenamiento federado',
      startDemo: 'Iniciar Demo',
      restartDemo: 'Reiniciar Demo',
      running: 'Ejecutando...',
      client1: 'FinBank Corp',
      client2: 'RetailCorp LATAM',
      rawData: 'Datos Originales',
      encryptedData: 'Datos Cifrados',
      sensitive: 'SENSIBLE',
      secure: 'SEGURO',
      encrypting: 'Cifrando...',
      sending: 'Enviando...',
      sent: 'Enviado',
      server: 'Servidor FHE',
      training: 'Entrenando Random Forest',
      modelReady: 'Modelo Listo',
      accuracy: 'Precisión',
      prediction: 'Predicción',
      lowRisk: 'Bajo Riesgo',
      highRisk: 'Alto Riesgo',
      step1: 'Paso 1: Datos sin cifrar (sensibles)',
      step2: 'Paso 2: Cifrando con FHE',
      step3: 'Paso 3: Enviando al consorcio',
      step4: 'Paso 4: Entrenamiento federado',
      step5: 'Paso 5: Modelo y predicción',
      warning: 'Estos datos NO se pueden compartir directamente',
      safe: 'Datos seguros para compartir',
      privacy: 'Los datos originales NUNCA salen del cliente',
      records: 'registros',
      trees: 'árboles construidos'
    },
    en: {
      title: 'FHE Clients Demo',
      subtitle: 'Homomorphic encryption and federated training simulation',
      startDemo: 'Start Demo',
      restartDemo: 'Restart Demo',
      running: 'Running...',
      client1: 'FinBank Corp',
      client2: 'RetailCorp LATAM',
      rawData: 'Raw Data',
      encryptedData: 'Encrypted Data',
      sensitive: 'SENSITIVE',
      secure: 'SECURE',
      encrypting: 'Encrypting...',
      sending: 'Sending...',
      sent: 'Sent',
      server: 'FHE Server',
      training: 'Training Random Forest',
      modelReady: 'Model Ready',
      accuracy: 'Accuracy',
      prediction: 'Prediction',
      lowRisk: 'Low Risk',
      highRisk: 'High Risk',
      step1: 'Step 1: Unencrypted data (sensitive)',
      step2: 'Step 2: Encrypting with FHE',
      step3: 'Step 3: Sending to consortium',
      step4: 'Step 4: Federated training',
      step5: 'Step 5: Model and prediction',
      warning: 'This data CANNOT be shared directly',
      safe: 'Data safe to share',
      privacy: 'Original data NEVER leaves the client',
      records: 'records',
      trees: 'trees built'
    }
  }

  const txt = texts[currentLang]

  const resetDemo = () => {
    setStep(0)
    setIsRunning(false)
    setClient1Encrypted(false)
    setClient2Encrypted(false)
    setClient1Sent(false)
    setClient2Sent(false)
    setTrainingProgress(0)
    setModelTrained(false)
    setEncryptionProgress1(0)
    setEncryptionProgress2(0)
    setShowPrediction(false)
  }

  const runDemo = async () => {
    resetDemo()
    setIsRunning(true)

    // Step 1: Show raw data
    setStep(1)
    await new Promise(r => setTimeout(r, 2000))

    // Step 2: Encrypt client 1
    setStep(2)
    for (let i = 0; i <= 100; i += 5) {
      setEncryptionProgress1(i)
      await new Promise(r => setTimeout(r, 50))
    }
    setClient1Encrypted(true)
    await new Promise(r => setTimeout(r, 500))

    // Encrypt client 2
    for (let i = 0; i <= 100; i += 5) {
      setEncryptionProgress2(i)
      await new Promise(r => setTimeout(r, 50))
    }
    setClient2Encrypted(true)
    await new Promise(r => setTimeout(r, 1000))

    // Step 3: Send to server
    setStep(3)
    await new Promise(r => setTimeout(r, 800))
    setClient1Sent(true)
    await new Promise(r => setTimeout(r, 800))
    setClient2Sent(true)
    await new Promise(r => setTimeout(r, 1000))

    // Step 4: Train model
    setStep(4)
    for (let i = 0; i <= 100; i += 2) {
      setTrainingProgress(i)
      await new Promise(r => setTimeout(r, 50))
    }
    setModelTrained(true)
    await new Promise(r => setTimeout(r, 1000))

    // Step 5: Show prediction
    setStep(5)
    await new Promise(r => setTimeout(r, 500))
    setShowPrediction(true)
    setIsRunning(false)
  }

  const DataTable = ({ data, encrypted, title, icon: Icon, color }) => (
    <div className={`bg-white rounded-xl border-2 ${encrypted ? 'border-green-200' : 'border-red-200'} overflow-hidden`}>
      <div className={`px-4 py-3 ${encrypted ? 'bg-green-50' : 'bg-red-50'} flex items-center justify-between`}>
        <div className="flex items-center gap-2">
          <Icon className={`w-5 h-5 ${color}`} />
          <span className="font-semibold text-slate-800">{title}</span>
        </div>
        <span className={`text-xs px-2 py-1 rounded-full font-medium ${encrypted ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
          {encrypted ? txt.secure : txt.sensitive}
        </span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-3 py-2 text-left text-slate-600">ID</th>
              <th className="px-3 py-2 text-left text-slate-600">Age</th>
              <th className="px-3 py-2 text-left text-slate-600">Income</th>
              <th className="px-3 py-2 text-left text-slate-600">Score</th>
              <th className="px-3 py-2 text-left text-slate-600">Risk</th>
            </tr>
          </thead>
          <tbody>
            {data.slice(0, 4).map((row, i) => (
              <tr key={i} className="border-t border-slate-100">
                <td className="px-3 py-2 font-mono text-slate-700">
                  {encrypted ? generateEncrypted() : row.id}
                </td>
                <td className="px-3 py-2 font-mono text-slate-700">
                  {encrypted ? generateEncrypted() : row.age}
                </td>
                <td className="px-3 py-2 font-mono text-slate-700">
                  {encrypted ? generateEncrypted() : `$${row.income.toLocaleString()}`}
                </td>
                <td className="px-3 py-2 font-mono text-slate-700">
                  {encrypted ? generateEncrypted() : row.credit_score}
                </td>
                <td className="px-3 py-2">
                  {encrypted ? (
                    <span className="text-green-600 font-mono">{generateEncrypted()}</span>
                  ) : (
                    <span className={`px-2 py-0.5 rounded text-xs ${row.risk ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
                      {row.risk ? 'High' : 'Low'}
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      {/* Header */}
      <div className="max-w-6xl mx-auto mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white flex items-center gap-3">
              <SparklesIcon className="w-8 h-8 text-amber-400" />
              {txt.title}
            </h1>
            <p className="text-slate-400 mt-1">{txt.subtitle}</p>
          </div>
          <button
            onClick={isRunning ? null : (step > 0 ? resetDemo : runDemo)}
            disabled={isRunning}
            className={`flex items-center gap-2 px-6 py-3 rounded-xl font-medium transition ${
              isRunning
                ? 'bg-slate-700 text-slate-400 cursor-not-allowed'
                : step > 0
                ? 'bg-slate-600 text-white hover:bg-slate-500'
                : 'bg-amber-500 text-white hover:bg-amber-600'
            }`}
          >
            {isRunning ? (
              <>
                <ArrowPathIcon className="w-5 h-5 animate-spin" />
                {txt.running}
              </>
            ) : step > 0 ? (
              <>
                <ArrowPathIcon className="w-5 h-5" />
                {txt.restartDemo}
              </>
            ) : (
              <>
                <PlayIcon className="w-5 h-5" />
                {txt.startDemo}
              </>
            )}
          </button>
        </div>

        {/* Progress Steps */}
        <div className="flex items-center justify-between mt-6 bg-slate-800/50 rounded-xl p-4">
          {[1, 2, 3, 4, 5].map((s) => (
            <div key={s} className="flex items-center">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold transition-all ${
                step >= s ? 'bg-amber-500 text-white' : 'bg-slate-700 text-slate-400'
              }`}>
                {step > s ? <CheckCircleIcon className="w-6 h-6" /> : s}
              </div>
              {s < 5 && (
                <div className={`w-16 md:w-24 h-1 mx-2 rounded ${step > s ? 'bg-amber-500' : 'bg-slate-700'}`} />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto">
        {/* Step Labels */}
        <div className="text-center mb-6">
          <span className={`inline-block px-4 py-2 rounded-lg text-sm font-medium ${
            step === 0 ? 'bg-slate-700 text-slate-300' :
            step === 1 ? 'bg-red-500/20 text-red-300' :
            step === 2 ? 'bg-yellow-500/20 text-yellow-300' :
            step === 3 ? 'bg-blue-500/20 text-blue-300' :
            step === 4 ? 'bg-purple-500/20 text-purple-300' :
            'bg-green-500/20 text-green-300'
          }`}>
            {step === 0 && (currentLang === 'es' ? 'Presiona "Iniciar Demo" para comenzar' : 'Press "Start Demo" to begin')}
            {step === 1 && txt.step1}
            {step === 2 && txt.step2}
            {step === 3 && txt.step3}
            {step === 4 && txt.step4}
            {step === 5 && txt.step5}
          </span>
        </div>

        {/* Clients Section */}
        <div className="grid md:grid-cols-2 gap-6 mb-8">
          {/* Client 1: FinBank */}
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-blue-500 rounded-xl flex items-center justify-center">
                <BuildingOffice2Icon className="w-7 h-7 text-white" />
              </div>
              <div>
                <h3 className="text-white font-semibold">{txt.client1}</h3>
                <p className="text-slate-400 text-sm">25 {txt.records}</p>
              </div>
              {client1Sent && (
                <CheckCircleIcon className="w-6 h-6 text-green-400 ml-auto" />
              )}
            </div>

            <DataTable
              data={FINBANK_DATA}
              encrypted={client1Encrypted}
              title={client1Encrypted ? txt.encryptedData : txt.rawData}
              icon={client1Encrypted ? LockClosedIcon : LockOpenIcon}
              color={client1Encrypted ? 'text-green-600' : 'text-red-600'}
            />

            {/* Encryption Progress */}
            {step === 2 && !client1Encrypted && (
              <div className="bg-slate-800 rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-yellow-400 text-sm font-medium">{txt.encrypting}</span>
                  <span className="text-slate-400 text-sm">{encryptionProgress1}%</span>
                </div>
                <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-yellow-500 transition-all duration-100"
                    style={{ width: `${encryptionProgress1}%` }}
                  />
                </div>
              </div>
            )}

            {/* Warning/Safe Message */}
            {step >= 1 && (
              <div className={`flex items-center gap-2 text-sm ${client1Encrypted ? 'text-green-400' : 'text-red-400'}`}>
                {client1Encrypted ? <EyeSlashIcon className="w-4 h-4" /> : <EyeIcon className="w-4 h-4" />}
                {client1Encrypted ? txt.safe : txt.warning}
              </div>
            )}
          </div>

          {/* Client 2: RetailCorp */}
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-purple-500 rounded-xl flex items-center justify-center">
                <ShoppingBagIcon className="w-7 h-7 text-white" />
              </div>
              <div>
                <h3 className="text-white font-semibold">{txt.client2}</h3>
                <p className="text-slate-400 text-sm">30 {txt.records}</p>
              </div>
              {client2Sent && (
                <CheckCircleIcon className="w-6 h-6 text-green-400 ml-auto" />
              )}
            </div>

            <DataTable
              data={RETAILCORP_DATA}
              encrypted={client2Encrypted}
              title={client2Encrypted ? txt.encryptedData : txt.rawData}
              icon={client2Encrypted ? LockClosedIcon : LockOpenIcon}
              color={client2Encrypted ? 'text-green-600' : 'text-red-600'}
            />

            {/* Encryption Progress */}
            {step === 2 && client1Encrypted && !client2Encrypted && (
              <div className="bg-slate-800 rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-yellow-400 text-sm font-medium">{txt.encrypting}</span>
                  <span className="text-slate-400 text-sm">{encryptionProgress2}%</span>
                </div>
                <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-yellow-500 transition-all duration-100"
                    style={{ width: `${encryptionProgress2}%` }}
                  />
                </div>
              </div>
            )}

            {/* Warning/Safe Message */}
            {step >= 1 && (
              <div className={`flex items-center gap-2 text-sm ${client2Encrypted ? 'text-green-400' : 'text-red-400'}`}>
                {client2Encrypted ? <EyeSlashIcon className="w-4 h-4" /> : <EyeIcon className="w-4 h-4" />}
                {client2Encrypted ? txt.safe : txt.warning}
              </div>
            )}
          </div>
        </div>

        {/* Server Section */}
        {step >= 3 && (
          <div className="bg-slate-800/50 rounded-2xl p-6 border border-slate-700">
            <div className="flex items-center gap-4 mb-6">
              <div className="w-14 h-14 bg-cyan-500 rounded-xl flex items-center justify-center">
                <ServerIcon className="w-8 h-8 text-white" />
              </div>
              <div>
                <h3 className="text-white text-xl font-semibold">{txt.server}</h3>
                <p className="text-slate-400 text-sm">
                  {client1Sent && client2Sent ? '55 ' + txt.records : txt.sending}
                </p>
              </div>
            </div>

            {/* Training Progress */}
            {step >= 4 && (
              <div className="space-y-4">
                <div className="bg-slate-900 rounded-xl p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <CpuChipIcon className="w-5 h-5 text-purple-400" />
                      <span className="text-white font-medium">{txt.training}</span>
                    </div>
                    <span className="text-slate-400 text-sm">{trainingProgress} {txt.trees}</span>
                  </div>
                  <div className="h-3 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-100"
                      style={{ width: `${trainingProgress}%` }}
                    />
                  </div>
                </div>

                {/* Model Results */}
                {modelTrained && (
                  <div className="grid md:grid-cols-3 gap-4">
                    <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-4 text-center">
                      <ChartBarIcon className="w-8 h-8 text-green-400 mx-auto mb-2" />
                      <div className="text-2xl font-bold text-green-400">92%</div>
                      <div className="text-slate-400 text-sm">{txt.accuracy}</div>
                    </div>
                    <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-4 text-center">
                      <ChartBarIcon className="w-8 h-8 text-blue-400 mx-auto mb-2" />
                      <div className="text-2xl font-bold text-blue-400">89%</div>
                      <div className="text-slate-400 text-sm">Precision</div>
                    </div>
                    <div className="bg-purple-500/10 border border-purple-500/30 rounded-xl p-4 text-center">
                      <ChartBarIcon className="w-8 h-8 text-purple-400 mx-auto mb-2" />
                      <div className="text-2xl font-bold text-purple-400">87%</div>
                      <div className="text-slate-400 text-sm">Recall</div>
                    </div>
                  </div>
                )}

                {/* Prediction Demo */}
                {showPrediction && (
                  <div className="bg-slate-900 rounded-xl p-6 mt-4">
                    <h4 className="text-white font-semibold mb-4 flex items-center gap-2">
                      <SparklesIcon className="w-5 h-5 text-amber-400" />
                      {txt.prediction}
                    </h4>
                    <div className="grid md:grid-cols-2 gap-6">
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-400">Age:</span>
                          <span className="text-white">35</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-400">Income:</span>
                          <span className="text-white">$65,000</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-400">Credit Score:</span>
                          <span className="text-white">680</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-400">Loan Amount:</span>
                          <span className="text-white">$20,000</span>
                        </div>
                      </div>
                      <div className="flex items-center justify-center">
                        <div className="text-center">
                          <div className="w-24 h-24 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-3">
                            <CheckCircleIcon className="w-12 h-12 text-green-400" />
                          </div>
                          <div className="text-green-400 font-bold text-xl">{txt.lowRisk}</div>
                          <div className="text-slate-400 text-sm">Score: 23%</div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Privacy Notice */}
        {step >= 2 && (
          <div className="mt-6 text-center">
            <div className="inline-flex items-center gap-2 bg-green-500/10 border border-green-500/30 rounded-full px-6 py-3">
              <LockClosedIcon className="w-5 h-5 text-green-400" />
              <span className="text-green-400 font-medium">{txt.privacy}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
