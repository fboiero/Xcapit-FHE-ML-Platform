import React from 'react'
import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import { Star, Quote, Award, Rocket, CheckCircle, ArrowRight } from 'lucide-react'

// Testimonial Card Component
export const TestimonialCard = ({ name, role, company, quote, rating = 5, image, theme = 'blue' }) => {
  const themeColors = {
    blue: 'from-blue-500 to-indigo-600',
    emerald: 'from-emerald-500 to-teal-600',
    slate: 'from-slate-600 to-gray-700',
    purple: 'from-purple-500 to-indigo-600'
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5 }}
      className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20 hover:border-white/40 transition-all duration-300"
    >
      <div className="flex items-start gap-4 mb-4">
        <Quote className={`w-8 h-8 text-${theme === 'blue' ? 'blue' : theme === 'emerald' ? 'emerald' : theme === 'slate' ? 'slate' : 'purple'}-400 opacity-50 flex-shrink-0`} />
      </div>
      <p className="text-white/90 text-lg italic mb-6 leading-relaxed">"{quote}"</p>
      <div className="flex items-center gap-4">
        {image ? (
          <img src={image} alt={name} className="w-12 h-12 rounded-full object-cover" />
        ) : (
          <div className={`w-12 h-12 rounded-full bg-gradient-to-r ${themeColors[theme]} flex items-center justify-center text-white font-bold`}>
            {name.charAt(0)}
          </div>
        )}
        <div>
          <p className="text-white font-semibold">{name}</p>
          <p className="text-white/60 text-sm">{role}</p>
          <p className="text-white/40 text-sm">{company}</p>
        </div>
      </div>
      {rating > 0 && (
        <div className="flex gap-1 mt-4">
          {[...Array(rating)].map((_, i) => (
            <Star key={i} className="w-4 h-4 fill-yellow-400 text-yellow-400" />
          ))}
        </div>
      )}
    </motion.div>
  )
}

// Case Study Card Component
export const CaseStudyCard = ({
  title,
  organization,
  logo,
  challenge,
  solution,
  results,
  quote,
  quotePerson,
  quoteRole,
  timeline,
  theme = 'blue'
}) => {
  const themeColors = {
    blue: { gradient: 'from-blue-500 to-indigo-600', accent: 'blue-400', bg: 'blue-500/20' },
    emerald: { gradient: 'from-emerald-500 to-teal-600', accent: 'emerald-400', bg: 'emerald-500/20' },
    slate: { gradient: 'from-slate-600 to-gray-700', accent: 'slate-400', bg: 'slate-500/20' },
    purple: { gradient: 'from-purple-500 to-indigo-600', accent: 'purple-400', bg: 'purple-500/20' }
  }

  const colors = themeColors[theme]

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.6 }}
      className="bg-white/5 backdrop-blur-sm rounded-3xl p-8 border border-white/10 hover:border-white/20 transition-all duration-300"
    >
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        {logo ? (
          <img src={logo} alt={organization} className="h-12 w-auto" />
        ) : (
          <div className={`w-12 h-12 rounded-xl bg-gradient-to-r ${colors.gradient} flex items-center justify-center`}>
            <Award className="w-6 h-6 text-white" />
          </div>
        )}
        <div>
          <h3 className="text-xl font-bold text-white">{title}</h3>
          <p className="text-white/60">{organization}</p>
        </div>
      </div>

      {/* Challenge & Solution */}
      <div className="grid md:grid-cols-2 gap-6 mb-6">
        <div className="space-y-2">
          <h4 className="text-sm font-semibold text-white/40 uppercase tracking-wider">Desafío</h4>
          <p className="text-white/80">{challenge}</p>
        </div>
        <div className="space-y-2">
          <h4 className="text-sm font-semibold text-white/40 uppercase tracking-wider">Solución</h4>
          <p className="text-white/80">{solution}</p>
        </div>
      </div>

      {/* Results */}
      {results && results.length > 0 && (
        <div className="mb-6">
          <h4 className="text-sm font-semibold text-white/40 uppercase tracking-wider mb-3">Resultados</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {results.map((result, idx) => (
              <div key={idx} className={`bg-${colors.bg} rounded-xl p-4 text-center`}>
                <p className={`text-2xl font-bold text-${colors.accent}`}>{result.value}</p>
                <p className="text-white/60 text-sm">{result.label}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quote */}
      {quote && (
        <div className={`bg-gradient-to-r ${colors.gradient} rounded-xl p-6 mt-6`}>
          <Quote className="w-6 h-6 text-white/50 mb-2" />
          <p className="text-white italic mb-4">"{quote}"</p>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center text-white text-sm font-bold">
              {quotePerson?.charAt(0)}
            </div>
            <div>
              <p className="text-white font-medium text-sm">{quotePerson}</p>
              <p className="text-white/70 text-xs">{quoteRole}</p>
            </div>
          </div>
        </div>
      )}

      {/* Timeline */}
      {timeline && (
        <div className="mt-6 pt-6 border-t border-white/10">
          <p className="text-white/60 text-sm">
            <span className="font-semibold">Implementación:</span> {timeline}
          </p>
        </div>
      )}
    </motion.div>
  )
}

// Early Adopter Card Component
export const EarlyAdopterCard = ({ onApply, theme = 'blue' }) => {
  const { t } = useTranslation()

  const themeColors = {
    blue: { gradient: 'from-blue-500 to-indigo-600', ring: 'ring-blue-500/50' },
    emerald: { gradient: 'from-emerald-500 to-teal-600', ring: 'ring-emerald-500/50' },
    slate: { gradient: 'from-slate-500 to-gray-600', ring: 'ring-slate-500/50' },
    purple: { gradient: 'from-purple-500 to-indigo-600', ring: 'ring-purple-500/50' }
  }

  const colors = themeColors[theme]

  const benefits = [
    { key: 'discount', icon: '💰', default: '50% de descuento el primer año' },
    { key: 'support', icon: '🚀', default: 'Soporte prioritario de implementación' },
    { key: 'caseStudy', icon: '📈', default: 'Tu caso de éxito publicado' },
    { key: 'influence', icon: '💡', default: 'Influencia en el roadmap del producto' }
  ]

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      whileInView={{ opacity: 1, scale: 1 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5 }}
      className={`relative overflow-hidden rounded-3xl bg-gradient-to-br ${colors.gradient} p-8 md:p-10`}
    >
      {/* Background decoration */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
      <div className="absolute bottom-0 left-0 w-48 h-48 bg-black/10 rounded-full blur-2xl translate-y-1/2 -translate-x-1/2" />

      <div className="relative z-10">
        <div className="flex items-center gap-3 mb-4">
          <Rocket className="w-8 h-8 text-white" />
          <span className="text-white/80 text-sm font-medium uppercase tracking-wider">
            {t('earlyAdopter.badge', 'Programa Early Adopter')}
          </span>
        </div>

        <h3 className="text-3xl md:text-4xl font-bold text-white mb-4">
          {t('earlyAdopter.title', 'Sé de los primeros en innovar')}
        </h3>

        <p className="text-white/80 text-lg mb-8 max-w-2xl">
          {t('earlyAdopter.description', 'Únete a nuestro programa exclusivo de early adopters y obtén beneficios únicos mientras transformas tu industria con privacidad de datos de próxima generación.')}
        </p>

        <div className="grid md:grid-cols-2 gap-4 mb-8">
          {benefits.map((benefit, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ delay: idx * 0.1 }}
              className="flex items-center gap-3 bg-white/10 rounded-xl p-4"
            >
              <span className="text-2xl">{benefit.icon}</span>
              <span className="text-white font-medium">
                {t(`earlyAdopter.benefits.${benefit.key}`, benefit.default)}
              </span>
            </motion.div>
          ))}
        </div>

        <motion.button
          onClick={onApply}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className={`group flex items-center gap-2 bg-white text-gray-900 px-8 py-4 rounded-xl font-bold text-lg hover:bg-white/90 transition-all ring-4 ${colors.ring}`}
        >
          {t('earlyAdopter.cta', 'Aplicar al programa')}
          <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
        </motion.button>

        <p className="text-white/60 text-sm mt-4">
          {t('earlyAdopter.limited', '* Plazas limitadas. Respondemos en 24-48 horas.')}
        </p>
      </div>
    </motion.div>
  )
}

// Main Testimonial Section Component
const TestimonialSection = ({
  testimonials = [],
  caseStudy = null,
  showEarlyAdopter = true,
  onEarlyAdopterApply,
  theme = 'blue',
  title,
  subtitle
}) => {
  const { t } = useTranslation()

  return (
    <section className="py-20 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            {title || t('testimonials.title', 'Lo que dicen nuestros clientes')}
          </h2>
          <p className="text-white/60 text-lg max-w-2xl mx-auto">
            {subtitle || t('testimonials.subtitle', 'Organizaciones líderes confían en Xcapit para proteger sus datos más sensibles')}
          </p>
        </motion.div>

        {/* Case Study (if provided) */}
        {caseStudy && (
          <div className="mb-16">
            <CaseStudyCard {...caseStudy} theme={theme} />
          </div>
        )}

        {/* Testimonials Grid */}
        {testimonials.length > 0 && (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">
            {testimonials.map((testimonial, idx) => (
              <TestimonialCard key={idx} {...testimonial} theme={theme} />
            ))}
          </div>
        )}

        {/* Early Adopter Card */}
        {showEarlyAdopter && (
          <EarlyAdopterCard onApply={onEarlyAdopterApply} theme={theme} />
        )}
      </div>
    </section>
  )
}

export default TestimonialSection
