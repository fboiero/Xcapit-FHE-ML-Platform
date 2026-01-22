import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import {
  FileSearch,
  Code,
  Brain,
  Rocket,
  Check,
  Clock,
  Users,
  Shield,
  Cloud,
  BookOpen,
  ChevronDown,
  ChevronUp
} from 'lucide-react'

const ImplementationTimeline = ({ industry = 'fintech', theme = 'blue' }) => {
  const { t } = useTranslation()
  const [expandedPhase, setExpandedPhase] = useState(null)

  const themeColors = {
    blue: { gradient: 'from-blue-500 to-indigo-600', accent: 'blue-400', bg: 'blue-500/20', line: 'blue-500' },
    emerald: { gradient: 'from-emerald-500 to-teal-600', accent: 'emerald-400', bg: 'emerald-500/20', line: 'emerald-500' },
    slate: { gradient: 'from-slate-600 to-gray-700', accent: 'slate-400', bg: 'slate-500/20', line: 'slate-500' },
    purple: { gradient: 'from-purple-500 to-indigo-600', accent: 'purple-400', bg: 'purple-500/20', line: 'purple-500' }
  }

  const colors = themeColors[theme]

  const phases = [
    {
      id: 1,
      title: t('timeline.phase1.title', 'Discovery & Setup'),
      duration: t('timeline.phase1.duration', '1-2 semanas'),
      icon: FileSearch,
      description: t('timeline.phase1.description', 'Análisis de requerimientos, arquitectura y plan de integración'),
      deliverables: [
        t('timeline.phase1.deliverable1', 'Documento de arquitectura técnica'),
        t('timeline.phase1.deliverable2', 'Plan de integración detallado'),
        t('timeline.phase1.deliverable3', 'Definición de KPIs y métricas'),
        t('timeline.phase1.deliverable4', 'Ambiente de desarrollo configurado')
      ]
    },
    {
      id: 2,
      title: t('timeline.phase2.title', 'Integración Piloto'),
      duration: t('timeline.phase2.duration', '2-4 semanas'),
      icon: Code,
      description: t('timeline.phase2.description', 'SDK integrado, pipeline de cifrado y ambiente de staging'),
      deliverables: [
        t('timeline.phase2.deliverable1', 'SDK integrado en tu stack'),
        t('timeline.phase2.deliverable2', 'Pipeline de cifrado funcional'),
        t('timeline.phase2.deliverable3', 'Ambiente de staging operativo'),
        t('timeline.phase2.deliverable4', 'Tests de integración pasando')
      ]
    },
    {
      id: 3,
      title: t('timeline.phase3.title', 'Entrenamiento Colaborativo'),
      duration: t('timeline.phase3.duration', '2-3 semanas'),
      icon: Brain,
      description: t('timeline.phase3.description', 'Modelo ML entrenado sobre datos cifrados con métricas validadas'),
      deliverables: [
        t('timeline.phase3.deliverable1', 'Modelo entrenado y validado'),
        t('timeline.phase3.deliverable2', 'Métricas de performance'),
        t('timeline.phase3.deliverable3', 'Dashboard de monitoreo'),
        t('timeline.phase3.deliverable4', 'Documentación del modelo')
      ]
    },
    {
      id: 4,
      title: t('timeline.phase4.title', 'Producción'),
      duration: t('timeline.phase4.duration', '1-2 semanas'),
      icon: Rocket,
      description: t('timeline.phase4.description', 'Deploy a producción con monitoreo y soporte continuo'),
      deliverables: [
        t('timeline.phase4.deliverable1', 'Deploy en producción'),
        t('timeline.phase4.deliverable2', 'Monitoreo 24/7 configurado'),
        t('timeline.phase4.deliverable3', 'Documentación completa'),
        t('timeline.phase4.deliverable4', 'Training para tu equipo')
      ]
    }
  ]

  const includes = [
    { icon: Users, text: t('timeline.includes.support', 'Soporte técnico dedicado') },
    { icon: Cloud, text: t('timeline.includes.cloud', 'Integración AWS/GCP/Azure/on-premise') },
    { icon: Shield, text: t('timeline.includes.compliance', 'Compliance automático (GDPR, HIPAA, PCI-DSS)') },
    { icon: BookOpen, text: t('timeline.includes.training', 'Training para equipo técnico') },
    { icon: Clock, text: t('timeline.includes.sla', 'SLA 99.9% uptime') }
  ]

  return (
    <section className="py-20 px-4">
      <div className="max-w-5xl mx-auto">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            {t('timeline.title', 'Tu camino a la privacidad de datos')}
          </h2>
          <p className="text-white/60 text-lg max-w-2xl mx-auto">
            {t('timeline.subtitle', 'Un proceso claro y probado para implementar FHE en tu organización')}
          </p>
        </motion.div>

        {/* Timeline */}
        <div className="relative">
          {/* Vertical Line */}
          <div className={`absolute left-6 md:left-1/2 top-0 bottom-0 w-0.5 bg-gradient-to-b ${colors.gradient} transform md:-translate-x-1/2`} />

          {/* Phases */}
          {phases.map((phase, idx) => (
            <motion.div
              key={phase.id}
              initial={{ opacity: 0, x: idx % 2 === 0 ? -30 : 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ delay: idx * 0.1 }}
              className={`relative flex items-start gap-4 md:gap-8 mb-8 md:mb-12 ${
                idx % 2 === 0 ? 'md:flex-row' : 'md:flex-row-reverse'
              }`}
            >
              {/* Icon */}
              <div className={`relative z-10 flex-shrink-0 w-12 h-12 rounded-full bg-gradient-to-r ${colors.gradient} flex items-center justify-center shadow-lg`}>
                <phase.icon className="w-6 h-6 text-white" />
              </div>

              {/* Content */}
              <div className={`flex-1 ${idx % 2 === 0 ? 'md:text-right md:pr-8' : 'md:text-left md:pl-8'}`}>
                <div
                  className={`bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/10 hover:border-white/20 transition-all cursor-pointer ${
                    expandedPhase === phase.id ? 'border-white/30' : ''
                  }`}
                  onClick={() => setExpandedPhase(expandedPhase === phase.id ? null : phase.id)}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className={idx % 2 === 0 ? 'md:order-2 md:text-left' : ''}>
                      <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium bg-${colors.bg} text-${colors.accent} mb-2`}>
                        {t('timeline.phase', 'Fase')} {phase.id}
                      </span>
                      <h3 className="text-xl font-bold text-white mb-1">{phase.title}</h3>
                      <div className="flex items-center gap-2 text-white/60 text-sm mb-2">
                        <Clock className="w-4 h-4" />
                        <span>{phase.duration}</span>
                      </div>
                      <p className="text-white/70">{phase.description}</p>
                    </div>
                    <button className="flex-shrink-0 text-white/40 hover:text-white/60">
                      {expandedPhase === phase.id ? (
                        <ChevronUp className="w-5 h-5" />
                      ) : (
                        <ChevronDown className="w-5 h-5" />
                      )}
                    </button>
                  </div>

                  {/* Expanded Content */}
                  {expandedPhase === phase.id && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="mt-4 pt-4 border-t border-white/10"
                    >
                      <h4 className="text-sm font-semibold text-white/40 uppercase tracking-wider mb-3">
                        {t('timeline.deliverables', 'Entregables')}
                      </h4>
                      <ul className={`space-y-2 ${idx % 2 === 0 ? 'md:text-left' : ''}`}>
                        {phase.deliverables.map((deliverable, dIdx) => (
                          <li key={dIdx} className="flex items-center gap-2 text-white/80">
                            <Check className={`w-4 h-4 text-${colors.accent} flex-shrink-0`} />
                            <span>{deliverable}</span>
                          </li>
                        ))}
                      </ul>
                    </motion.div>
                  )}
                </div>
              </div>

              {/* Spacer for opposite side on desktop */}
              <div className="hidden md:block flex-1" />
            </motion.div>
          ))}
        </div>

        {/* What's Included */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mt-16"
        >
          <h3 className="text-2xl font-bold text-white text-center mb-8">
            {t('timeline.includesTitle', '¿Qué incluye?')}
          </h3>
          <div className="grid md:grid-cols-3 lg:grid-cols-5 gap-4">
            {includes.map((item, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: idx * 0.1 }}
                className={`bg-white/5 backdrop-blur-sm rounded-xl p-4 border border-white/10 hover:border-${colors.accent}/30 transition-all text-center`}
              >
                <item.icon className={`w-8 h-8 text-${colors.accent} mx-auto mb-2`} />
                <p className="text-white/80 text-sm">{item.text}</p>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="mt-12 text-center"
        >
          <p className="text-white/60 mb-4">
            {t('timeline.ctaText', '¿Listo para empezar?')}
          </p>
          <a
            href="#contact"
            className={`inline-flex items-center gap-2 bg-gradient-to-r ${colors.gradient} text-white px-8 py-4 rounded-xl font-semibold hover:opacity-90 transition-opacity`}
          >
            {t('timeline.ctaButton', 'Agendar llamada de discovery')}
          </a>
        </motion.div>
      </div>
    </section>
  )
}

export default ImplementationTimeline
