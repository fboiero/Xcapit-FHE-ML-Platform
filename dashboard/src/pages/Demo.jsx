import { useState, useEffect } from 'react'

// Simulated FHE encryption (in production, use actual TenSEAL via WASM or API)
const simulateEncryption = (value) => {
  // Generate realistic-looking ciphertext bytes
  const bytes = []
  const seed = typeof value === 'number' ? value : value.toString().charCodeAt(0)
  for (let i = 0; i < 64; i++) {
    bytes.push(((seed * 17 + i * 31) % 256).toString(16).padStart(2, '0'))
  }
  return '0x' + bytes.join('')
}

const simulateDecryption = (ciphertext, originalValue) => {
  // In demo, we "decrypt" back to the original
  return originalValue
}

// Simulate homomorphic operation
const simulateHomomorphicOp = (encryptedValues, operation) => {
  const bytes = []
  for (let i = 0; i < 64; i++) {
    bytes.push(Math.floor(Math.random() * 256).toString(16).padStart(2, '0'))
  }
  return '0x' + bytes.join('')
}

const steps = [
  { id: 1, title: 'Datos Originales', description: 'Tus datos en texto plano (solo visibles en tu navegador)' },
  { id: 2, title: 'Cifrado Local', description: 'Encriptacion FHE con tu clave privada' },
  { id: 3, title: 'Transmision Segura', description: 'Solo datos cifrados viajan al servidor' },
  { id: 4, title: 'Procesamiento Cifrado', description: 'El servidor calcula SIN descifrar' },
  { id: 5, title: 'Resultado Cifrado', description: 'El resultado tambien esta cifrado' },
  { id: 6, title: 'Descifrado Local', description: 'Solo tu puedes ver el resultado final' },
]

export default function Demo() {
  const [currentStep, setCurrentStep] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [inputData, setInputData] = useState([
    { name: 'salario', value: 50000, label: 'Salario Anual' },
    { name: 'edad', value: 35, label: 'Edad' },
    { name: 'antiguedad', value: 5, label: 'Anos de Antiguedad' },
    { name: 'deuda', value: 15000, label: 'Deuda Actual' },
  ])
  const [encryptedData, setEncryptedData] = useState({})
  const [serverView, setServerView] = useState([])
  const [encryptedResult, setEncryptedResult] = useState('')
  const [finalResult, setFinalResult] = useState(null)
  const [logs, setLogs] = useState([])

  const addLog = (message, type = 'info') => {
    const timestamp = new Date().toLocaleTimeString()
    setLogs(prev => [...prev, { timestamp, message, type }])
  }

  const resetDemo = () => {
    setCurrentStep(0)
    setEncryptedData({})
    setServerView([])
    setEncryptedResult('')
    setFinalResult(null)
    setLogs([])
    setIsPlaying(false)
  }

  const runStep = async (step) => {
    switch (step) {
      case 1:
        addLog('Preparando datos originales...', 'info')
        await sleep(500)
        addLog(`Datos cargados: ${inputData.length} campos`, 'success')
        break

      case 2:
        addLog('Iniciando cifrado FHE (CKKS scheme)...', 'info')
        await sleep(300)
        const encrypted = {}
        for (const field of inputData) {
          await sleep(400)
          encrypted[field.name] = simulateEncryption(field.value)
          addLog(`Cifrado ${field.label}: ${encrypted[field.name].substring(0, 20)}...`, 'encrypt')
        }
        setEncryptedData(encrypted)
        addLog('Cifrado completo. Clave privada permanece LOCAL.', 'success')
        break

      case 3:
        addLog('Enviando datos cifrados al servidor...', 'info')
        await sleep(300)
        const serverData = inputData.map(field => ({
          field: field.name,
          ciphertext: encryptedData[field.name],
        }))
        setServerView(serverData)
        addLog('POST /api/v1/consortiums/{id}/data', 'network')
        await sleep(500)
        addLog('Servidor recibio SOLO ciphertext. No puede descifrar.', 'success')
        break

      case 4:
        addLog('Servidor procesando datos cifrados...', 'info')
        await sleep(400)
        addLog('Agregando con datos de otros participantes (cifrados)...', 'compute')
        await sleep(600)
        addLog('Ejecutando regresion logistica sobre ciphertext...', 'compute')
        await sleep(800)
        addLog('Multiplicacion homomorforca: Enc(a) * Enc(b) = Enc(a*b)', 'compute')
        await sleep(400)
        addLog('Suma homomorfica: Enc(a) + Enc(b) = Enc(a+b)', 'compute')
        await sleep(600)
        const result = simulateHomomorphicOp(Object.values(encryptedData), 'predict')
        setEncryptedResult(result)
        addLog('Calculo completado. Resultado CIFRADO generado.', 'success')
        break

      case 5:
        addLog('Servidor enviando resultado cifrado...', 'info')
        await sleep(400)
        addLog(`Resultado: ${encryptedResult.substring(0, 30)}...`, 'network')
        addLog('El servidor NO SABE el resultado. Solo tu puedes descifrarlo.', 'warning')
        break

      case 6:
        addLog('Descifrando resultado con tu clave privada...', 'info')
        await sleep(600)
        const prediction = 0.87
        setFinalResult({
          score: prediction,
          label: prediction > 0.5 ? 'APROBADO' : 'RECHAZADO',
          confidence: (prediction * 100).toFixed(1)
        })
        addLog(`Resultado descifrado: Score = ${prediction}`, 'decrypt')
        addLog('Demo completada. Tus datos NUNCA fueron vistos por el servidor.', 'success')
        break
    }
  }

  const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms))

  const playDemo = async () => {
    setIsPlaying(true)
    resetDemo()
    await sleep(500)

    for (let i = 1; i <= 6; i++) {
      setCurrentStep(i)
      await runStep(i)
      await sleep(1000)
    }

    setIsPlaying(false)
  }

  const updateInputValue = (index, newValue) => {
    const updated = [...inputData]
    updated[index].value = parseFloat(newValue) || 0
    setInputData(updated)
  }

  return (
    <div className="pt-16 pb-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-2 text-sm text-slate-500 mb-4">
          <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded-full text-xs font-medium">
            Demo Interactiva
          </span>
        </div>
        <h1 className="text-3xl font-bold text-slate-900 mb-2">
          Privacidad en Accion
        </h1>
        <p className="text-lg text-slate-600">
          Observa como tus datos permanecen cifrados en todo momento.
          El servidor NUNCA ve la informacion original.
        </p>
      </div>

      {/* Controls */}
      <div className="flex gap-4 mb-8">
        <button
          onClick={playDemo}
          disabled={isPlaying}
          className="bg-brand-600 text-white px-6 py-3 rounded-xl font-medium hover:bg-brand-700 transition disabled:opacity-50 flex items-center gap-2"
        >
          {isPlaying ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Ejecutando...
            </>
          ) : (
            <>
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z" />
              </svg>
              Iniciar Demo
            </>
          )}
        </button>
        <button
          onClick={resetDemo}
          className="px-6 py-3 border border-slate-300 rounded-xl font-medium hover:bg-slate-50 transition"
        >
          Reiniciar
        </button>
      </div>

      {/* Progress Steps */}
      <div className="flex items-center gap-2 mb-8 overflow-x-auto pb-2">
        {steps.map((step, index) => (
          <div key={step.id} className="flex items-center">
            <div
              className={`flex items-center gap-2 px-4 py-2 rounded-lg whitespace-nowrap transition ${
                currentStep === step.id
                  ? 'bg-brand-600 text-white'
                  : currentStep > step.id
                  ? 'bg-green-100 text-green-700'
                  : 'bg-slate-100 text-slate-500'
              }`}
            >
              <span className="w-6 h-6 rounded-full bg-white/20 flex items-center justify-center text-sm">
                {currentStep > step.id ? '✓' : step.id}
              </span>
              <span className="text-sm font-medium">{step.title}</span>
            </div>
            {index < steps.length - 1 && (
              <div className={`w-8 h-0.5 mx-1 ${currentStep > step.id ? 'bg-green-300' : 'bg-slate-200'}`} />
            )}
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column - Data View */}
        <div className="space-y-6">
          {/* Your Browser - Original Data */}
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
            <div className="bg-green-50 border-b border-green-200 px-4 py-3 flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-green-500" />
              <span className="font-medium text-green-800">Tu Navegador (Privado)</span>
              <span className="ml-auto text-xs text-green-600 bg-green-100 px-2 py-1 rounded-full">
                Solo tu lo ves
              </span>
            </div>
            <div className="p-4">
              <h3 className="text-sm font-medium text-slate-500 mb-3">Datos Originales</h3>
              <div className="space-y-3">
                {inputData.map((field, index) => (
                  <div key={field.name} className="flex items-center gap-3">
                    <label className="w-40 text-sm text-slate-700">{field.label}:</label>
                    <input
                      type="number"
                      value={field.value}
                      onChange={(e) => updateInputValue(index, e.target.value)}
                      disabled={isPlaying}
                      className="flex-1 px-3 py-2 border border-slate-300 rounded-lg text-slate-900 font-mono disabled:bg-slate-50"
                    />
                  </div>
                ))}
              </div>

              {/* Encrypted View */}
              {Object.keys(encryptedData).length > 0 && (
                <div className="mt-6 pt-4 border-t border-slate-100">
                  <h3 className="text-sm font-medium text-slate-500 mb-3 flex items-center gap-2">
                    <svg className="w-4 h-4 text-brand-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                    Datos Cifrados (lo que se envia)
                  </h3>
                  <div className="space-y-2">
                    {inputData.map((field) => (
                      <div key={field.name} className="bg-slate-900 rounded-lg p-3">
                        <div className="text-xs text-slate-400 mb-1">{field.label}:</div>
                        <div className="text-xs font-mono text-green-400 break-all">
                          {encryptedData[field.name]?.substring(0, 50)}...
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Final Result */}
          {finalResult && (
            <div className="bg-white rounded-2xl border-2 border-green-500 overflow-hidden">
              <div className="bg-green-500 px-4 py-3">
                <span className="font-medium text-white">Resultado Descifrado</span>
              </div>
              <div className="p-6 text-center">
                <div className={`text-5xl font-bold mb-2 ${finalResult.score > 0.5 ? 'text-green-600' : 'text-red-600'}`}>
                  {finalResult.label}
                </div>
                <div className="text-slate-600">
                  Confianza: {finalResult.confidence}%
                </div>
                <div className="mt-4 p-3 bg-green-50 rounded-lg text-sm text-green-800">
                  Este resultado fue calculado sin que el servidor viera tus datos originales.
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Column - Server View & Logs */}
        <div className="space-y-6">
          {/* Server View */}
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
            <div className="bg-red-50 border-b border-red-200 px-4 py-3 flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500" />
              <span className="font-medium text-red-800">Servidor (Vista Limitada)</span>
              <span className="ml-auto text-xs text-red-600 bg-red-100 px-2 py-1 rounded-full">
                No puede descifrar
              </span>
            </div>
            <div className="p-4">
              {serverView.length === 0 ? (
                <div className="text-center py-8 text-slate-400">
                  <svg className="w-12 h-12 mx-auto mb-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                  <p>Esperando datos cifrados...</p>
                </div>
              ) : (
                <div className="space-y-2">
                  <h3 className="text-sm font-medium text-slate-500 mb-3">
                    Lo que el servidor recibe:
                  </h3>
                  {serverView.map((item, index) => (
                    <div key={index} className="bg-slate-900 rounded-lg p-3">
                      <div className="text-xs text-slate-400 mb-1">campo_{item.field}:</div>
                      <div className="text-xs font-mono text-orange-400 break-all">
                        {item.ciphertext?.substring(0, 50)}...
                      </div>
                    </div>
                  ))}

                  {encryptedResult && (
                    <div className="mt-4 pt-4 border-t border-slate-700">
                      <h3 className="text-sm font-medium text-slate-500 mb-3">
                        Resultado calculado (cifrado):
                      </h3>
                      <div className="bg-slate-900 rounded-lg p-3">
                        <div className="text-xs text-slate-400 mb-1">prediction_encrypted:</div>
                        <div className="text-xs font-mono text-purple-400 break-all">
                          {encryptedResult.substring(0, 80)}...
                        </div>
                      </div>
                      <p className="text-xs text-red-500 mt-2 flex items-center gap-1">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                        </svg>
                        El servidor NO puede saber que el resultado es "APROBADO"
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Activity Log */}
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
            <div className="bg-slate-800 px-4 py-3 flex items-center gap-2">
              <span className="font-medium text-white">Registro de Actividad</span>
            </div>
            <div className="h-64 overflow-y-auto p-3 bg-slate-900 font-mono text-xs">
              {logs.length === 0 ? (
                <div className="text-slate-500 text-center py-8">
                  Inicia la demo para ver el registro...
                </div>
              ) : (
                logs.map((log, index) => (
                  <div key={index} className="flex gap-2 py-1">
                    <span className="text-slate-500">[{log.timestamp}]</span>
                    <span className={
                      log.type === 'success' ? 'text-green-400' :
                      log.type === 'encrypt' ? 'text-blue-400' :
                      log.type === 'decrypt' ? 'text-purple-400' :
                      log.type === 'network' ? 'text-yellow-400' :
                      log.type === 'compute' ? 'text-orange-400' :
                      log.type === 'warning' ? 'text-red-400' :
                      'text-slate-300'
                    }>
                      {log.message}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Info Box */}
      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-2xl p-6">
        <h3 className="font-semibold text-blue-900 mb-3 flex items-center gap-2">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Como funciona la Encriptacion Homomorfica (FHE)
        </h3>
        <div className="grid md:grid-cols-3 gap-4 text-sm text-blue-800">
          <div className="bg-white rounded-lg p-4">
            <div className="font-medium mb-1">Cifrado CKKS</div>
            <p>Esquema que permite operaciones aritmeticas sobre numeros cifrados con precision configurable.</p>
          </div>
          <div className="bg-white rounded-lg p-4">
            <div className="font-medium mb-1">Operaciones Homomorficas</div>
            <p>Suma y multiplicacion funcionan directamente sobre ciphertext: Enc(a) + Enc(b) = Enc(a+b)</p>
          </div>
          <div className="bg-white rounded-lg p-4">
            <div className="font-medium mb-1">Clave Privada Local</div>
            <p>Solo tu navegador tiene la clave. El servidor NUNCA puede descifrar los datos.</p>
          </div>
        </div>
      </div>
    </div>
  )
}
