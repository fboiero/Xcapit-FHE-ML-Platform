import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { motion, AnimatePresence } from 'framer-motion'
import { Check, X, AlertTriangle, HelpCircle, Shield, Server, Users, FileCheck } from 'lucide-react'

const TechnologyComparison = ({ theme = 'blue' }) => {
  const { t } = useTranslation()
  const [activeTooltip, setActiveTooltip] = useState(null)

  const themeColors = {
    blue: { gradient: 'from-blue-500 to-indigo-600', accent: 'blue-400', bg: 'blue-500/20', border: 'blue-500/30' },
    emerald: { gradient: 'from-emerald-500 to-teal-600', accent: 'emerald-400', bg: 'emerald-500/20', border: 'emerald-500/30' },
    slate: { gradient: 'from-slate-600 to-gray-700', accent: 'slate-400', bg: 'slate-500/20', border: 'slate-500/30' },
    purple: { gradient: 'from-purple-500 to-indigo-600', accent: 'purple-400', bg: 'purple-500/20', border: 'purple-500/30' }
  }

  const colors = themeColors[theme]

  const technologies = [
    {
      id: 'fhe',
      name: 'FHE (Xcapit)',
      highlight: true,
      description: t('comparison.fhe.description', 'Los datos NUNCA se descifran. 2+2=4 se calcula SIN ver el 2.'),
      icon: Shield
    },
    {
      id: 'mpc',
      name: 'MPC',
      description: t('comparison.mpc.description', 'Varios servidores calculan juntos. Si uno es comprometido, los datos están en riesgo.'),
      icon: Server
    },
    {
      id: 'federated',
      name: 'Federated Learning',
      description: t('comparison.federated.description', 'El modelo viaja a los datos. Vulnerable a ataques de inferencia.'),
      icon: Users
    },
    {
      id: 'dcr',
      name: 'Data Clean Rooms',
      description: t('comparison.dcr.description', 'Un tercero ve tus datos para procesarlos. Requiere confianza total.'),
      icon: FileCheck
    }
  ]

  const features = [
    {
      id: 'always_encrypted',
      name: t('comparison.features.alwaysEncrypted', 'Datos SIEMPRE cifrados'),
      tooltip: t('comparison.features.alwaysEncryptedTooltip', 'Los datos permanecen cifrados durante todo el procesamiento, nunca se descifran en el servidor'),
      values: { fhe: 'yes', mpc: 'partial', federated: 'no', dcr: 'no' }
    },
    {
      id: 'no_trust',
      name: t('comparison.features.noTrust', 'Sin tercero de confianza'),
      tooltip: t('comparison.features.noTrustTooltip', 'No requiere confiar en ningún servidor o tercero con tus datos'),
      values: { fhe: 'yes', mpc: 'partial', federated: 'yes', dcr: 'no' }
    },
    {
      id: 'full_ml',
      name: t('comparison.features.fullML', 'ML completo sobre cifrado'),
      tooltip: t('comparison.features.fullMLTooltip', 'Soporta modelos de ML complejos (regresión, clasificación, clustering) sobre datos cifrados'),
      values: { fhe: 'yes', mpc: 'partial', federated: 'no', dcr: 'no' }
    },
    {
      id: 'blockchain_audit',
      name: t('comparison.features.blockchainAudit', 'Auditoría blockchain'),
      tooltip: t('comparison.features.blockchainAuditTooltip', 'Registro inmutable de todas las operaciones para cumplimiento regulatorio'),
      values: { fhe: 'yes', mpc: 'no', federated: 'no', dcr: 'no' }
    },
    {
      id: 'data_sovereignty',
      name: t('comparison.features.dataSovereignty', 'Soberanía de datos'),
      tooltip: t('comparison.features.dataSovereigntyTooltip', 'Los datos nunca salen de tu infraestructura ni son accesibles por terceros'),
      values: { fhe: 'yes', mpc: 'partial', federated: 'partial', dcr: 'no' }
    },
    {
      id: 'compliance',
      name: t('comparison.features.compliance', 'Compliance automático'),
      tooltip: t('comparison.features.complianceTooltip', 'Cumple automáticamente con GDPR, HIPAA, PCI-DSS y otras regulaciones'),
      values: { fhe: 'yes', mpc: 'partial', federated: 'partial', dcr: 'partial' }
    }
  ]

  const renderValue = (value) => {
    switch (value) {
      case 'yes':
        return <Check className="w-5 h-5 text-green-400" />
      case 'no':
        return <X className="w-5 h-5 text-red-400" />
      case 'partial':
        return <AlertTriangle className="w-5 h-5 text-yellow-400" />
      default:
        return null
    }
  }

  return (
    <section className="py-20 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-12"
        >
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            {t('comparison.title', '¿Por qué FHE es superior?')}
          </h2>
          <p className="text-white/60 text-lg max-w-2xl mx-auto">
            {t('comparison.subtitle', 'Compara las tecnologías de privacidad y descubre por qué el cifrado homomórfico es el futuro')}
          </p>
        </motion.div>

        {/* Comparison Table - Desktop */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="hidden md:block overflow-hidden rounded-2xl border border-white/10"
        >
          {/* Header Row */}
          <div className="grid grid-cols-5 bg-white/5">
            <div className="p-6 border-r border-white/10">
              <span className="text-white/40 text-sm font-medium uppercase tracking-wider">
                {t('comparison.feature', 'Característica')}
              </span>
            </div>
            {technologies.map((tech) => (
              <div
                key={tech.id}
                className={`p-6 text-center border-r border-white/10 last:border-r-0 ${
                  tech.highlight ? `bg-gradient-to-b ${colors.gradient} bg-opacity-20` : ''
                }`}
              >
                <div className="flex flex-col items-center gap-2">
                  <tech.icon className={`w-6 h-6 ${tech.highlight ? 'text-white' : 'text-white/60'}`} />
                  <span className={`font-bold ${tech.highlight ? 'text-white' : 'text-white/80'}`}>
                    {tech.name}
                  </span>
                  {tech.highlight && (
                    <span className="text-xs bg-white/20 px-2 py-1 rounded-full text-white">
                      {t('comparison.recommended', 'Recomendado')}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Feature Rows */}
          {features.map((feature, idx) => (
            <div
              key={feature.id}
              className={`grid grid-cols-5 ${idx % 2 === 0 ? 'bg-white/[0.02]' : ''}`}
            >
              <div className="p-4 border-r border-white/10 flex items-center gap-2">
                <span className="text-white/80">{feature.name}</span>
                <button
                  onClick={() => setActiveTooltip(activeTooltip === feature.id ? null : feature.id)}
                  className="text-white/40 hover:text-white/60 transition-colors"
                >
                  <HelpCircle className="w-4 h-4" />
                </button>
                <AnimatePresence>
                  {activeTooltip === feature.id && (
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      className="absolute z-10 mt-16 ml-0 w-64 p-3 bg-gray-900 rounded-lg shadow-xl border border-white/20 text-sm text-white/80"
                    >
                      {feature.tooltip}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
              {technologies.map((tech) => (
                <div
                  key={`${feature.id}-${tech.id}`}
                  className={`p-4 flex justify-center items-center border-r border-white/10 last:border-r-0 ${
                    tech.highlight ? `bg-${colors.bg}` : ''
                  }`}
                >
                  {renderValue(feature.values[tech.id])}
                </div>
              ))}
            </div>
          ))}
        </motion.div>

        {/* Comparison Cards - Mobile */}
        <div className="md:hidden space-y-4">
          {technologies.map((tech, techIdx) => (
            <motion.div
              key={tech.id}
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ delay: techIdx * 0.1 }}
              className={`rounded-xl p-6 ${
                tech.highlight
                  ? `bg-gradient-to-br ${colors.gradient}`
                  : 'bg-white/5 border border-white/10'
              }`}
            >
              <div className="flex items-center gap-3 mb-4">
                <tech.icon className="w-6 h-6 text-white" />
                <h3 className="text-xl font-bold text-white">{tech.name}</h3>
                {tech.highlight && (
                  <span className="text-xs bg-white/20 px-2 py-1 rounded-full text-white ml-auto">
                    {t('comparison.recommended', 'Recomendado')}
                  </span>
                )}
              </div>
              <p className="text-white/70 text-sm mb-4">{tech.description}</p>
              <div className="space-y-2">
                {features.map((feature) => (
                  <div key={feature.id} className="flex items-center justify-between">
                    <span className="text-white/60 text-sm">{feature.name}</span>
                    {renderValue(feature.values[tech.id])}
                  </div>
                ))}
              </div>
            </motion.div>
          ))}
        </div>

        {/* Legend */}
        <div className="mt-8 flex flex-wrap justify-center gap-6 text-sm">
          <div className="flex items-center gap-2">
            <Check className="w-4 h-4 text-green-400" />
            <span className="text-white/60">{t('comparison.legend.full', 'Soporte completo')}</span>
          </div>
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-yellow-400" />
            <span className="text-white/60">{t('comparison.legend.partial', 'Soporte parcial')}</span>
          </div>
          <div className="flex items-center gap-2">
            <X className="w-4 h-4 text-red-400" />
            <span className="text-white/60">{t('comparison.legend.none', 'No soportado')}</span>
          </div>
        </div>

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="mt-12 text-center"
        >
          <p className="text-white/60 mb-4">
            {t('comparison.cta.text', '¿Quieres entender mejor las diferencias?')}
          </p>
          <a
            href="#contact"
            className={`inline-flex items-center gap-2 bg-gradient-to-r ${colors.gradient} text-white px-6 py-3 rounded-xl font-semibold hover:opacity-90 transition-opacity`}
          >
            {t('comparison.cta.button', 'Hablar con un experto')}
          </a>
        </motion.div>
      </div>
    </section>
  )
}

export default TechnologyComparison
