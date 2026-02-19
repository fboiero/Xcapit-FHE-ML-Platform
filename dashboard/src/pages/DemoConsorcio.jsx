import { useState } from 'react'
import {
  LockClosedIcon,
  ServerIcon,
  CpuChipIcon,
  ShieldCheckIcon,
  EyeSlashIcon,
  ArrowRightIcon,
  PlayIcon,
  CheckCircleIcon,
  BuildingOffice2Icon,
  HeartIcon
} from '@heroicons/react/24/outline'

// ========== CASO 1: BANCOS ==========
const BANKS_DATA = {
  bancoAlpha: {
    name: 'Banco Alpha',
    logo: 'A',
    customers: 125000,
    borderClass: 'border-blue-500',
    bgClass: 'bg-blue-50',
    logoClass: 'bg-blue-600',
    data: [
      { id: 'TX-8847', amount: '$15,420', type: 'Transferencia', flagged: false },
      { id: 'TX-8848', amount: '$89,500', type: 'Retiro', flagged: true },
      { id: 'TX-8849', amount: '$2,340', type: 'Compra', flagged: false },
      { id: 'TX-8850', amount: '$156,000', type: 'Transferencia', flagged: true },
    ],
    stats: { transactions: '2.3M', fraudRate: '0.8%', avgAmount: '$4,520' }
  },
  bancoBeta: {
    name: 'Banco Beta',
    logo: 'B',
    customers: 89000,
    borderClass: 'border-emerald-500',
    bgClass: 'bg-emerald-50',
    logoClass: 'bg-emerald-600',
    data: [
      { id: 'BB-2201', amount: '$45,600', type: 'Wire', flagged: true },
      { id: 'BB-2202', amount: '$890', type: 'Compra', flagged: false },
      { id: 'BB-2203', amount: '$23,400', type: 'Transferencia', flagged: false },
      { id: 'BB-2204', amount: '$178,000', type: 'Retiro', flagged: true },
    ],
    stats: { transactions: '1.1M', fraudRate: '1.2%', avgAmount: '$3,890' }
  },
  bancoGamma: {
    name: 'Banco Gamma',
    logo: 'G',
    customers: 67000,
    borderClass: 'border-purple-500',
    bgClass: 'bg-purple-50',
    logoClass: 'bg-purple-600',
    data: [
      { id: 'BG-5501', amount: '$12,300', type: 'Compra', flagged: false },
      { id: 'BG-5502', amount: '$67,800', type: 'Transferencia', flagged: true },
      { id: 'BG-5503', amount: '$4,560', type: 'Retiro', flagged: false },
      { id: 'BG-5504', amount: '$234,000', type: 'Wire', flagged: true },
    ],
    stats: { transactions: '890K', fraudRate: '0.9%', avgAmount: '$5,120' }
  }
}

// ========== CASO 2: HOSPITALES ==========
const HOSPITALS_DATA = {
  hospitalCentral: {
    name: 'Hospital Central',
    logo: 'HC',
    patients: 45000,
    borderClass: 'border-rose-500',
    bgClass: 'bg-rose-50',
    logoClass: 'bg-rose-600',
    data: [
      { id: 'PAC-1001', age: 67, diagnosis: 'Diabetes T2', risk: 'Alto' },
      { id: 'PAC-1002', age: 45, diagnosis: 'Hipertension', risk: 'Medio' },
      { id: 'PAC-1003', age: 72, diagnosis: 'Cardiopatia', risk: 'Alto' },
      { id: 'PAC-1004', age: 38, diagnosis: 'Asma', risk: 'Bajo' },
    ],
    stats: { records: '890K', conditions: '156', avgAge: '52' }
  },
  hospitalNorte: {
    name: 'Hospital Norte',
    logo: 'HN',
    patients: 32000,
    borderClass: 'border-cyan-500',
    bgClass: 'bg-cyan-50',
    logoClass: 'bg-cyan-600',
    data: [
      { id: 'HN-4421', age: 55, diagnosis: 'Cancer Pulmon', risk: 'Alto' },
      { id: 'HN-4422', age: 29, diagnosis: 'Anemia', risk: 'Bajo' },
      { id: 'HN-4423', age: 61, diagnosis: 'Diabetes T1', risk: 'Medio' },
      { id: 'HN-4424', age: 78, diagnosis: 'Alzheimer', risk: 'Alto' },
    ],
    stats: { records: '620K', conditions: '142', avgAge: '58' }
  },
  hospitalSur: {
    name: 'Clinica del Sur',
    logo: 'CS',
    patients: 28000,
    borderClass: 'border-amber-500',
    bgClass: 'bg-amber-50',
    logoClass: 'bg-amber-600',
    data: [
      { id: 'CS-7801', age: 43, diagnosis: 'Obesidad', risk: 'Medio' },
      { id: 'CS-7802', age: 66, diagnosis: 'Parkinson', risk: 'Alto' },
      { id: 'CS-7803', age: 51, diagnosis: 'Artritis', risk: 'Bajo' },
      { id: 'CS-7804', age: 70, diagnosis: 'EPOC', risk: 'Alto' },
    ],
    stats: { records: '480K', conditions: '128', avgAge: '49' }
  }
}

const generateCiphertext = (length = 64) => {
  const chars = '0123456789abcdef'
  return Array.from({ length }, () => chars[Math.floor(Math.random() * chars.length)]).join('')
}

// Configuracion por caso de uso
const USE_CASES = {
  banks: {
    title: 'Deteccion de Fraude con ML',
    subtitle: 'Machine Learning colaborativo sin compartir datos',
    icon: BuildingOffice2Icon,
    data: BANKS_DATA,
    entityName: 'banco',
    dataLabel: 'clientes',
    problem: {
      title: 'El Dilema del Fraude Bancario',
      description: 'Un modelo de ML entrenado con datos de 3 bancos detecta 3x mas fraude. Pero compartir transacciones de clientes es ilegal.',
      barriers: ['Secreto bancario', 'Competencia directa', 'Regulacion financiera'],
      solution: 'Con FHE: entrenar ML sobre datos cifrados. El servidor procesa pero NUNCA ve los datos originales.'
    },
    steps: [
      { title: 'El Problema', description: 'Los bancos quieren colaborar para mejorar su ML, pero NO pueden compartir datos de clientes.' },
      { title: 'Datos Sensibles', description: 'Cada banco tiene transacciones con montos reales, nombres de clientes, y patrones de fraude.' },
      { title: 'Cifrado Local', description: 'Cada banco cifra sus datos ANTES de enviarlos. La clave privada NUNCA sale del banco.' },
      { title: 'Vista del Servidor', description: 'El servidor recibe SOLO ciphertext. No puede ver montos, nombres, ni ningun dato real.' },
      { title: 'ML sobre Cifrado', description: 'El modelo de ML se entrena sobre los datos CIFRADOS. Aprende patrones SIN ver los datos.' },
      { title: 'Predicciones ML', description: 'El servidor envia predicciones cifradas. Solo cada banco puede descifrar SUS resultados.' },
    ],
    results: {
      bancoAlpha: { metric1: 847, metric1Label: 'Predicciones ML', metric2: '$12.4M', metric2Label: 'Fraudes predichos', accuracy: '94.2%' },
      bancoBeta: { metric1: 523, metric1Label: 'Predicciones ML', metric2: '$8.7M', metric2Label: 'Fraudes predichos', accuracy: '93.8%' },
      bancoGamma: { metric1: 412, metric1Label: 'Predicciones ML', metric2: '$6.2M', metric2Label: 'Fraudes predichos', accuracy: '94.5%' },
    },
    summary: {
      stat1: 'ML 3x mas preciso',
      stat1sub: 'Entrenado con datos de 3 bancos',
      stat2: 'Datos originales: NUNCA visibles',
      stat2sub: 'Solo el modelo vio ciphertext',
      stat3: 'Solo ves TUS predicciones',
      stat3sub: 'Cada banco descifra sus resultados',
    },
    keyInsight: 'El servidor ejecuto Machine Learning sobre millones de transacciones CIFRADAS. Obtuvo predicciones de fraude, pero NUNCA vio un solo monto real ni nombre de cliente.'
  },
  health: {
    title: 'Investigacion Medica con ML',
    subtitle: 'Machine Learning colaborativo sin exponer pacientes',
    icon: HeartIcon,
    data: HOSPITALS_DATA,
    entityName: 'hospital',
    dataLabel: 'pacientes',
    problem: {
      title: 'El Dilema de la Investigacion Medica',
      description: 'Un modelo predictivo necesita miles de casos para ser preciso. Pero compartir historiales medicos viola HIPAA y la privacidad del paciente.',
      barriers: ['HIPAA / Ley de proteccion', 'Datos ultra-sensibles', 'Riesgo reputacional'],
      solution: 'Con FHE: entrenar ML sobre datos cifrados. El servidor procesa pero NUNCA ve diagnosticos ni identificaciones.'
    },
    steps: [
      { title: 'El Problema', description: 'Los hospitales quieren crear un modelo predictivo, pero NO pueden compartir historiales de pacientes.' },
      { title: 'Datos Sensibles', description: 'Cada hospital tiene registros con diagnosticos reales, edades, nombres, y tratamientos.' },
      { title: 'Cifrado Local', description: 'Cada hospital cifra sus registros ANTES de enviarlos. La clave privada NUNCA sale del hospital.' },
      { title: 'Vista del Servidor', description: 'El servidor recibe SOLO ciphertext. No puede ver diagnosticos, nombres, ni ningun dato real.' },
      { title: 'ML sobre Cifrado', description: 'El modelo de ML se entrena sobre los datos CIFRADOS. Aprende a predecir SIN ver pacientes.' },
      { title: 'Predicciones ML', description: 'El servidor envia predicciones cifradas. Solo cada hospital puede descifrar SUS resultados.' },
    ],
    results: {
      hospitalCentral: { metric1: 234, metric1Label: 'Predicciones ML', metric2: '89%', metric2Label: 'Riesgos predichos', accuracy: '91.3%' },
      hospitalNorte: { metric1: 187, metric1Label: 'Predicciones ML', metric2: '92%', metric2Label: 'Riesgos predichos', accuracy: '90.8%' },
      hospitalSur: { metric1: 156, metric1Label: 'Predicciones ML', metric2: '87%', metric2Label: 'Riesgos predichos', accuracy: '91.1%' },
    },
    summary: {
      stat1: 'ML mas preciso',
      stat1sub: 'Entrenado con datos de 3 hospitales',
      stat2: 'Historiales: NUNCA visibles',
      stat2sub: 'Solo el modelo vio ciphertext',
      stat3: 'Solo ves TUS predicciones',
      stat3sub: 'Cada hospital descifra sus resultados',
    },
    keyInsight: 'El servidor ejecuto Machine Learning sobre miles de historiales CIFRADOS. Obtuvo predicciones de riesgo, pero NUNCA vio un solo diagnostico real ni nombre de paciente.'
  }
}

export default function DemoConsorcio() {
  const [activeCase, setActiveCase] = useState('banks')
  const [step, setStep] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [encryptedData, setEncryptedData] = useState({})
  const [serverView, setServerView] = useState([])
  const [modelProgress, setModelProgress] = useState(0)
  const [results, setResults] = useState(null)
  const [logs, setLogs] = useState([])

  const config = USE_CASES[activeCase]
  const entities = config.data

  const addLog = (message, type = 'info') => {
    setLogs(prev => [...prev, { message, type, time: new Date().toLocaleTimeString() }])
  }

  const resetDemo = () => {
    setStep(0)
    setEncryptedData({})
    setServerView([])
    setModelProgress(0)
    setResults(null)
    setLogs([])
  }

  const switchCase = (newCase) => {
    setActiveCase(newCase)
    resetDemo()
  }

  const runStep = async (stepNum) => {
    setStep(stepNum)
    const entityKeys = Object.keys(entities)
    const entityNames = Object.values(entities).map(e => e.name)

    switch(stepNum) {
      case 1:
        addLog(`Mostrando datos sensibles de cada ${config.entityName}...`, 'info')
        addLog('ESTOS DATOS NUNCA SALEN DE CADA INSTITUCION', 'warning')
        break

      case 2:
        for (let i = 0; i < entityKeys.length; i++) {
          addLog(`${entityNames[i]}: Cifrando con FHE (clave privada local)...`, 'encrypt')
          await new Promise(r => setTimeout(r, 800))
          setEncryptedData(prev => ({ ...prev, [entityKeys[i]]: generateCiphertext(128) }))
        }
        addLog('Solo el ciphertext viaja al servidor, NUNCA los datos', 'success')
        break

      case 3:
        addLog('Servidor recibe SOLO ciphertext...', 'server')
        await new Promise(r => setTimeout(r, 500))
        setServerView(entityNames.map((name, i) => ({
          from: name,
          cipher: generateCiphertext(64),
          size: `${Math.floor(50 + Math.random() * 100)} MB`
        })))
        addLog('El servidor VE estos bytes pero NO PUEDE descifrarlos', 'warning')
        addLog('Sin clave privada = datos originales invisibles', 'warning')
        break

      case 4:
        addLog('Iniciando MACHINE LEARNING sobre datos CIFRADOS...', 'train')
        for (let i = 0; i <= 100; i += 5) {
          setModelProgress(i)
          await new Promise(r => setTimeout(r, 150))
        }
        addLog('Modelo ML entrenado = PREDICCIONES disponibles', 'success')
        addLog('DATOS ORIGINALES = siguen siendo invisibles', 'success')
        break

      case 5:
        addLog('Generando PREDICCIONES del modelo ML (cifradas)...', 'result')
        await new Promise(r => setTimeout(r, 1000))
        setResults(config.results)
        addLog(`Cada ${config.entityName} descifra SUS predicciones`, 'success')
        addLog('Resultado: VES las predicciones, NO los datos de otros', 'success')
        break
    }
  }

  const playDemo = async () => {
    setIsPlaying(true)
    resetDemo()

    for (let i = 0; i <= 5; i++) {
      await runStep(i)
      await new Promise(r => setTimeout(r, 2000))
    }

    setIsPlaying(false)
  }

  const EntityCard = ({ entityKey, entity, showData = false, encrypted = null }) => (
    <div className={`border-2 rounded-xl p-4 ${entity.borderClass} ${entity.bgClass} transition-all`}>
      <div className="flex items-center gap-3 mb-3">
        <div className={`w-10 h-10 ${entity.logoClass} rounded-lg flex items-center justify-center text-white font-bold text-sm`}>
          {entity.logo}
        </div>
        <div>
          <h3 className="font-semibold text-gray-900">{entity.name}</h3>
          <p className="text-xs text-gray-500">{entity.patients?.toLocaleString() || entity.customers?.toLocaleString()} {config.dataLabel}</p>
        </div>
      </div>

      {showData && !encrypted && (
        <div className="space-y-2">
          <div className="grid grid-cols-3 gap-2 text-xs mb-3">
            {activeCase === 'banks' ? (
              <>
                <div className="bg-white rounded p-2 text-center">
                  <div className="font-semibold text-gray-900">{entity.stats.transactions}</div>
                  <div className="text-gray-500">Transacciones</div>
                </div>
                <div className="bg-white rounded p-2 text-center">
                  <div className="font-semibold text-red-600">{entity.stats.fraudRate}</div>
                  <div className="text-gray-500">Tasa Fraude</div>
                </div>
                <div className="bg-white rounded p-2 text-center">
                  <div className="font-semibold text-gray-900">{entity.stats.avgAmount}</div>
                  <div className="text-gray-500">Promedio</div>
                </div>
              </>
            ) : (
              <>
                <div className="bg-white rounded p-2 text-center">
                  <div className="font-semibold text-gray-900">{entity.stats.records}</div>
                  <div className="text-gray-500">Registros</div>
                </div>
                <div className="bg-white rounded p-2 text-center">
                  <div className="font-semibold text-rose-600">{entity.stats.conditions}</div>
                  <div className="text-gray-500">Condiciones</div>
                </div>
                <div className="bg-white rounded p-2 text-center">
                  <div className="font-semibold text-gray-900">{entity.stats.avgAge} años</div>
                  <div className="text-gray-500">Edad prom.</div>
                </div>
              </>
            )}
          </div>
          <div className="bg-white rounded-lg p-2 text-xs">
            <div className="font-medium text-gray-700 mb-1">Muestra de registros:</div>
            {entity.data.map((row, i) => (
              <div key={i} className={`flex justify-between py-1 border-b last:border-0 ${
                (row.flagged || row.risk === 'Alto') ? 'text-red-600' : 'text-gray-600'
              }`}>
                <span className="font-mono">{row.id}</span>
                {activeCase === 'banks' ? (
                  <>
                    <span>{row.amount}</span>
                    <span>{row.type}</span>
                  </>
                ) : (
                  <>
                    <span>{row.age} años</span>
                    <span>{row.diagnosis}</span>
                  </>
                )}
                {(row.flagged || row.risk === 'Alto') && <span className="text-red-500 font-bold">!</span>}
              </div>
            ))}
          </div>
        </div>
      )}

      {encrypted && (
        <div className="bg-gray-900 rounded-lg p-3 font-mono text-xs text-yellow-400 break-all">
          <div className="flex items-center gap-2 text-green-400 mb-2">
            <LockClosedIcon className="w-4 h-4" />
            <span>CIFRADO CON CLAVE PRIVADA</span>
          </div>
          {encrypted.substring(0, 80)}...
        </div>
      )}
    </div>
  )

  const Icon = config.icon

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-900 to-slate-800 text-white py-6 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center gap-3 mb-2">
            <Icon className="w-8 h-8" />
            <h1 className="text-2xl font-bold">{config.title}</h1>
          </div>
          <p className="text-slate-300">{config.subtitle}</p>
        </div>
      </div>

      {/* Case Selector Tabs */}
      <div className="bg-white border-b">
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex gap-1">
            <button
              onClick={() => switchCase('banks')}
              className={`px-6 py-4 font-medium transition-all border-b-2 ${
                activeCase === 'banks'
                  ? 'border-indigo-600 text-indigo-600 bg-indigo-50'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <BuildingOffice2Icon className="w-5 h-5 inline mr-2" />
              Fraude Bancario
            </button>
            <button
              onClick={() => switchCase('health')}
              className={`px-6 py-4 font-medium transition-all border-b-2 ${
                activeCase === 'health'
                  ? 'border-rose-600 text-rose-600 bg-rose-50'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <HeartIcon className="w-5 h-5 inline mr-2" />
              Investigacion Medica
            </button>
          </div>
        </div>
      </div>

      {/* Progress Steps */}
      <div className="bg-white border-b shadow-sm sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-3">
          <div className="flex items-center justify-between flex-wrap gap-2">
            {config.steps.map((s, i) => (
              <div key={i} className="flex items-center">
                <button
                  onClick={() => !isPlaying && runStep(i)}
                  disabled={isPlaying}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-all text-sm ${
                    step === i
                      ? activeCase === 'banks' ? 'bg-indigo-600 text-white' : 'bg-rose-600 text-white'
                      : step > i
                        ? 'bg-green-100 text-green-700'
                        : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                  }`}
                >
                  {step > i ? (
                    <CheckCircleIcon className="w-4 h-4" />
                  ) : (
                    <span className="w-4 h-4 rounded-full border-2 flex items-center justify-center text-xs font-bold">
                      {i + 1}
                    </span>
                  )}
                  <span className="font-medium hidden lg:inline">{s.title}</span>
                </button>
                {i < config.steps.length - 1 && (
                  <ArrowRightIcon className="w-3 h-3 text-gray-300 mx-1 hidden sm:block" />
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-6">
        {/* Current Step + Play Button */}
        <div className="bg-white rounded-xl shadow-sm border p-5 mb-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <h2 className="text-lg font-bold text-gray-900 mb-1">
                Paso {step + 1}: {config.steps[step].title}
              </h2>
              <p className="text-gray-600 text-sm">{config.steps[step].description}</p>
            </div>
            <button
              onClick={playDemo}
              disabled={isPlaying}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold transition-all whitespace-nowrap ${
                isPlaying
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : activeCase === 'banks'
                    ? 'bg-indigo-600 text-white hover:bg-indigo-700 shadow-lg'
                    : 'bg-rose-600 text-white hover:bg-rose-700 shadow-lg'
              }`}
            >
              <PlayIcon className="w-5 h-5" />
              {isPlaying ? 'Ejecutando...' : 'Iniciar Demo'}
            </button>
          </div>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mb-6">

          {/* Step 0: Problem */}
          {step === 0 && (
            <div className="lg:col-span-3 bg-white rounded-xl shadow-sm border p-6">
              <div className="text-center max-w-3xl mx-auto">
                <div className="flex justify-center gap-3 mb-5">
                  {Object.values(entities).map((entity, i) => (
                    <div key={i} className={`w-14 h-14 ${entity.logoClass} rounded-xl flex items-center justify-center text-white text-lg font-bold`}>
                      {entity.logo}
                    </div>
                  ))}
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-3">{config.problem.title}</h3>
                <p className="text-gray-600 mb-5">{config.problem.description}</p>
                <div className="grid grid-cols-3 gap-3 text-sm mb-6">
                  {config.problem.barriers.map((barrier, i) => (
                    <div key={i} className="bg-red-50 border border-red-200 rounded-lg p-3">
                      <div className="text-red-600 font-semibold">{barrier}</div>
                    </div>
                  ))}
                </div>
                {/* Solution */}
                <div className={`${activeCase === 'banks' ? 'bg-indigo-50 border-indigo-200' : 'bg-rose-50 border-rose-200'} border-2 rounded-xl p-4`}>
                  <div className={`font-bold ${activeCase === 'banks' ? 'text-indigo-700' : 'text-rose-700'} mb-2`}>
                    La Solucion: Fully Homomorphic Encryption (FHE)
                  </div>
                  <p className="text-gray-700">{config.problem.solution}</p>
                </div>
              </div>
            </div>
          )}

          {/* Step 1 & 2: Data Cards */}
          {(step === 1 || step === 2) && (
            <>
              {Object.entries(entities).map(([key, entity]) => (
                <EntityCard
                  key={key}
                  entityKey={key}
                  entity={entity}
                  showData={true}
                  encrypted={encryptedData[key]}
                />
              ))}
            </>
          )}

          {/* Step 3: Server View */}
          {step === 3 && (
            <div className="lg:col-span-3">
              <div className="bg-slate-900 rounded-xl p-5 text-white">
                <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 mb-4">
                  <ServerIcon className="w-7 h-7 text-slate-400" />
                  <div>
                    <h3 className="font-semibold">Servidor Central</h3>
                    <p className="text-slate-400 text-sm">NO puede descifrar los datos</p>
                  </div>
                  <div className="sm:ml-auto flex items-center gap-2 bg-red-500/20 text-red-400 px-3 py-1 rounded-full text-sm">
                    <EyeSlashIcon className="w-4 h-4" />
                    Sin acceso
                  </div>
                </div>

                <div className="space-y-3">
                  {serverView.map((item, i) => (
                    <div key={i} className="bg-slate-800 rounded-lg p-3">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-slate-300 font-medium text-sm">{item.from}</span>
                        <span className="text-slate-500 text-xs">{item.size}</span>
                      </div>
                      <div className="font-mono text-xs text-yellow-400 break-all bg-slate-950 p-2 rounded">
                        {item.cipher}...
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Step 4: Training */}
          {step === 4 && (
            <div className="lg:col-span-3">
              <div className="bg-white rounded-xl shadow-sm border p-5">
                <div className="flex items-center gap-3 mb-5">
                  <CpuChipIcon className={`w-7 h-7 ${activeCase === 'banks' ? 'text-indigo-600' : 'text-rose-600'}`} />
                  <div>
                    <h3 className="font-semibold text-gray-900">Machine Learning sobre Datos Cifrados</h3>
                    <p className="text-gray-500 text-sm">El modelo aprende patrones SIN ver los datos originales</p>
                  </div>
                </div>

                {/* Key callout */}
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-5 text-sm">
                  <span className="font-bold text-yellow-800">IMPORTANTE:</span>
                  <span className="text-yellow-700"> El servidor ejecuta ML sobre ciphertext. Obtiene un modelo entrenado pero NUNCA ve los datos reales.</span>
                </div>

                <div className="mb-5">
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-gray-600">Entrenando modelo ML...</span>
                    <span className={`font-semibold ${activeCase === 'banks' ? 'text-indigo-600' : 'text-rose-600'}`}>{modelProgress}%</span>
                  </div>
                  <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all duration-300 ${activeCase === 'banks' ? 'bg-indigo-600' : 'bg-rose-600'}`}
                      style={{ width: `${modelProgress}%` }}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-4 gap-4 text-center">
                  <div className="bg-gray-50 rounded-lg p-3">
                    <div className="text-xl font-bold text-gray-900">
                      {activeCase === 'banks' ? '4.2M' : '1.9M'}
                    </div>
                    <div className="text-xs text-gray-500">Registros cifrados</div>
                  </div>
                  <div className="bg-green-50 rounded-lg p-3">
                    <div className="text-xl font-bold text-green-600">0</div>
                    <div className="text-xs text-gray-500">Datos visibles</div>
                  </div>
                  <div className={`${activeCase === 'banks' ? 'bg-indigo-50' : 'bg-rose-50'} rounded-lg p-3`}>
                    <div className={`text-xl font-bold ${activeCase === 'banks' ? 'text-indigo-600' : 'text-rose-600'}`}>ML</div>
                    <div className="text-xs text-gray-500">Modelo entrenado</div>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3">
                    <div className="text-xl font-bold text-gray-900">3</div>
                    <div className="text-xs text-gray-500">Fuentes de datos</div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Step 5: Results */}
          {step === 5 && results && (
            <>
              {/* Results header */}
              <div className="lg:col-span-3 mb-2">
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <h3 className="font-bold text-green-800 mb-1">Resultados del Machine Learning</h3>
                  <p className="text-sm text-green-700">
                    Cada institucion ve SUS predicciones. <strong>NADIE</strong> ve los datos originales de otros.
                  </p>
                </div>
              </div>
              {Object.entries(entities).map(([key, entity]) => (
                <div key={key} className={`bg-white rounded-xl shadow-sm border-2 ${entity.borderClass} p-4`}>
                  <div className="flex items-center gap-3 mb-4">
                    <div className={`w-9 h-9 ${entity.logoClass} rounded-lg flex items-center justify-center text-white font-bold text-sm`}>
                      {entity.logo}
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900 text-sm">{entity.name}</h3>
                      <p className="text-xs text-green-600 flex items-center gap-1">
                        <ShieldCheckIcon className="w-3 h-3" />
                        Predicciones descifradas
                      </p>
                    </div>
                  </div>

                  <div className="text-xs text-gray-500 mb-2 font-medium uppercase">Predicciones del modelo ML:</div>

                  <div className="grid grid-cols-2 gap-2 mb-3">
                    <div className="bg-green-50 rounded-lg p-2 text-center">
                      <div className="text-xl font-bold text-green-600">{results[key].metric1}</div>
                      <div className="text-xs text-gray-600">{results[key].metric1Label}</div>
                    </div>
                    <div className="bg-blue-50 rounded-lg p-2 text-center">
                      <div className="text-xl font-bold text-blue-600">{results[key].metric2}</div>
                      <div className="text-xs text-gray-600">{results[key].metric2Label}</div>
                    </div>
                  </div>

                  <div className={`${activeCase === 'banks' ? 'bg-indigo-50' : 'bg-rose-50'} rounded-lg p-2 text-center`}>
                    <div className={`text-lg font-bold ${activeCase === 'banks' ? 'text-indigo-600' : 'text-rose-600'}`}>{results[key].accuracy}</div>
                    <div className="text-xs text-gray-600">Precision del modelo</div>
                  </div>
                </div>
              ))}
            </>
          )}
        </div>

        {/* Activity Log */}
        {logs.length > 0 && (
          <div className="bg-slate-900 rounded-xl p-4 text-sm font-mono mb-6">
            <div className="text-slate-400 mb-2 text-xs">Log:</div>
            <div className="space-y-1 max-h-32 overflow-y-auto">
              {logs.map((log, i) => (
                <div key={i} className={`flex items-center gap-2 text-xs ${
                  log.type === 'success' ? 'text-green-400' :
                  log.type === 'warning' ? 'text-yellow-400' :
                  log.type === 'encrypt' ? 'text-blue-400' :
                  log.type === 'server' ? 'text-purple-400' :
                  log.type === 'train' ? 'text-orange-400' :
                  log.type === 'result' ? 'text-cyan-400' :
                  'text-slate-300'
                }`}>
                  <span className="text-slate-600">[{log.time}]</span>
                  <span>{log.message}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Video Demos Section */}
        <div className="bg-white rounded-xl shadow-sm border p-6 mb-6">
          <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
            <PlayIcon className="w-5 h-5 text-indigo-600" />
            Videos Demo
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Demo Consorcio */}
            <div>
              <h4 className="font-medium text-gray-700 mb-2">Demo: Consorcio FHE-ML</h4>
              <p className="text-sm text-gray-500 mb-3">Flujo completo de entrenamiento federado con datos cifrados</p>
              <video
                controls
                className="w-full rounded-lg border border-gray-200 bg-black"
                poster="/videos/demo_consorcio_poster.jpg"
              >
                <source src="/videos/demo_consorcio.mp4" type="video/mp4" />
                Tu navegador no soporta videos HTML5.
              </video>
            </div>
            {/* Demo Web */}
            <div>
              <h4 className="font-medium text-gray-700 mb-2">Demo: Interfaz Web</h4>
              <p className="text-sm text-gray-500 mb-3">Navegacion por el dashboard y funcionalidades principales</p>
              <video
                controls
                className="w-full rounded-lg border border-gray-200 bg-black"
              >
                <source src="/videos/demo_web.mp4" type="video/mp4" />
                Tu navegador no soporta videos HTML5.
              </video>
            </div>
          </div>
        </div>

        {/* Summary */}
        {step === 5 && results && (
          <>
            {/* Key Insight Box */}
            <div className="bg-slate-900 rounded-xl p-5 mb-6 border-2 border-yellow-500">
              <div className="flex items-start gap-3">
                <div className="bg-yellow-500 rounded-full p-2 flex-shrink-0">
                  <EyeSlashIcon className="w-5 h-5 text-slate-900" />
                </div>
                <div>
                  <h4 className="font-bold text-yellow-400 mb-2">Lo que acaba de pasar:</h4>
                  <p className="text-white text-sm leading-relaxed">{config.keyInsight}</p>
                </div>
              </div>
            </div>

            {/* Results Summary */}
            <div className={`rounded-xl p-6 text-white ${activeCase === 'banks' ? 'bg-gradient-to-r from-indigo-600 to-purple-600' : 'bg-gradient-to-r from-rose-600 to-pink-600'}`}>
              <h3 className="text-lg font-bold mb-4">Resumen:</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                <div className="flex items-start gap-3">
                  <CheckCircleIcon className="w-5 h-5 text-green-300 flex-shrink-0 mt-0.5" />
                  <div>
                    <div className="font-semibold">{config.summary.stat1}</div>
                    <div className="text-white/70 text-sm">{config.summary.stat1sub}</div>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <CheckCircleIcon className="w-5 h-5 text-green-300 flex-shrink-0 mt-0.5" />
                  <div>
                    <div className="font-semibold">{config.summary.stat2}</div>
                    <div className="text-white/70 text-sm">{config.summary.stat2sub}</div>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <CheckCircleIcon className="w-5 h-5 text-green-300 flex-shrink-0 mt-0.5" />
                  <div>
                    <div className="font-semibold">{config.summary.stat3}</div>
                    <div className="text-white/70 text-sm">{config.summary.stat3sub}</div>
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
