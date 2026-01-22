import React, { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { motion, AnimatePresence } from 'framer-motion'
import { Lock, Unlock, Cpu, Eye, EyeOff, Play, RotateCcw, ArrowRight, Check } from 'lucide-react'

const EncryptionDemo = ({ theme = 'blue' }) => {
  const { t } = useTranslation()
  const [currentStep, setCurrentStep] = useState(0)
  const [inputData, setInputData] = useState('')
  const [encryptedData, setEncryptedData] = useState('')
  const [result, setResult] = useState('')
  const [isAnimating, setIsAnimating] = useState(false)

  const themeColors = {
    blue: { gradient: 'from-blue-500 to-indigo-600', accent: 'blue-400', bg: 'blue-500/20', text: 'blue-400' },
    emerald: { gradient: 'from-emerald-500 to-teal-600', accent: 'emerald-400', bg: 'emerald-500/20', text: 'emerald-400' },
    slate: { gradient: 'from-slate-600 to-gray-700', accent: 'slate-400', bg: 'slate-500/20', text: 'slate-400' },
    purple: { gradient: 'from-purple-500 to-indigo-600', accent: 'purple-400', bg: 'purple-500/20', text: 'purple-400' }
  }

  const colors = themeColors[theme]

  const exampleData = {
    fintech: {
      input: 'Juan Pérez, DNI: 12345678, Saldo: $50,000',
      encrypted: 'a7f3x9k2...m8p1q5r4...z2v6n0b3',
      operation: 'Detectar fraude',
      result: 'Riesgo: BAJO (0.12)'
    },
    healthcare: {
      input: 'Paciente: María G., Glucosa: 126mg/dL',
      encrypted: 'h2j8w4e1...y6i0o3u7...d5g9s2l8',
      operation: 'Predecir diabetes',
      result: 'Probabilidad: 23%'
    },
    gobierno: {
      input: 'Contribuyente ID: 98765, Ingresos: $85,000',
      encrypted: 'b4n6m2k8...f1p5t9v3...c7x0z4a1',
      operation: 'Detectar evasión',
      result: 'Alerta: NO'
    }
  }

  const selectedExample = exampleData.fintech

  const steps = [
    {
      id: 0,
      title: t('demo.steps.input', 'Ingresa datos'),
      description: t('demo.steps.inputDesc', 'Datos sensibles en texto plano'),
      icon: Eye
    },
    {
      id: 1,
      title: t('demo.steps.encrypt', 'Cifrar'),
      description: t('demo.steps.encryptDesc', 'FHE convierte a ciphertext'),
      icon: Lock
    },
    {
      id: 2,
      title: t('demo.steps.compute', 'Calcular'),
      description: t('demo.steps.computeDesc', 'ML sobre datos cifrados'),
      icon: Cpu
    },
    {
      id: 3,
      title: t('demo.steps.result', 'Resultado'),
      description: t('demo.steps.resultDesc', 'Solo tú ves el resultado'),
      icon: Unlock
    }
  ]

  useEffect(() => {
    if (!inputData) {
      setInputData(selectedExample.input)
    }
  }, [])

  const generateEncrypted = () => {
    const chars = 'abcdef0123456789'
    let result = ''
    for (let i = 0; i < 64; i++) {
      if (i > 0 && i % 16 === 0) result += '...'
      result += chars[Math.floor(Math.random() * chars.length)]
    }
    return result
  }

  const runDemo = async () => {
    if (isAnimating) return
    setIsAnimating(true)
    setCurrentStep(0)

    // Step 1: Show input
    await new Promise(r => setTimeout(r, 800))
    setCurrentStep(1)

    // Step 2: Encrypt
    let encrypted = ''
    for (let i = 0; i < 20; i++) {
      encrypted = generateEncrypted()
      setEncryptedData(encrypted)
      await new Promise(r => setTimeout(r, 50))
    }
    await new Promise(r => setTimeout(r, 500))
    setCurrentStep(2)

    // Step 3: Compute
    await new Promise(r => setTimeout(r, 1500))
    setCurrentStep(3)

    // Step 4: Result
    setResult(selectedExample.result)
    setIsAnimating(false)
  }

  const resetDemo = () => {
    setCurrentStep(0)
    setEncryptedData('')
    setResult('')
    setIsAnimating(false)
  }

  return (
    <section className="py-20 px-4">
      <div className="max-w-5xl mx-auto">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-12"
        >
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            {t('demo.title', 'Mira FHE en acción')}
          </h2>
          <p className="text-white/60 text-lg max-w-2xl mx-auto">
            {t('demo.subtitle', 'Observa cómo tus datos permanecen cifrados durante todo el procesamiento')}
          </p>
        </motion.div>

        {/* Step Indicators */}
        <div className="flex justify-center mb-8">
          <div className="flex items-center gap-2 md:gap-4">
            {steps.map((step, idx) => (
              <React.Fragment key={step.id}>
                <motion.div
                  animate={{
                    scale: currentStep === idx ? 1.1 : 1,
                    opacity: currentStep >= idx ? 1 : 0.4
                  }}
                  className={`flex flex-col items-center ${currentStep >= idx ? 'text-white' : 'text-white/40'}`}
                >
                  <div
                    className={`w-10 h-10 md:w-12 md:h-12 rounded-full flex items-center justify-center transition-all ${
                      currentStep >= idx
                        ? `bg-gradient-to-r ${colors.gradient}`
                        : 'bg-white/10'
                    }`}
                  >
                    {currentStep > idx ? (
                      <Check className="w-5 h-5" />
                    ) : (
                      <step.icon className="w-5 h-5" />
                    )}
                  </div>
                  <span className="text-xs mt-2 hidden md:block">{step.title}</span>
                </motion.div>
                {idx < steps.length - 1 && (
                  <div className={`w-8 md:w-16 h-0.5 ${currentStep > idx ? `bg-${colors.text}` : 'bg-white/20'}`} />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>

        {/* Demo Area */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="bg-white/5 backdrop-blur-sm rounded-3xl p-6 md:p-8 border border-white/10"
        >
          {/* Input Area */}
          <div className="mb-6">
            <label className="block text-white/60 text-sm mb-2">
              {t('demo.inputLabel', 'Datos de entrada (ejemplo)')}
            </label>
            <div className="relative">
              <input
                type="text"
                value={inputData}
                onChange={(e) => setInputData(e.target.value)}
                disabled={isAnimating}
                className="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white placeholder-white/40 focus:outline-none focus:border-white/40 disabled:opacity-50"
                placeholder={t('demo.inputPlaceholder', 'Ingresa datos sensibles...')}
              />
              <AnimatePresence>
                {currentStep >= 1 && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent"
                    style={{ animation: 'shimmer 2s infinite' }}
                  />
                )}
              </AnimatePresence>
            </div>
          </div>

          {/* Processing Visualization */}
          <div className="grid md:grid-cols-3 gap-4 mb-6">
            {/* Encrypted Data */}
            <div className={`rounded-xl p-4 transition-all ${currentStep >= 1 ? `bg-${colors.bg} border border-${colors.accent}/30` : 'bg-white/5 border border-white/10'}`}>
              <div className="flex items-center gap-2 mb-2">
                <Lock className={`w-4 h-4 ${currentStep >= 1 ? `text-${colors.text}` : 'text-white/40'}`} />
                <span className="text-white/60 text-sm">{t('demo.encrypted', 'Cifrado')}</span>
              </div>
              <div className="font-mono text-xs text-white/80 break-all min-h-[60px]">
                {currentStep >= 1 ? (
                  <motion.span
                    key={encryptedData}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                  >
                    {encryptedData || selectedExample.encrypted}
                  </motion.span>
                ) : (
                  <span className="text-white/30">---</span>
                )}
              </div>
            </div>

            {/* Operation */}
            <div className={`rounded-xl p-4 transition-all ${currentStep >= 2 ? `bg-${colors.bg} border border-${colors.accent}/30` : 'bg-white/5 border border-white/10'}`}>
              <div className="flex items-center gap-2 mb-2">
                <Cpu className={`w-4 h-4 ${currentStep >= 2 ? `text-${colors.text}` : 'text-white/40'}`} />
                <span className="text-white/60 text-sm">{t('demo.operation', 'Operación')}</span>
              </div>
              <div className="text-white/80 min-h-[60px] flex items-center">
                {currentStep >= 2 ? (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="flex items-center gap-2"
                  >
                    <span>{selectedExample.operation}</span>
                    {currentStep === 2 && (
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                        className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full"
                      />
                    )}
                  </motion.div>
                ) : (
                  <span className="text-white/30">---</span>
                )}
              </div>
            </div>

            {/* Result */}
            <div className={`rounded-xl p-4 transition-all ${currentStep >= 3 ? `bg-gradient-to-br ${colors.gradient}` : 'bg-white/5 border border-white/10'}`}>
              <div className="flex items-center gap-2 mb-2">
                <Unlock className={`w-4 h-4 ${currentStep >= 3 ? 'text-white' : 'text-white/40'}`} />
                <span className={`text-sm ${currentStep >= 3 ? 'text-white/80' : 'text-white/60'}`}>
                  {t('demo.result', 'Resultado')}
                </span>
              </div>
              <div className="min-h-[60px] flex items-center">
                {currentStep >= 3 ? (
                  <motion.span
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="text-white font-bold text-lg"
                  >
                    {result}
                  </motion.span>
                ) : (
                  <span className="text-white/30">---</span>
                )}
              </div>
            </div>
          </div>

          {/* Key Points */}
          <div className="bg-white/5 rounded-xl p-4 mb-6">
            <div className="flex items-start gap-3">
              <EyeOff className={`w-5 h-5 ${colors.text} flex-shrink-0 mt-0.5`} />
              <div>
                <p className="text-white/80 text-sm">
                  <span className="font-semibold">{t('demo.keyPoint', 'Punto clave:')}</span>{' '}
                  {t('demo.keyPointDesc', 'El servidor NUNCA vio los datos originales. Todo el procesamiento ocurrió sobre datos cifrados. Solo tú, con tu clave privada, puedes ver el resultado.')}
                </p>
              </div>
            </div>
          </div>

          {/* Controls */}
          <div className="flex justify-center gap-4">
            <motion.button
              onClick={runDemo}
              disabled={isAnimating}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className={`flex items-center gap-2 bg-gradient-to-r ${colors.gradient} text-white px-6 py-3 rounded-xl font-semibold disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              <Play className="w-5 h-5" />
              {isAnimating ? t('demo.running', 'Ejecutando...') : t('demo.run', 'Ejecutar demo')}
            </motion.button>

            {currentStep > 0 && (
              <motion.button
                onClick={resetDemo}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="flex items-center gap-2 bg-white/10 text-white px-6 py-3 rounded-xl font-semibold hover:bg-white/20"
              >
                <RotateCcw className="w-5 h-5" />
                {t('demo.reset', 'Reiniciar')}
              </motion.button>
            )}
          </div>
        </motion.div>

        {/* Technical Note */}
        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="text-center text-white/40 text-sm mt-6"
        >
          {t('demo.techNote', 'Esta es una visualización simplificada. En producción, usamos el esquema CKKS con 128-256 bits de seguridad.')}
        </motion.p>
      </div>

      <style jsx>{`
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
      `}</style>
    </section>
  )
}

export default EncryptionDemo
