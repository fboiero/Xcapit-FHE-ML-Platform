import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import LanguageSwitcher from '../components/LanguageSwitcher'

// Hook for scroll-triggered animations
function useScrollAnimation(threshold = 0.1) {
  const ref = useRef(null)
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true)
          observer.unobserve(entry.target)
        }
      },
      { threshold }
    )

    if (ref.current) observer.observe(ref.current)
    return () => observer.disconnect()
  }, [threshold])

  return [ref, isVisible]
}

// Animated counter hook
function useCounter(end, duration = 2000, isVisible = true) {
  const [count, setCount] = useState(0)
  const [hasStarted, setHasStarted] = useState(false)

  useEffect(() => {
    if (!isVisible || hasStarted) return
    setHasStarted(true)
    let startTime = null
    const animate = (timestamp) => {
      if (!startTime) startTime = timestamp
      const progress = Math.min((timestamp - startTime) / duration, 1)
      setCount(Math.floor(progress * end))
      if (progress < 1) requestAnimationFrame(animate)
    }
    requestAnimationFrame(animate)
  }, [end, duration, isVisible, hasStarted])

  return count
}

// Particle background animation with floating particles
function ParticleBackground() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {/* Large gradient blurs */}
      <div className="absolute top-0 -left-40 w-[500px] h-[500px] bg-brand-500/20 rounded-full blur-[150px] animate-pulse" />
      <div className="absolute bottom-0 -right-40 w-[500px] h-[500px] bg-indigo-500/20 rounded-full blur-[150px] animate-pulse" style={{ animationDelay: '1s' }} />

      {/* Floating particles */}
      {[...Array(15)].map((_, i) => (
        <div
          key={i}
          className="absolute w-1 h-1 bg-brand-400/40 rounded-full"
          style={{
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
            animation: `float ${3 + Math.random() * 4}s ease-in-out infinite`,
            animationDelay: `${Math.random() * 2}s`
          }}
        />
      ))}

      <style>{`
        @keyframes float {
          0%, 100% { transform: translateY(0) translateX(0); opacity: 0.4; }
          50% { transform: translateY(-20px) translateX(10px); opacity: 0.8; }
        }
      `}</style>
    </div>
  )
}

// Hero illustration - Financial data encryption visualization
function HeroIllustration() {
  return (
    <div className="relative w-full max-w-lg mx-auto">
      <svg viewBox="0 0 400 300" className="w-full h-auto">
        <defs>
          <linearGradient id="gradientBlue" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#3b82f6" />
            <stop offset="100%" stopColor="#6366f1" />
          </linearGradient>
          <linearGradient id="gradientGreen" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#10b981" />
            <stop offset="100%" stopColor="#06b6d4" />
          </linearGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
            <feMerge>
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>

        {/* Bank nodes */}
        <g className="animate-pulse" style={{ animationDuration: '3s' }}>
          {/* Bank A */}
          <rect x="30" y="50" width="70" height="50" rx="8" fill="#1e293b" stroke="url(#gradientBlue)" strokeWidth="2" />
          <text x="65" y="72" textAnchor="middle" fill="#94a3b8" fontSize="10" fontWeight="500">Bank A</text>
          <rect x="42" y="82" width="46" height="8" rx="2" fill="#334155" />

          {/* Bank B */}
          <rect x="30" y="130" width="70" height="50" rx="8" fill="#1e293b" stroke="url(#gradientBlue)" strokeWidth="2" />
          <text x="65" y="152" textAnchor="middle" fill="#94a3b8" fontSize="10" fontWeight="500">Bank B</text>
          <rect x="42" y="162" width="46" height="8" rx="2" fill="#334155" />

          {/* Bank C */}
          <rect x="30" y="210" width="70" height="50" rx="8" fill="#1e293b" stroke="url(#gradientBlue)" strokeWidth="2" />
          <text x="65" y="232" textAnchor="middle" fill="#94a3b8" fontSize="10" fontWeight="500">Bank C</text>
          <rect x="42" y="242" width="46" height="8" rx="2" fill="#334155" />
        </g>

        {/* Connection lines with animation */}
        <path d="M100 75 Q150 75 175 130" stroke="url(#gradientBlue)" strokeWidth="2" fill="none" strokeDasharray="5,5" opacity="0.6">
          <animate attributeName="stroke-dashoffset" from="0" to="-20" dur="2s" repeatCount="indefinite"/>
        </path>
        <path d="M100 155 L175 155" stroke="url(#gradientBlue)" strokeWidth="2" fill="none" strokeDasharray="5,5" opacity="0.6">
          <animate attributeName="stroke-dashoffset" from="0" to="-20" dur="2s" repeatCount="indefinite"/>
        </path>
        <path d="M100 235 Q150 235 175 180" stroke="url(#gradientBlue)" strokeWidth="2" fill="none" strokeDasharray="5,5" opacity="0.6">
          <animate attributeName="stroke-dashoffset" from="0" to="-20" dur="2s" repeatCount="indefinite"/>
        </path>

        {/* Central encrypted model */}
        <g filter="url(#glow)">
          <rect x="175" y="110" width="90" height="90" rx="12" fill="#1e293b" stroke="url(#gradientGreen)" strokeWidth="2"/>

          {/* Lock icon */}
          <path d="M220 135 L220 145 M208 152 L208 175 L232 175 L232 152 L208 152 M212 152 L212 145 C212 139 217 135 220 135 C223 135 228 139 228 145 L228 152"
                stroke="white" strokeWidth="2" fill="none" strokeLinecap="round"/>

          {/* Encrypted text representation */}
          <text x="220" y="188" textAnchor="middle" fill="#10b981" fontSize="8" fontFamily="monospace">FHE Model</text>
        </g>

        {/* Output lines */}
        <path d="M265 130 Q290 130 310 100" stroke="url(#gradientGreen)" strokeWidth="2" fill="none" strokeDasharray="5,5" opacity="0.6">
          <animate attributeName="stroke-dashoffset" from="-20" to="0" dur="2s" repeatCount="indefinite"/>
        </path>
        <path d="M265 155 L310 155" stroke="url(#gradientGreen)" strokeWidth="2" fill="none" strokeDasharray="5,5" opacity="0.6">
          <animate attributeName="stroke-dashoffset" from="-20" to="0" dur="2s" repeatCount="indefinite"/>
        </path>
        <path d="M265 180 Q290 180 310 210" stroke="url(#gradientGreen)" strokeWidth="2" fill="none" strokeDasharray="5,5" opacity="0.6">
          <animate attributeName="stroke-dashoffset" from="-20" to="0" dur="2s" repeatCount="indefinite"/>
        </path>

        {/* Results */}
        <g className="animate-pulse" style={{ animationDuration: '2s', animationDelay: '1s' }}>
          <rect x="310" y="80" width="70" height="40" rx="8" fill="#1e293b" stroke="url(#gradientGreen)" strokeWidth="1.5" />
          <text x="345" y="97" textAnchor="middle" fill="#10b981" fontSize="8">Fraud Score</text>
          <text x="345" y="112" textAnchor="middle" fill="white" fontSize="12" fontWeight="bold">0.02</text>

          <rect x="310" y="135" width="70" height="40" rx="8" fill="#1e293b" stroke="url(#gradientGreen)" strokeWidth="1.5" />
          <text x="345" y="152" textAnchor="middle" fill="#10b981" fontSize="8">Credit Risk</text>
          <text x="345" y="167" textAnchor="middle" fill="white" fontSize="12" fontWeight="bold">Low</text>

          <rect x="310" y="190" width="70" height="40" rx="8" fill="#1e293b" stroke="url(#gradientGreen)" strokeWidth="1.5" />
          <text x="345" y="207" textAnchor="middle" fill="#10b981" fontSize="8">AML Flag</text>
          <text x="345" y="222" textAnchor="middle" fill="white" fontSize="12" fontWeight="bold">Clear</text>
        </g>

        {/* Floating data particles */}
        <circle cx="140" cy="90" r="3" fill="#3b82f6" opacity="0.6">
          <animate attributeName="cx" values="140;160;140" dur="3s" repeatCount="indefinite"/>
        </circle>
        <circle cx="145" cy="155" r="2" fill="#6366f1" opacity="0.6">
          <animate attributeName="cx" values="145;165;145" dur="2.5s" repeatCount="indefinite"/>
        </circle>
        <circle cx="140" cy="220" r="3" fill="#3b82f6" opacity="0.6">
          <animate attributeName="cx" values="140;160;140" dur="3.5s" repeatCount="indefinite"/>
        </circle>
      </svg>
    </div>
  )
}

// Stat card component
function StatCard({ value, label, icon }) {
  return (
    <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/10 hover:border-brand-400/30 transition-all duration-300">
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 bg-gradient-to-br from-brand-500/20 to-indigo-500/20 rounded-xl flex items-center justify-center text-2xl">
          {icon}
        </div>
        <div>
          <div className="text-3xl font-bold text-white">{value}</div>
          <div className="text-slate-400 text-sm">{label}</div>
        </div>
      </div>
    </div>
  )
}

// Contact Form Component
function ContactForm({ lang }) {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    company: '',
    phone: '',
    job_title: '',
    use_case: ''
  })
  const [status, setStatus] = useState('idle')

  const content = {
    es: {
      title: 'Agendar Demo de 30 minutos',
      subtitle: 'Te mostramos cómo funciona con un caso real de tu industria.',
      name: 'Nombre completo',
      email: 'Email corporativo',
      company: 'Empresa',
      phone: 'Teléfono',
      position: 'Cargo',
      useCase: 'Caso de uso de interés',
      useCases: ['Detección de fraude', 'Credit scoring', 'KYC/AML', 'Otro'],
      submit: 'Agendar Demo',
      sending: 'Enviando...',
      success: 'Mensaje enviado. Te contactaremos pronto.',
      error: 'Error al enviar. Intenta de nuevo.',
      also: 'También puedes contactarnos en'
    },
    en: {
      title: 'Book a 30-minute Demo',
      subtitle: 'We\'ll show you how it works with a real case from your industry.',
      name: 'Full name',
      email: 'Corporate email',
      company: 'Company',
      phone: 'Phone',
      position: 'Job title',
      useCase: 'Use case of interest',
      useCases: ['Fraud detection', 'Credit scoring', 'KYC/AML', 'Other'],
      submit: 'Book Demo',
      sending: 'Sending...',
      success: 'Message sent. We\'ll contact you soon.',
      error: 'Error sending. Please try again.',
      also: 'You can also contact us at'
    }
  }

  const t = content[lang]

  const handleSubmit = async (e) => {
    e.preventDefault()
    setStatus('sending')

    try {
      const response = await fetch('https://api.web3forms.com/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          access_key: 'd7f419bc-95cf-498d-8d8b-5f4830622bf4',
          subject: 'Demo Request - Fintech - Xcapit Privacy',
          from_name: 'Xcapit Privacy',
          vertical: 'Fintech',
          ...formData
        }),
      })

      if (response.ok) {
        setStatus('success')
        setFormData({ name: '', email: '', company: '', phone: '', job_title: '', use_case: '' })
      } else {
        setStatus('error')
      }
    } catch (err) {
      setStatus('error')
    }
  }

  return (
    <div className="bg-white/10 backdrop-blur-md rounded-2xl p-8 border border-white/20 shadow-2xl">
      <h3 className="text-2xl font-bold text-white mb-2">{t.title}</h3>
      <p className="text-slate-300 mb-6">{t.subtitle}</p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid md:grid-cols-2 gap-4">
          <input
            type="text"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder={t.name}
            required
            className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl focus:outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-400/20 text-white placeholder-slate-400 transition"
          />
          <input
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            placeholder={t.email}
            required
            className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl focus:outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-400/20 text-white placeholder-slate-400 transition"
          />
        </div>
        <div className="grid md:grid-cols-2 gap-4">
          <input
            type="text"
            value={formData.company}
            onChange={(e) => setFormData({ ...formData, company: e.target.value })}
            placeholder={t.company}
            required
            className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl focus:outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-400/20 text-white placeholder-slate-400 transition"
          />
          <input
            type="tel"
            value={formData.phone}
            onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
            placeholder={t.phone}
            className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl focus:outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-400/20 text-white placeholder-slate-400 transition"
          />
        </div>
        <input
          type="text"
          value={formData.job_title}
          onChange={(e) => setFormData({ ...formData, job_title: e.target.value })}
          placeholder={t.position}
          required
          className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl focus:outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-400/20 text-white placeholder-slate-400 transition"
        />
        <select
          value={formData.use_case}
          onChange={(e) => setFormData({ ...formData, use_case: e.target.value })}
          required
          className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl focus:outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-400/20 text-white placeholder-slate-400 transition appearance-none cursor-pointer"
        >
          <option value="" className="bg-slate-800">{t.useCase}</option>
          {t.useCases.map(uc => (
            <option key={uc} value={uc} className="bg-slate-800">{uc}</option>
          ))}
        </select>

        <button
          type="submit"
          disabled={status === 'sending'}
          className="w-full bg-gradient-to-r from-brand-500 to-indigo-500 text-white py-4 px-6 rounded-xl font-semibold hover:from-brand-600 hover:to-indigo-600 transition disabled:opacity-50 shadow-lg shadow-brand-500/25"
        >
          {status === 'sending' ? t.sending : t.submit}
        </button>

        {status === 'success' && (
          <p className="text-green-400 text-center font-medium">{t.success}</p>
        )}
        {status === 'error' && (
          <p className="text-red-400 text-center font-medium">{t.error}</p>
        )}
      </form>

      <p className="mt-6 text-center text-sm text-slate-400">
        {t.also}{' '}
        <a href="mailto:consorcios@xcapit.com" className="text-brand-400 font-medium hover:underline">
          consorcios@xcapit.com
        </a>
      </p>
    </div>
  )
}

// Use Case Card Component
function UseCaseCard({ title, problem, solution, metric, icon, lang }) {
  return (
    <div className="group bg-white rounded-2xl p-8 border border-slate-200 hover:shadow-2xl hover:shadow-brand-500/10 hover:-translate-y-1 transition-all duration-300">
      <div className="w-14 h-14 bg-gradient-to-br from-brand-500/10 to-indigo-500/10 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
        {icon}
      </div>
      <h3 className="text-xl font-bold text-slate-900 mb-4">{title}</h3>
      <div className="mb-4">
        <span className="inline-flex items-center gap-1.5 text-sm font-semibold text-red-600 uppercase tracking-wider">
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          {lang === 'es' ? 'El Problema' : 'The Problem'}
        </span>
        <p className="text-slate-600 mt-2">{problem}</p>
      </div>
      <div className="mb-4">
        <span className="inline-flex items-center gap-1.5 text-sm font-semibold text-emerald-600 uppercase tracking-wider">
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
          {lang === 'es' ? 'La Solución' : 'The Solution'}
        </span>
        <p className="text-slate-600 mt-2">{solution}</p>
      </div>
      <div className="mt-6 pt-4 border-t border-slate-100">
        <span className="text-3xl font-bold bg-gradient-to-r from-brand-600 to-indigo-600 bg-clip-text text-transparent">
          {metric}
        </span>
      </div>
    </div>
  )
}

// Compliance badge component
function ComplianceBadge({ name, icon }) {
  return (
    <div className="flex items-center gap-2 bg-emerald-50 border border-emerald-200 px-5 py-2.5 rounded-full hover:scale-105 transition-transform">
      {icon}
      <span className="font-semibold text-emerald-800">{name}</span>
    </div>
  )
}

// Step component for how it works
function StepCard({ number, title, description, icon }) {
  return (
    <div className="relative group">
      <div className="absolute -inset-0.5 bg-gradient-to-r from-brand-500 to-indigo-500 rounded-2xl blur opacity-0 group-hover:opacity-30 transition duration-500" />
      <div className="relative bg-white rounded-2xl p-8 border border-slate-200">
        <div className="w-12 h-12 bg-gradient-to-br from-brand-500 to-indigo-500 rounded-xl flex items-center justify-center text-white font-bold text-lg mb-4">
          {number}
        </div>
        <h3 className="text-xl font-bold text-slate-900 mb-2">{title}</h3>
        <p className="text-slate-600">{description}</p>
      </div>
    </div>
  )
}

export default function LandingFintech() {
  const { i18n } = useTranslation()
  const lang = i18n.language?.startsWith('es') ? 'es' : 'en'
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const content = {
    es: {
      nav: {
        casosUso: 'Casos de Uso',
        comoFunciona: 'Cómo Funciona',
        seguridad: 'Seguridad',
        demo: 'Demo'
      },
      hero: {
        badge: 'Fintech & Banking',
        headline: 'Modelos de fraude entrenados con datos de toda la industria.',
        highlight: 'Sin compartir ni un dato.',
        subheadline: 'Los defraudadores conocen los patrones de todos los bancos. Ahora ustedes también pueden. Con cifrado homomórfico, múltiples instituciones entrenan UN modelo compartido sin que nadie vea los datos del otro.',
        cta: 'Agendar Demo',
        ctaSecondary: 'Ver cómo funciona',
        stats: {
          detection: { value: '+40%', label: 'Detección de fraude' },
          default: { value: '-25%', label: 'Tasa de default' },
          compliance: { value: '100%', label: 'Compliance' }
        }
      },
      trustedBy: {
        title: 'Tecnología utilizada por líderes de la industria',
        partners: ['Microsoft SEAL', 'TenSEAL', 'OpenFHE', 'HElib']
      },
      problem: {
        title: 'Tu modelo solo conoce el fraude que ya te pasó',
        points: [
          {
            title: 'El problema del silo',
            desc: 'Cada banco entrena su modelo de fraude con sus propios datos. Los defraudadores conocen patrones de toda la industria. Ustedes solo conocen los suyos.',
            icon: '🔒'
          },
          {
            title: 'Regulación que impide colaborar',
            desc: 'Quieres compartir patrones con otros bancos, pero PCI-DSS, LGPD y secreto bancario lo hacen imposible. O eso creías.',
            icon: '⚖️'
          },
          {
            title: 'Clientes nuevos = riesgo desconocido',
            desc: 'Sin historial en tu institución, cada cliente nuevo es una apuesta. Pero ese cliente tiene años de comportamiento en otros lugares que nunca podrás ver.',
            icon: '❓'
          }
        ]
      },
      solution: {
        title: 'Colabora sin compartir',
        desc: 'Con cifrado homomórfico, tus datos nunca salen de tu infraestructura. Solo enviás versiones cifradas que permiten entrenar modelos compartidos. Nadie puede descifrar tus datos - ni siquiera nosotros.',
        steps: [
          { title: 'Cifras localmente', desc: 'Tu clave privada nunca sale de tu infraestructura' },
          { title: 'Entrenas sobre cifrado', desc: 'El servidor hace cálculos sin descifrar jamás' },
          { title: 'Descifras tus resultados', desc: 'Solo tú puedes ver tus predicciones' }
        ]
      },
      useCases: {
        title: 'Casos de Uso',
        subtitle: 'Soluciones específicas para el sector financiero',
        cases: [
          {
            title: 'Detección de Fraude Colaborativo',
            problem: 'Tu modelo detecta el fraude que ya te pasó. Los nuevos vectores de ataque que están usando en otros bancos? Los vas a conocer cuando te ataquen a vos.',
            solution: 'Modelo entrenado con patrones de fraude de múltiples instituciones. Detecta ataques antes de que lleguen a tu banco.',
            metric: '+40% detección'
          },
          {
            title: 'Credit Scoring Compartido',
            problem: 'Un cliente sin historial en tu banco es una caja negra. Aprobarlo es arriesgado. Rechazarlo es perder negocio.',
            solution: 'Score basado en comportamiento crediticio cross-institucional, sin que ninguna institución revele datos de sus clientes.',
            metric: '-25% default'
          },
          {
            title: 'KYC/AML Colaborativo',
            problem: 'Cada banco hace KYC de forma aislada. Un cliente rechazado en un banco abre cuenta en otro. Las redes de lavado operan cross-institucional.',
            solution: 'Detección de patrones sospechosos y redes de lavado que operan entre múltiples instituciones.',
            metric: 'Redes invisibles detectadas'
          }
        ]
      },
      compliance: {
        title: 'Cumplimiento regulatorio garantizado',
        desc: 'Como los datos nunca se descifran, no hay exposición de información personal. La colaboración ocurre 100% sobre datos cifrados.',
        badges: ['PCI-DSS', 'GDPR', 'SOC2 Type II', 'LGPD', 'Secreto Bancario']
      },
      differentiators: {
        title: '¿Por qué Xcapit y no otras opciones?',
        headers: ['Característica', 'Xcapit', 'Data Clean Rooms', 'Federated Learning', 'MPC'],
        rows: [
          ['Datos nunca descifrados', true, false, false, 'partial'],
          ['ML sobre cifrado', true, false, false, false],
          ['Auditoría blockchain', true, false, false, false],
          ['Sin trusted third party', true, false, true, true],
          ['Compliance automático', true, 'partial', false, false]
        ]
      },
      cta: {
        title: '¿Listo para entrenar con datos que no puedes ver?',
        subtitle: 'Agenda una demo de 30 minutos. Te mostramos cómo funciona con un caso real de tu industria.'
      },
      footer: {
        product: 'Producto',
        resources: 'Recursos',
        contact: 'Contacto',
        rights: '© 2025 Xcapit Privacy. Todos los derechos reservados.',
        links: {
          industries: 'Otras industrias',
          docs: 'Documentación',
          github: 'GitHub'
        }
      }
    },
    en: {
      nav: {
        casosUso: 'Use Cases',
        comoFunciona: 'How it Works',
        seguridad: 'Security',
        demo: 'Demo'
      },
      hero: {
        badge: 'Fintech & Banking',
        headline: 'Fraud models trained on industry-wide data.',
        highlight: 'Without sharing a single record.',
        subheadline: 'Fraudsters know patterns from all banks. Now you can too. With homomorphic encryption, multiple institutions train ONE shared model without anyone seeing each other\'s data.',
        cta: 'Book Demo',
        ctaSecondary: 'See how it works',
        stats: {
          detection: { value: '+40%', label: 'Fraud detection' },
          default: { value: '-25%', label: 'Default rate' },
          compliance: { value: '100%', label: 'Compliance' }
        }
      },
      trustedBy: {
        title: 'Technology used by industry leaders',
        partners: ['Microsoft SEAL', 'TenSEAL', 'OpenFHE', 'HElib']
      },
      problem: {
        title: 'Your model only knows the fraud you\'ve already experienced',
        points: [
          {
            title: 'The silo problem',
            desc: 'Each bank trains its fraud model with its own data. Fraudsters know patterns from the entire industry. You only know yours.',
            icon: '🔒'
          },
          {
            title: 'Regulation prevents collaboration',
            desc: 'You want to share patterns with other banks, but PCI-DSS, GDPR, and banking secrecy make it impossible. Or so you thought.',
            icon: '⚖️'
          },
          {
            title: 'New customers = unknown risk',
            desc: 'Without history at your institution, every new customer is a gamble. But that customer has years of behavior elsewhere you\'ll never see.',
            icon: '❓'
          }
        ]
      },
      solution: {
        title: 'Collaborate without sharing',
        desc: 'With homomorphic encryption, your data never leaves your infrastructure. You only send encrypted versions that enable shared model training. No one can decrypt your data - not even us.',
        steps: [
          { title: 'Encrypt locally', desc: 'Your private key never leaves your infrastructure' },
          { title: 'Train on encrypted', desc: 'Server computes without ever decrypting' },
          { title: 'Decrypt your results', desc: 'Only you can see your predictions' }
        ]
      },
      useCases: {
        title: 'Use Cases',
        subtitle: 'Specific solutions for the financial sector',
        cases: [
          {
            title: 'Collaborative Fraud Detection',
            problem: 'Your model detects fraud you\'ve already experienced. New attack vectors being used at other banks? You\'ll learn about them when they hit you.',
            solution: 'Model trained on fraud patterns from multiple institutions. Detect attacks before they reach your bank.',
            metric: '+40% detection'
          },
          {
            title: 'Shared Credit Scoring',
            problem: 'A customer with no history at your bank is a black box. Approving them is risky. Rejecting them loses business.',
            solution: 'Score based on cross-institutional credit behavior, without any institution revealing customer data.',
            metric: '-25% default'
          },
          {
            title: 'Collaborative KYC/AML',
            problem: 'Each bank does KYC in isolation. A customer rejected at one bank opens an account at another. Money laundering networks operate cross-institutionally.',
            solution: 'Detection of suspicious patterns and laundering networks operating across institutions.',
            metric: 'Invisible networks detected'
          }
        ]
      },
      compliance: {
        title: 'Regulatory compliance guaranteed',
        desc: 'Since data is never decrypted, there\'s no exposure of personal information. Collaboration happens 100% on encrypted data.',
        badges: ['PCI-DSS', 'GDPR', 'SOC2 Type II', 'LGPD', 'Banking Secrecy']
      },
      differentiators: {
        title: 'Why Xcapit over alternatives?',
        headers: ['Feature', 'Xcapit', 'Data Clean Rooms', 'Federated Learning', 'MPC'],
        rows: [
          ['Data never decrypted', true, false, false, 'partial'],
          ['ML on encrypted', true, false, false, false],
          ['Blockchain audit', true, false, false, false],
          ['No trusted third party', true, false, true, true],
          ['Auto compliance', true, 'partial', false, false]
        ]
      },
      cta: {
        title: 'Ready to train on data you can\'t see?',
        subtitle: 'Book a 30-minute demo. We\'ll show you how it works with a real case from your industry.'
      },
      footer: {
        product: 'Product',
        resources: 'Resources',
        contact: 'Contact',
        rights: '© 2025 Xcapit Privacy. All rights reserved.',
        links: {
          industries: 'Other industries',
          docs: 'Documentation',
          github: 'GitHub'
        }
      }
    }
  }

  const t = content[lang]

  const useCaseIcons = [
    <svg key="fraud" className="w-7 h-7 text-brand-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>,
    <svg key="credit" className="w-7 h-7 text-brand-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>,
    <svg key="kyc" className="w-7 h-7 text-brand-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
    </svg>
  ]

  const renderCheckmark = (value) => {
    if (value === true) {
      return (
        <div className="w-8 h-8 bg-emerald-100 rounded-full flex items-center justify-center mx-auto">
          <svg className="w-5 h-5 text-emerald-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        </div>
      )
    }
    if (value === 'partial') {
      return (
        <div className="w-8 h-8 bg-amber-100 rounded-full flex items-center justify-center mx-auto">
          <svg className="w-5 h-5 text-amber-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
          </svg>
        </div>
      )
    }
    return (
      <div className="w-8 h-8 bg-slate-100 rounded-full flex items-center justify-center mx-auto">
        <svg className="w-5 h-5 text-slate-400" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
        </svg>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Navigation */}
      <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled ? 'bg-slate-900/95 backdrop-blur-md shadow-lg' : 'bg-transparent'
      }`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link to="/hub" className="flex items-center group">
              <div className="w-10 h-10 bg-gradient-to-br from-brand-500 to-indigo-600 rounded-xl flex items-center justify-center mr-2 group-hover:scale-105 transition-transform">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <span className="text-xl font-bold text-white">Xcapit</span>
              <span className="text-xl font-light text-brand-400 ml-1">Privacy</span>
            </Link>
            <div className="hidden md:flex items-center gap-6">
              <a href="#use-cases" className="text-slate-300 hover:text-white font-medium transition">{t.nav.casosUso}</a>
              <a href="#how-it-works" className="text-slate-300 hover:text-white font-medium transition">{t.nav.comoFunciona}</a>
              <a href="#compliance" className="text-slate-300 hover:text-white font-medium transition">{t.nav.seguridad}</a>
            </div>
            <div className="flex items-center gap-3">
              <LanguageSwitcher variant="toggle" />
              <a href="#contact" className="bg-gradient-to-r from-brand-500 to-indigo-600 text-white px-5 py-2.5 rounded-lg font-medium hover:from-brand-600 hover:to-indigo-700 transition shadow-lg shadow-brand-500/25">
                {t.hero.cta}
              </a>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center pt-16 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950" />
        <div className="absolute inset-0">
          <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-brand-500/10 rounded-full blur-3xl" />
          <div className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] bg-indigo-500/10 rounded-full blur-3xl" />
        </div>
        <ParticleBackground />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <div className="inline-flex items-center gap-2 bg-white/5 backdrop-blur-sm px-4 py-2 rounded-full mb-8 border border-white/10">
                <span className="text-2xl">🏦</span>
                <span className="text-white/90 text-sm font-medium">{t.hero.badge}</span>
              </div>

              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-6 leading-tight">
                {t.hero.headline}
                <br />
                <span className="bg-gradient-to-r from-brand-400 via-indigo-400 to-cyan-400 bg-clip-text text-transparent">
                  {t.hero.highlight}
                </span>
              </h1>

              <p className="text-lg lg:text-xl text-slate-300 mb-8 max-w-xl leading-relaxed">
                {t.hero.subheadline}
              </p>

              <div className="flex flex-col sm:flex-row gap-4 mb-12">
                <a
                  href="#contact"
                  className="inline-flex items-center justify-center gap-3 bg-gradient-to-r from-brand-500 to-indigo-600 text-white px-8 py-4 rounded-xl font-semibold hover:from-brand-600 hover:to-indigo-700 transition text-lg shadow-2xl shadow-brand-500/25"
                >
                  {t.hero.cta}
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                  </svg>
                </a>
                <a
                  href="#how-it-works"
                  className="inline-flex items-center justify-center gap-2 bg-white/5 backdrop-blur-sm text-white px-8 py-4 rounded-xl font-semibold hover:bg-white/10 transition text-lg border border-white/10"
                >
                  {t.hero.ctaSecondary}
                </a>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-3 gap-4">
                <StatCard
                  value={t.hero.stats.detection.value}
                  label={t.hero.stats.detection.label}
                  icon="📈"
                />
                <StatCard
                  value={t.hero.stats.default.value}
                  label={t.hero.stats.default.label}
                  icon="📉"
                />
                <StatCard
                  value={t.hero.stats.compliance.value}
                  label={t.hero.stats.compliance.label}
                  icon="✓"
                />
              </div>
            </div>

            <div className="hidden lg:block">
              <HeroIllustration />
            </div>
          </div>
        </div>
      </section>

      {/* Trusted By Section */}
      <section className="relative py-12 border-y border-white/5 bg-slate-900/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-center text-slate-500 text-sm uppercase tracking-wider mb-8">{t.trustedBy.title}</p>
          <div className="flex flex-wrap justify-center items-center gap-8 md:gap-16">
            {t.trustedBy.partners.map((partner, idx) => (
              <div key={idx} className="text-slate-400 font-semibold text-lg hover:text-white transition cursor-default">
                {partner}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Problem Section */}
      <section className="py-24 bg-slate-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              {t.problem.title}
            </h2>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {t.problem.points.map((point, index) => (
              <div key={index} className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-8 border border-slate-700 hover:border-red-500/30 transition-colors">
                <div className="w-14 h-14 bg-red-500/10 rounded-2xl flex items-center justify-center mb-6">
                  <span className="text-3xl">{point.icon}</span>
                </div>
                <h3 className="text-xl font-bold text-white mb-3">{point.title}</h3>
                <p className="text-slate-400">{point.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Solution Section */}
      <section id="how-it-works" className="py-24 bg-slate-950">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              {t.solution.title}
            </h2>
            <p className="text-xl text-slate-400 max-w-3xl mx-auto">
              {t.solution.desc}
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {t.solution.steps.map((step, index) => (
              <StepCard
                key={index}
                number={index + 1}
                title={step.title}
                description={step.desc}
              />
            ))}
          </div>
        </div>
      </section>

      {/* Use Cases Section */}
      <section id="use-cases" className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4">
              {t.useCases.title}
            </h2>
            <p className="text-xl text-slate-600">{t.useCases.subtitle}</p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {t.useCases.cases.map((useCase, index) => (
              <UseCaseCard
                key={index}
                title={useCase.title}
                problem={useCase.problem}
                solution={useCase.solution}
                metric={useCase.metric}
                icon={useCaseIcons[index]}
                lang={lang}
              />
            ))}
          </div>
        </div>
      </section>

      {/* Compliance Section */}
      <section id="compliance" className="py-24 bg-slate-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4">
              {t.compliance.title}
            </h2>
            <p className="text-xl text-slate-600 max-w-3xl mx-auto">
              {t.compliance.desc}
            </p>
          </div>

          <div className="flex flex-wrap justify-center gap-4">
            {t.compliance.badges.map((badge, index) => (
              <ComplianceBadge
                key={index}
                name={badge}
                icon={
                  <svg className="w-5 h-5 text-emerald-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                }
              />
            ))}
          </div>
        </div>
      </section>

      {/* Differentiators Section */}
      <section className="py-24 bg-white">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl md:text-4xl font-bold text-slate-900 text-center mb-12">
            {t.differentiators.title}
          </h2>

          <div className="bg-white rounded-2xl overflow-hidden border border-slate-200 shadow-xl">
            <div className="grid grid-cols-5 bg-gradient-to-r from-slate-100 to-slate-50 border-b border-slate-200">
              {t.differentiators.headers.map((header, index) => (
                <div
                  key={index}
                  className={`p-5 font-semibold ${index === 0 ? 'text-left' : 'text-center'} ${
                    index === 1 ? 'text-brand-600 bg-brand-50/50' : 'text-slate-600'
                  }`}
                >
                  {header}
                </div>
              ))}
            </div>
            {t.differentiators.rows.map((row, rowIndex) => (
              <div key={rowIndex} className="grid grid-cols-5 border-b border-slate-100 last:border-0 hover:bg-slate-50/50 transition">
                <div className="p-5 text-slate-700 font-medium">{row[0]}</div>
                {row.slice(1).map((value, colIndex) => (
                  <div key={colIndex} className={`p-5 flex justify-center items-center ${colIndex === 0 ? 'bg-brand-50/30' : ''}`}>
                    {renderCheckmark(value)}
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Contact Section */}
      <section id="contact" className="py-24 bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 relative overflow-hidden">
        <div className="absolute inset-0">
          <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-brand-500/10 rounded-full blur-3xl" />
          <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-indigo-500/10 rounded-full blur-3xl" />
        </div>
        <div className="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              {t.cta.title}
            </h2>
            <p className="text-xl text-slate-300">
              {t.cta.subtitle}
            </p>
          </div>
          <ContactForm lang={lang} />
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-950 py-16 border-t border-white/5">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-12 mb-12">
            {/* Brand */}
            <div className="md:col-span-2">
              <div className="flex items-center mb-4">
                <div className="w-10 h-10 bg-gradient-to-br from-brand-500 to-indigo-600 rounded-xl flex items-center justify-center mr-2">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                </div>
                <span className="text-xl font-bold text-white">Xcapit</span>
                <span className="text-xl font-light text-brand-400 ml-1">Privacy</span>
              </div>
              <p className="text-slate-400 max-w-md">
                {lang === 'es'
                  ? 'Plataforma de machine learning con cifrado homomórfico para colaboración segura entre instituciones financieras.'
                  : 'Homomorphic encryption machine learning platform for secure collaboration between financial institutions.'}
              </p>
            </div>

            {/* Links */}
            <div>
              <h4 className="text-white font-semibold mb-4">{t.footer.product}</h4>
              <ul className="space-y-2">
                <li><Link to="/hub" className="text-slate-400 hover:text-white transition">{t.footer.links.industries}</Link></li>
                <li><a href="#use-cases" className="text-slate-400 hover:text-white transition">{t.nav.casosUso}</a></li>
                <li><a href="#how-it-works" className="text-slate-400 hover:text-white transition">{t.nav.comoFunciona}</a></li>
              </ul>
            </div>

            <div>
              <h4 className="text-white font-semibold mb-4">{t.footer.contact}</h4>
              <ul className="space-y-2">
                <li><a href="mailto:consorcios@xcapit.com" className="text-slate-400 hover:text-white transition">consorcios@xcapit.com</a></li>
                <li><a href="https://github.com/xcapit" target="_blank" rel="noopener noreferrer" className="text-slate-400 hover:text-white transition">{t.footer.links.github}</a></li>
              </ul>
            </div>
          </div>

          <div className="pt-8 border-t border-white/5 text-center">
            <p className="text-slate-500 text-sm">{t.footer.rights}</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
