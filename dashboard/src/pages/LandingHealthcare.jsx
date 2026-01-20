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
      <div className="absolute top-0 -left-40 w-[500px] h-[500px] bg-emerald-500/20 rounded-full blur-[150px] animate-pulse" />
      <div className="absolute bottom-0 -right-40 w-[500px] h-[500px] bg-teal-500/20 rounded-full blur-[150px] animate-pulse" style={{ animationDelay: '1s' }} />

      {/* Floating particles */}
      {[...Array(15)].map((_, i) => (
        <div
          key={i}
          className="absolute w-1 h-1 bg-emerald-400/40 rounded-full"
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

// Hero illustration - Medical data collaboration visualization
function HeroIllustration() {
  return (
    <div className="relative w-full max-w-lg mx-auto">
      <svg viewBox="0 0 400 300" className="w-full h-auto">
        <defs>
          <linearGradient id="gradientEmerald" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#10b981" />
            <stop offset="100%" stopColor="#14b8a6" />
          </linearGradient>
          <linearGradient id="gradientTeal" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#14b8a6" />
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

        {/* Hospital nodes */}
        <g className="animate-pulse" style={{ animationDuration: '3s' }}>
          {/* Hospital A */}
          <rect x="20" y="40" width="80" height="55" rx="8" fill="#1e293b" stroke="url(#gradientEmerald)" strokeWidth="2" />
          <path d="M55 50 L55 60 M50 55 L60 55" stroke="white" strokeWidth="2" fill="none" />
          <text x="60" y="78" textAnchor="middle" fill="#94a3b8" fontSize="9" fontWeight="500">Hospital A</text>
          <rect x="30" y="85" width="60" height="4" rx="1" fill="#334155" />

          {/* Hospital B */}
          <rect x="20" y="125" width="80" height="55" rx="8" fill="#1e293b" stroke="url(#gradientEmerald)" strokeWidth="2" />
          <path d="M55 135 L55 145 M50 140 L60 140" stroke="white" strokeWidth="2" fill="none" />
          <text x="60" y="163" textAnchor="middle" fill="#94a3b8" fontSize="9" fontWeight="500">Hospital B</text>
          <rect x="30" y="170" width="60" height="4" rx="1" fill="#334155" />

          {/* Research Lab */}
          <rect x="20" y="210" width="80" height="55" rx="8" fill="#1e293b" stroke="url(#gradientEmerald)" strokeWidth="2" />
          <circle cx="55" cy="230" r="8" fill="none" stroke="white" strokeWidth="2" />
          <circle cx="55" cy="230" r="3" fill="white" />
          <text x="60" y="253" textAnchor="middle" fill="#94a3b8" fontSize="9" fontWeight="500">Research Lab</text>
        </g>

        {/* Connection lines with animation */}
        <path d="M100 67 Q140 67 160 120" stroke="url(#gradientEmerald)" strokeWidth="2" fill="none" strokeDasharray="5,5" opacity="0.6">
          <animate attributeName="stroke-dashoffset" from="0" to="-20" dur="2s" repeatCount="indefinite"/>
        </path>
        <path d="M100 152 L160 152" stroke="url(#gradientEmerald)" strokeWidth="2" fill="none" strokeDasharray="5,5" opacity="0.6">
          <animate attributeName="stroke-dashoffset" from="0" to="-20" dur="2s" repeatCount="indefinite"/>
        </path>
        <path d="M100 237 Q140 237 160 185" stroke="url(#gradientEmerald)" strokeWidth="2" fill="none" strokeDasharray="5,5" opacity="0.6">
          <animate attributeName="stroke-dashoffset" from="0" to="-20" dur="2s" repeatCount="indefinite"/>
        </path>

        {/* Central FHE Model */}
        <g filter="url(#glow)">
          <rect x="160" y="105" width="100" height="95" rx="12" fill="#1e293b" stroke="url(#gradientTeal)" strokeWidth="2"/>

          {/* DNA/Medical symbol */}
          <path d="M195 125 C195 130 205 130 205 125 C205 135 195 135 195 140 C195 145 205 145 205 140 C205 150 195 150 195 155"
                stroke="#10b981" strokeWidth="2" fill="none" strokeLinecap="round"/>
          <path d="M215 125 C215 130 225 130 225 125 C225 135 215 135 215 140 C215 145 225 145 225 140 C225 150 215 150 215 155"
                stroke="#14b8a6" strokeWidth="2" fill="none" strokeLinecap="round"/>

          {/* Lock overlay */}
          <path d="M210 165 L210 172 M203 177 L203 190 L217 190 L217 177 L203 177 M206 177 L206 172 C206 168 208 166 210 166 C212 166 214 168 214 172 L214 177"
                stroke="white" strokeWidth="1.5" fill="none" strokeLinecap="round"/>

          <text x="210" y="198" textAnchor="middle" fill="#10b981" fontSize="7" fontFamily="monospace">Encrypted ML</text>
        </g>

        {/* Output lines */}
        <path d="M260 125 Q290 125 310 95" stroke="url(#gradientTeal)" strokeWidth="2" fill="none" strokeDasharray="5,5" opacity="0.6">
          <animate attributeName="stroke-dashoffset" from="-20" to="0" dur="2s" repeatCount="indefinite"/>
        </path>
        <path d="M260 152 L310 152" stroke="url(#gradientTeal)" strokeWidth="2" fill="none" strokeDasharray="5,5" opacity="0.6">
          <animate attributeName="stroke-dashoffset" from="-20" to="0" dur="2s" repeatCount="indefinite"/>
        </path>
        <path d="M260 180 Q290 180 310 210" stroke="url(#gradientTeal)" strokeWidth="2" fill="none" strokeDasharray="5,5" opacity="0.6">
          <animate attributeName="stroke-dashoffset" from="-20" to="0" dur="2s" repeatCount="indefinite"/>
        </path>

        {/* Results */}
        <g className="animate-pulse" style={{ animationDuration: '2s', animationDelay: '1s' }}>
          <rect x="310" y="70" width="75" height="50" rx="8" fill="#1e293b" stroke="url(#gradientTeal)" strokeWidth="1.5" />
          <text x="347" y="88" textAnchor="middle" fill="#10b981" fontSize="8">Diagnosis</text>
          <text x="347" y="103" textAnchor="middle" fill="white" fontSize="10" fontWeight="bold">+35% Accuracy</text>

          <rect x="310" y="130" width="75" height="50" rx="8" fill="#1e293b" stroke="url(#gradientTeal)" strokeWidth="1.5" />
          <text x="347" y="148" textAnchor="middle" fill="#10b981" fontSize="8">Drug Discovery</text>
          <text x="347" y="163" textAnchor="middle" fill="white" fontSize="10" fontWeight="bold">-40% Time</text>

          <rect x="310" y="190" width="75" height="50" rx="8" fill="#1e293b" stroke="url(#gradientTeal)" strokeWidth="1.5" />
          <text x="347" y="208" textAnchor="middle" fill="#10b981" fontSize="8">Trials</text>
          <text x="347" y="223" textAnchor="middle" fill="white" fontSize="10" fontWeight="bold">Multi-Center</text>
        </g>

        {/* Floating particles */}
        <circle cx="135" cy="85" r="3" fill="#10b981" opacity="0.6">
          <animate attributeName="cx" values="135;155;135" dur="3s" repeatCount="indefinite"/>
        </circle>
        <circle cx="138" cy="152" r="2" fill="#14b8a6" opacity="0.6">
          <animate attributeName="cx" values="138;158;138" dur="2.5s" repeatCount="indefinite"/>
        </circle>
        <circle cx="135" cy="220" r="3" fill="#10b981" opacity="0.6">
          <animate attributeName="cx" values="135;155;135" dur="3.5s" repeatCount="indefinite"/>
        </circle>
      </svg>
    </div>
  )
}

// Stat card component with animated counter
function StatCard({ value, label, icon, delay = 0, isVisible = true }) {
  const numericValue = parseInt(String(value).replace(/[^0-9]/g, '')) || 0
  const prefix = value.startsWith('+') ? '+' : value.startsWith('-') ? '-' : ''
  const suffix = String(value).replace(/[0-9+-]/g, '')
  const count = useCounter(numericValue, 2000, isVisible)

  return (
    <div
      className="bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/10 hover:border-emerald-400/30 transition-all duration-500 hover:scale-105"
      style={{
        opacity: isVisible ? 1 : 0,
        transform: isVisible ? 'translateY(0)' : 'translateY(20px)',
        transition: `all 0.6s ease ${delay}ms`
      }}
    >
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 bg-gradient-to-br from-emerald-500/20 to-teal-500/20 rounded-xl flex items-center justify-center text-2xl">
          {icon}
        </div>
        <div>
          <div className="text-3xl font-bold text-white">{prefix}{count}{suffix}</div>
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
      title: 'Agendar Demo Healthcare',
      subtitle: 'Te mostramos cómo funciona con un caso real de diagnóstico colaborativo.',
      name: 'Nombre completo',
      email: 'Email corporativo',
      company: 'Organización',
      phone: 'Teléfono',
      position: 'Cargo',
      useCase: 'Caso de uso de interés',
      useCases: ['Diagnóstico colaborativo', 'Drug discovery', 'Ensayos clínicos', 'Otro'],
      submit: 'Agendar Demo',
      sending: 'Enviando...',
      success: 'Mensaje enviado. Te contactaremos pronto.',
      error: 'Error al enviar. Intenta de nuevo.',
      also: 'También puedes contactarnos en'
    },
    en: {
      title: 'Book Healthcare Demo',
      subtitle: 'We\'ll show you how it works with a real collaborative diagnosis case.',
      name: 'Full name',
      email: 'Corporate email',
      company: 'Organization',
      phone: 'Phone',
      position: 'Job title',
      useCase: 'Use case of interest',
      useCases: ['Collaborative diagnosis', 'Drug discovery', 'Clinical trials', 'Other'],
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
          subject: 'Demo Request - Healthcare - Xcapit Privacy',
          from_name: 'Xcapit Privacy',
          vertical: 'Healthcare',
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
            className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl focus:outline-none focus:border-emerald-400 focus:ring-2 focus:ring-emerald-400/20 text-white placeholder-slate-400 transition"
          />
          <input
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            placeholder={t.email}
            required
            className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl focus:outline-none focus:border-emerald-400 focus:ring-2 focus:ring-emerald-400/20 text-white placeholder-slate-400 transition"
          />
        </div>
        <div className="grid md:grid-cols-2 gap-4">
          <input
            type="text"
            value={formData.company}
            onChange={(e) => setFormData({ ...formData, company: e.target.value })}
            placeholder={t.company}
            required
            className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl focus:outline-none focus:border-emerald-400 focus:ring-2 focus:ring-emerald-400/20 text-white placeholder-slate-400 transition"
          />
          <input
            type="tel"
            value={formData.phone}
            onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
            placeholder={t.phone}
            className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl focus:outline-none focus:border-emerald-400 focus:ring-2 focus:ring-emerald-400/20 text-white placeholder-slate-400 transition"
          />
        </div>
        <input
          type="text"
          value={formData.job_title}
          onChange={(e) => setFormData({ ...formData, job_title: e.target.value })}
          placeholder={t.position}
          required
          className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl focus:outline-none focus:border-emerald-400 focus:ring-2 focus:ring-emerald-400/20 text-white placeholder-slate-400 transition"
        />
        <select
          value={formData.use_case}
          onChange={(e) => setFormData({ ...formData, use_case: e.target.value })}
          required
          className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl focus:outline-none focus:border-emerald-400 focus:ring-2 focus:ring-emerald-400/20 text-white placeholder-slate-400 transition appearance-none cursor-pointer"
        >
          <option value="" className="bg-slate-800">{t.useCase}</option>
          {t.useCases.map(uc => (
            <option key={uc} value={uc} className="bg-slate-800">{uc}</option>
          ))}
        </select>

        <button
          type="submit"
          disabled={status === 'sending'}
          className="w-full bg-gradient-to-r from-emerald-500 to-teal-500 text-white py-4 px-6 rounded-xl font-semibold hover:from-emerald-600 hover:to-teal-600 transition disabled:opacity-50 shadow-lg shadow-emerald-500/25"
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
        <a href="mailto:consorcios@xcapit.com" className="text-emerald-400 font-medium hover:underline">
          consorcios@xcapit.com
        </a>
      </p>
    </div>
  )
}

// Use Case Card Component with animation support
function UseCaseCard({ title, problem, solution, metric, icon, lang, delay = 0, isVisible = true }) {
  return (
    <div
      className="group bg-white rounded-2xl p-8 border border-slate-200 hover:shadow-2xl hover:shadow-emerald-500/10 hover:-translate-y-1 transition-all duration-300"
      style={{
        opacity: isVisible ? 1 : 0,
        transform: isVisible ? 'translateY(0)' : 'translateY(30px)',
        transition: `all 0.6s ease ${delay}ms`
      }}
    >
      <div className="w-14 h-14 bg-gradient-to-br from-emerald-500/10 to-teal-500/10 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
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
        <span className="text-3xl font-bold bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent">
          {metric}
        </span>
      </div>
    </div>
  )
}

// Compliance badge component with animation
function ComplianceBadge({ name, icon, delay = 0, isVisible = true }) {
  return (
    <div
      className="flex items-center gap-2 bg-emerald-50 border border-emerald-200 px-5 py-2.5 rounded-full hover:scale-110 transition-all duration-300"
      style={{
        opacity: isVisible ? 1 : 0,
        transform: isVisible ? 'translateY(0) scale(1)' : 'translateY(15px) scale(0.9)',
        transition: `all 0.5s ease ${delay}ms`
      }}
    >
      {icon}
      <span className="font-semibold text-emerald-800">{name}</span>
    </div>
  )
}

// Step component for how it works with animation
function StepCard({ number, title, description, delay = 0, isVisible = true, showConnector = false }) {
  return (
    <div
      className="relative group"
      style={{
        opacity: isVisible ? 1 : 0,
        transform: isVisible ? 'translateY(0)' : 'translateY(30px)',
        transition: `all 0.6s ease ${delay}ms`
      }}
    >
      {/* Connection line */}
      {showConnector && (
        <div className="hidden md:block absolute top-14 -right-4 w-8 h-0.5 bg-gradient-to-r from-emerald-500 to-teal-500 z-10" />
      )}
      <div className="absolute -inset-0.5 bg-gradient-to-r from-emerald-500 to-teal-500 rounded-2xl blur opacity-0 group-hover:opacity-30 transition duration-500" />
      <div className="relative bg-white rounded-2xl p-8 border border-slate-200 h-full">
        <div className="w-12 h-12 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-xl flex items-center justify-center text-white font-bold text-lg mb-4 group-hover:scale-110 transition-transform">
          {number}
        </div>
        <h3 className="text-xl font-bold text-slate-900 mb-2">{title}</h3>
        <p className="text-slate-600">{description}</p>
      </div>
    </div>
  )
}

// Differentiator row component with animation
function DifferentiatorRow({ option, problem, xcapit, delay = 0, isVisible = true }) {
  return (
    <div
      className="bg-white rounded-xl p-6 border border-slate-200 hover:shadow-lg hover:border-emerald-200 transition-all duration-300"
      style={{
        opacity: isVisible ? 1 : 0,
        transform: isVisible ? 'translateX(0)' : 'translateX(-20px)',
        transition: `all 0.5s ease ${delay}ms`
      }}
    >
      <div className="grid md:grid-cols-3 gap-4 items-start">
        <div className="font-semibold text-slate-900">{option}</div>
        <div className="flex items-start gap-2">
          <div className="w-6 h-6 bg-red-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
            <svg className="w-4 h-4 text-red-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </div>
          <span className="text-slate-600">{problem}</span>
        </div>
        <div className="flex items-start gap-2">
          <div className="w-6 h-6 bg-emerald-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
            <svg className="w-4 h-4 text-emerald-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          </div>
          <span className="text-emerald-700 font-medium">{xcapit}</span>
        </div>
      </div>
    </div>
  )
}

export default function LandingHealthcare() {
  const { i18n } = useTranslation()
  const lang = i18n.language?.startsWith('es') ? 'es' : 'en'
  const [scrolled, setScrolled] = useState(false)

  // Scroll animation refs for each section
  const [heroRef, heroVisible] = useScrollAnimation(0.1)
  const [problemRef, problemVisible] = useScrollAnimation(0.2)
  const [solutionRef, solutionVisible] = useScrollAnimation(0.2)
  const [useCasesRef, useCasesVisible] = useScrollAnimation(0.15)
  const [complianceRef, complianceVisible] = useScrollAnimation(0.2)
  const [diffRef, diffVisible] = useScrollAnimation(0.2)
  const [contactRef, contactVisible] = useScrollAnimation(0.2)

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
        compliance: 'Compliance',
        demo: 'Demo'
      },
      hero: {
        badge: 'Healthcare & Life Sciences',
        headline: 'Investigación médica colaborativa',
        highlight: 'sin exponer un solo paciente.',
        subheadline: 'Hospitales y farmacéuticas pueden entrenar modelos de diagnóstico con datos de millones de pacientes. Sin violar HIPAA. Sin compartir historiales. Con cifrado homomórfico.',
        cta: 'Agendar Demo',
        ctaSecondary: 'Ver cómo funciona',
        stats: {
          accuracy: { value: '+35%', label: 'Precisión diagnóstica' },
          time: { value: '-40%', label: 'Tiempo discovery' },
          compliance: { value: '100%', label: 'HIPAA Compliant' }
        }
      },
      trustedBy: {
        title: 'Tecnología validada por instituciones líderes',
        partners: ['Microsoft SEAL', 'OpenFHE', 'HElib', 'PALISADE']
      },
      problem: {
        title: 'Los mejores diagnósticos requieren datos que nunca vas a tener',
        points: [
          {
            title: 'El dilema de la privacidad',
            desc: 'Cada hospital tiene datos únicos de pacientes. Un modelo entrenado con datos de 100 hospitales sería 10x más preciso. Pero HIPAA y ética médica hacen imposible compartirlos.',
            icon: '🔒'
          },
          {
            title: 'Enfermedades raras = datos insuficientes',
            desc: 'Para enfermedades raras, ningún hospital tiene suficientes casos para entrenar modelos confiables. Los casos existen, dispersos en miles de instituciones.',
            icon: '🧬'
          },
          {
            title: 'Drug discovery lento y costoso',
            desc: 'Desarrollar un medicamento toma 10+ años y $2B. La mayor parte del tiempo se pierde en conseguir datos clínicos suficientes.',
            icon: '💊'
          }
        ]
      },
      solution: {
        title: 'Colaboración médica sin exponer pacientes',
        desc: 'Con cifrado homomórfico, los datos de pacientes nunca salen de cada hospital. Solo versiones cifradas que permiten entrenar modelos compartidos. Nadie puede reconstruir historiales.',
        steps: [
          { title: 'Cifrado en el hospital', desc: 'Los datos de pacientes se cifran localmente. El historial nunca sale.' },
          { title: 'Entrenamiento federado', desc: 'El modelo se entrena sobre datos cifrados de múltiples hospitales.' },
          { title: 'Diagnósticos mejorados', desc: 'Cada hospital recibe un modelo mejor sin haber expuesto datos.' }
        ]
      },
      useCases: {
        title: 'Casos de Uso',
        subtitle: 'Soluciones específicas para el sector salud',
        cases: [
          {
            title: 'Diagnóstico Asistido por IA',
            problem: 'Tu hospital ha visto 1,000 casos de cierta condición. Otros hospitales han visto 100,000. El modelo que podrías entrenar con esos datos sería dramáticamente mejor.',
            solution: 'Entrena modelos de diagnóstico con datos de toda una red hospitalaria sin que ningún paciente sea identificable.',
            metric: '+35% precisión'
          },
          {
            title: 'Drug Discovery Acelerado',
            problem: 'Identificar candidatos para un nuevo medicamento requiere analizar respuestas de miles de pacientes a tratamientos similares. Esos datos están en silos.',
            solution: 'Análisis de eficacia y efectos secundarios sobre datos clínicos cifrados de múltiples estudios.',
            metric: '-40% tiempo'
          },
          {
            title: 'Ensayos Clínicos Multi-Centro',
            problem: 'Un ensayo clínico multi-centro requiere que cada hospital comparta datos de pacientes con el sponsor. Esto genera fricción y riesgos legales.',
            solution: 'Cada centro mantiene sus datos locales. El análisis se hace sobre datos cifrados. El sponsor nunca ve datos crudos.',
            metric: '-60% fricción'
          }
        ]
      },
      compliance: {
        title: 'HIPAA sin compromisos. Ética médica intacta.',
        desc: 'El cifrado homomórfico elimina el debate ético sobre compartir datos de pacientes. No estás compartiendo datos - estás compartiendo versiones cifradas que nadie puede descifrar.',
        badges: ['HIPAA', 'GDPR', '21 CFR Part 11', 'IRB Ready', 'ANVISA']
      },
      differentiators: {
        title: '¿Por qué no usar otras soluciones?',
        subtitle: 'Comparativa con alternativas tradicionales',
        items: [
          { option: 'Data Clean Rooms', problem: 'Datos aún se centralizan en un tercero', xcapit: 'Datos nunca salen del hospital' },
          { option: 'Federated Learning tradicional', problem: 'Modelo viaja, puede extraerse información', xcapit: 'Solo datos cifrados viajan' },
          { option: 'Anonimización', problem: 'Re-identificación posible con datos genómicos', xcapit: 'Imposible reconstruir datos originales' },
          { option: 'Synthetic Data', problem: 'Pierde patrones importantes de enfermedades raras', xcapit: 'Preserva todos los patrones' }
        ]
      },
      cta: {
        title: '¿Listo para investigación médica sin barreras de privacidad?',
        subtitle: 'Agenda una demo con nuestro equipo especializado en healthcare.'
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
        compliance: 'Compliance',
        demo: 'Demo'
      },
      hero: {
        badge: 'Healthcare & Life Sciences',
        headline: 'Collaborative medical research',
        highlight: 'without exposing a single patient.',
        subheadline: 'Hospitals and pharma can train diagnostic models on millions of patients\' data. Without violating HIPAA. Without sharing records. With homomorphic encryption.',
        cta: 'Book Demo',
        ctaSecondary: 'See how it works',
        stats: {
          accuracy: { value: '+35%', label: 'Diagnostic accuracy' },
          time: { value: '-40%', label: 'Discovery time' },
          compliance: { value: '100%', label: 'HIPAA Compliant' }
        }
      },
      trustedBy: {
        title: 'Technology validated by leading institutions',
        partners: ['Microsoft SEAL', 'OpenFHE', 'HElib', 'PALISADE']
      },
      problem: {
        title: 'The best diagnoses require data you\'ll never have',
        points: [
          {
            title: 'The privacy dilemma',
            desc: 'Every hospital has unique patient data. A model trained on data from 100 hospitals would be 10x more accurate. But HIPAA and medical ethics make sharing impossible.',
            icon: '🔒'
          },
          {
            title: 'Rare diseases = insufficient data',
            desc: 'For rare diseases, no single hospital has enough cases to train reliable models. The cases exist, scattered across thousands of institutions.',
            icon: '🧬'
          },
          {
            title: 'Slow and expensive drug discovery',
            desc: 'Developing a drug takes 10+ years and $2B. Most time is lost getting enough clinical data.',
            icon: '💊'
          }
        ]
      },
      solution: {
        title: 'Medical collaboration without exposing patients',
        desc: 'With homomorphic encryption, patient data never leaves each hospital. Only encrypted versions that enable shared model training. No one can reconstruct records.',
        steps: [
          { title: 'Encryption at hospital', desc: 'Patient data is encrypted locally. Records never leave.' },
          { title: 'Federated training', desc: 'Model trains on encrypted data from multiple hospitals.' },
          { title: 'Better diagnoses', desc: 'Each hospital gets a better model without exposing data.' }
        ]
      },
      useCases: {
        title: 'Use Cases',
        subtitle: 'Specific solutions for the healthcare sector',
        cases: [
          {
            title: 'AI-Assisted Diagnosis',
            problem: 'Your hospital has seen 1,000 cases of a condition. Other hospitals have seen 100,000. The model you could train on that data would be dramatically better.',
            solution: 'Train diagnostic models with data from an entire hospital network without any patient being identifiable.',
            metric: '+35% accuracy'
          },
          {
            title: 'Accelerated Drug Discovery',
            problem: 'Identifying candidates for a new drug requires analyzing thousands of patients\' responses to similar treatments. That data is siloed.',
            solution: 'Efficacy and side effect analysis on encrypted clinical data from multiple studies.',
            metric: '-40% time'
          },
          {
            title: 'Multi-Center Clinical Trials',
            problem: 'A multi-center clinical trial requires each hospital to share patient data with the sponsor. This creates friction and legal risks.',
            solution: 'Each center keeps its data local. Analysis runs on encrypted data. The sponsor never sees raw data.',
            metric: '-60% friction'
          }
        ]
      },
      compliance: {
        title: 'HIPAA without compromise. Medical ethics intact.',
        desc: 'Homomorphic encryption eliminates the ethical debate about sharing patient data. You\'re not sharing data - you\'re sharing encrypted versions no one can decrypt.',
        badges: ['HIPAA', 'GDPR', '21 CFR Part 11', 'IRB Ready', 'ANVISA']
      },
      differentiators: {
        title: 'Why not use other solutions?',
        subtitle: 'Comparison with traditional alternatives',
        items: [
          { option: 'Data Clean Rooms', problem: 'Data still centralizes with a third party', xcapit: 'Data never leaves the hospital' },
          { option: 'Traditional Federated Learning', problem: 'Model travels, information can be extracted', xcapit: 'Only encrypted data travels' },
          { option: 'Anonymization', problem: 'Re-identification possible with genomic data', xcapit: 'Impossible to reconstruct original data' },
          { option: 'Synthetic Data', problem: 'Loses important patterns for rare diseases', xcapit: 'Preserves all patterns' }
        ]
      },
      cta: {
        title: 'Ready for medical research without privacy barriers?',
        subtitle: 'Book a demo with our healthcare-specialized team.'
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
    <svg key="diagnosis" className="w-7 h-7 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
    </svg>,
    <svg key="drug" className="w-7 h-7 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
    </svg>,
    <svg key="trials" className="w-7 h-7 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
    </svg>
  ]

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Navigation */}
      <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled ? 'bg-slate-900/95 backdrop-blur-md shadow-lg' : 'bg-transparent'
      }`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link to="/hub" className="flex items-center group">
              <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl flex items-center justify-center mr-2 group-hover:scale-105 transition-transform">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <span className="text-xl font-bold text-white">Xcapit</span>
              <span className="text-xl font-light text-emerald-400 ml-1">Privacy</span>
            </Link>
            <div className="hidden md:flex items-center gap-6">
              <a href="#use-cases" className="text-slate-300 hover:text-white font-medium transition">{t.nav.casosUso}</a>
              <a href="#how-it-works" className="text-slate-300 hover:text-white font-medium transition">{t.nav.comoFunciona}</a>
              <a href="#compliance" className="text-slate-300 hover:text-white font-medium transition">{t.nav.compliance}</a>
            </div>
            <div className="flex items-center gap-3">
              <LanguageSwitcher variant="toggle" />
              <a href="#contact" className="bg-gradient-to-r from-emerald-500 to-teal-600 text-white px-5 py-2.5 rounded-lg font-medium hover:from-emerald-600 hover:to-teal-700 transition shadow-lg shadow-emerald-500/25">
                {t.hero.cta}
              </a>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center pt-16 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950" />
        <div className="absolute inset-0">
          <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-emerald-500/10 rounded-full blur-3xl" />
          <div className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] bg-teal-500/10 rounded-full blur-3xl" />
        </div>
        <ParticleBackground />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <div className="inline-flex items-center gap-2 bg-white/5 backdrop-blur-sm px-4 py-2 rounded-full mb-8 border border-white/10">
                <span className="text-2xl">🏥</span>
                <span className="text-white/90 text-sm font-medium">{t.hero.badge}</span>
              </div>

              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-6 leading-tight">
                {t.hero.headline}
                <br />
                <span className="bg-gradient-to-r from-emerald-400 via-teal-400 to-cyan-400 bg-clip-text text-transparent">
                  {t.hero.highlight}
                </span>
              </h1>

              <p className="text-lg lg:text-xl text-slate-300 mb-8 max-w-xl leading-relaxed">
                {t.hero.subheadline}
              </p>

              <div className="flex flex-col sm:flex-row gap-4 mb-12">
                <a
                  href="#contact"
                  className="inline-flex items-center justify-center gap-3 bg-gradient-to-r from-emerald-500 to-teal-600 text-white px-8 py-4 rounded-xl font-semibold hover:from-emerald-600 hover:to-teal-700 transition text-lg shadow-2xl shadow-emerald-500/25"
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
              <div ref={heroRef} className="grid grid-cols-3 gap-4">
                <StatCard
                  value={t.hero.stats.accuracy.value}
                  label={t.hero.stats.accuracy.label}
                  icon="🎯"
                  delay={0}
                  isVisible={heroVisible}
                />
                <StatCard
                  value={t.hero.stats.time.value}
                  label={t.hero.stats.time.label}
                  icon="⚡"
                  delay={150}
                  isVisible={heroVisible}
                />
                <StatCard
                  value={t.hero.stats.compliance.value}
                  label={t.hero.stats.compliance.label}
                  icon="✓"
                  delay={300}
                  isVisible={heroVisible}
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
      <section ref={problemRef} className="py-24 bg-slate-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div
            className="text-center mb-16"
            style={{
              opacity: problemVisible ? 1 : 0,
              transform: problemVisible ? 'translateY(0)' : 'translateY(20px)',
              transition: 'all 0.6s ease'
            }}
          >
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              {t.problem.title}
            </h2>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {t.problem.points.map((point, index) => (
              <div
                key={index}
                className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-8 border border-slate-700 hover:border-red-500/30 hover:scale-105 transition-all duration-300"
                style={{
                  opacity: problemVisible ? 1 : 0,
                  transform: problemVisible ? 'translateY(0)' : 'translateY(30px)',
                  transition: `all 0.6s ease ${150 + index * 150}ms`
                }}
              >
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
      <section ref={solutionRef} id="how-it-works" className="py-24 bg-slate-950">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div
            className="text-center mb-16"
            style={{
              opacity: solutionVisible ? 1 : 0,
              transform: solutionVisible ? 'translateY(0)' : 'translateY(20px)',
              transition: 'all 0.6s ease'
            }}
          >
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
                delay={index * 200}
                isVisible={solutionVisible}
                showConnector={index < t.solution.steps.length - 1}
              />
            ))}
          </div>
        </div>
      </section>

      {/* Use Cases Section */}
      <section ref={useCasesRef} id="use-cases" className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div
            className="text-center mb-16"
            style={{
              opacity: useCasesVisible ? 1 : 0,
              transform: useCasesVisible ? 'translateY(0)' : 'translateY(20px)',
              transition: 'all 0.6s ease'
            }}
          >
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
                delay={index * 150}
                isVisible={useCasesVisible}
              />
            ))}
          </div>
        </div>
      </section>

      {/* Compliance Section */}
      <section ref={complianceRef} id="compliance" className="py-24 bg-slate-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div
            className="text-center mb-12"
            style={{
              opacity: complianceVisible ? 1 : 0,
              transform: complianceVisible ? 'translateY(0)' : 'translateY(20px)',
              transition: 'all 0.6s ease'
            }}
          >
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
                delay={index * 100}
                isVisible={complianceVisible}
              />
            ))}
          </div>
        </div>
      </section>

      {/* Differentiators Section */}
      <section ref={diffRef} className="py-24 bg-white">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div
            className="text-center mb-12"
            style={{
              opacity: diffVisible ? 1 : 0,
              transform: diffVisible ? 'translateY(0)' : 'translateY(20px)',
              transition: 'all 0.6s ease'
            }}
          >
            <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4">
              {t.differentiators.title}
            </h2>
            <p className="text-xl text-slate-600">{t.differentiators.subtitle}</p>
          </div>

          <div className="space-y-4">
            {t.differentiators.items.map((item, index) => (
              <DifferentiatorRow
                key={index}
                option={item.option}
                problem={item.problem}
                xcapit={item.xcapit}
                delay={index * 100}
                isVisible={diffVisible}
              />
            ))}
          </div>
        </div>
      </section>

      {/* Contact Section */}
      <section ref={contactRef} id="contact" className="py-24 bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950 relative overflow-hidden">
        <div className="absolute inset-0">
          <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-emerald-500/10 rounded-full blur-3xl" />
          <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-teal-500/10 rounded-full blur-3xl" />
        </div>
        <div className="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div
            className="text-center mb-12"
            style={{
              opacity: contactVisible ? 1 : 0,
              transform: contactVisible ? 'translateY(0)' : 'translateY(20px)',
              transition: 'all 0.6s ease'
            }}
          >
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              {t.cta.title}
            </h2>
            <p className="text-xl text-slate-300">
              {t.cta.subtitle}
            </p>
          </div>
          <div
            style={{
              opacity: contactVisible ? 1 : 0,
              transform: contactVisible ? 'translateY(0)' : 'translateY(30px)',
              transition: 'all 0.6s ease 200ms'
            }}
          >
            <ContactForm lang={lang} />
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-950 py-16 border-t border-white/5">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-12 mb-12">
            {/* Brand */}
            <div className="md:col-span-2">
              <div className="flex items-center mb-4">
                <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl flex items-center justify-center mr-2">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                </div>
                <span className="text-xl font-bold text-white">Xcapit</span>
                <span className="text-xl font-light text-emerald-400 ml-1">Privacy</span>
              </div>
              <p className="text-slate-400 max-w-md">
                {lang === 'es'
                  ? 'Plataforma de machine learning con cifrado homomórfico para investigación médica colaborativa sin exponer datos de pacientes.'
                  : 'Homomorphic encryption machine learning platform for collaborative medical research without exposing patient data.'}
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
