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

    if (ref.current) {
      observer.observe(ref.current)
    }

    return () => observer.disconnect()
  }, [threshold])

  return [ref, isVisible]
}

// Animated counter hook
function useCounter(end, duration = 2000, startOnVisible = false, isVisible = true) {
  const [count, setCount] = useState(0)
  const [hasStarted, setHasStarted] = useState(false)

  useEffect(() => {
    if (startOnVisible && !isVisible) return
    if (hasStarted) return

    setHasStarted(true)
    let startTime = null
    const animate = (timestamp) => {
      if (!startTime) startTime = timestamp
      const progress = Math.min((timestamp - startTime) / duration, 1)
      setCount(Math.floor(progress * end))
      if (progress < 1) {
        requestAnimationFrame(animate)
      }
    }
    requestAnimationFrame(animate)
  }, [end, duration, startOnVisible, isVisible, hasStarted])

  return count
}

// Typing effect component
function TypeWriter({ text, speed = 80, delay = 0 }) {
  const [displayText, setDisplayText] = useState('')
  const [showCursor, setShowCursor] = useState(true)

  useEffect(() => {
    let timeout
    const startTyping = () => {
      let i = 0
      const type = () => {
        if (i < text.length) {
          setDisplayText(text.slice(0, i + 1))
          i++
          timeout = setTimeout(type, speed)
        } else {
          setTimeout(() => setShowCursor(false), 1000)
        }
      }
      type()
    }

    const delayTimeout = setTimeout(startTyping, delay)
    return () => {
      clearTimeout(timeout)
      clearTimeout(delayTimeout)
    }
  }, [text, speed, delay])

  return (
    <span>
      {displayText}
      {showCursor && <span className="animate-pulse">|</span>}
    </span>
  )
}

// Animated background with floating particles
function ParticleBackground() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      <div className="absolute top-0 -left-40 w-[500px] h-[500px] bg-brand-500/20 rounded-full blur-[150px] animate-pulse" />
      <div className="absolute bottom-0 -right-40 w-[500px] h-[500px] bg-indigo-500/20 rounded-full blur-[150px] animate-pulse" style={{ animationDelay: '1s' }} />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-purple-500/5 rounded-full blur-[200px]" />

      {/* Floating particles */}
      {[...Array(20)].map((_, i) => (
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

      {/* Grid pattern */}
      <svg className="absolute inset-0 w-full h-full opacity-[0.02]" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <pattern id="grid" width="60" height="60" patternUnits="userSpaceOnUse">
            <path d="M 60 0 L 0 0 0 60" fill="none" stroke="white" strokeWidth="1"/>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />
      </svg>

      <style>{`
        @keyframes float {
          0%, 100% { transform: translateY(0) translateX(0); opacity: 0.4; }
          50% { transform: translateY(-20px) translateX(10px); opacity: 0.8; }
        }
      `}</style>
    </div>
  )
}

// Hero Illustration - Encryption Flow Diagram
function HeroIllustration() {
  return (
    <div className="relative w-full max-w-lg mx-auto">
      <svg viewBox="0 0 400 300" className="w-full h-auto">
        {/* Background glow */}
        <defs>
          <linearGradient id="gradientBlue" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.8"/>
            <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0.8"/>
          </linearGradient>
          <linearGradient id="gradientGreen" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#10b981" stopOpacity="0.8"/>
            <stop offset="100%" stopColor="#06b6d4" stopOpacity="0.8"/>
          </linearGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
            <feMerge>
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>

        {/* Connection lines */}
        <path d="M80 150 Q150 100 200 150" stroke="url(#gradientBlue)" strokeWidth="2" fill="none" strokeDasharray="5,5" opacity="0.5">
          <animate attributeName="stroke-dashoffset" from="0" to="-20" dur="2s" repeatCount="indefinite"/>
        </path>
        <path d="M320 150 Q250 100 200 150" stroke="url(#gradientGreen)" strokeWidth="2" fill="none" strokeDasharray="5,5" opacity="0.5">
          <animate attributeName="stroke-dashoffset" from="0" to="-20" dur="2s" repeatCount="indefinite"/>
        </path>
        <path d="M80 150 Q150 200 200 150" stroke="url(#gradientBlue)" strokeWidth="2" fill="none" strokeDasharray="5,5" opacity="0.5">
          <animate attributeName="stroke-dashoffset" from="0" to="-20" dur="2s" repeatCount="indefinite"/>
        </path>
        <path d="M320 150 Q250 200 200 150" stroke="url(#gradientGreen)" strokeWidth="2" fill="none" strokeDasharray="5,5" opacity="0.5">
          <animate attributeName="stroke-dashoffset" from="0" to="-20" dur="2s" repeatCount="indefinite"/>
        </path>

        {/* Left nodes - Organizations */}
        <g filter="url(#glow)">
          <circle cx="60" cy="80" r="25" fill="#1e293b" stroke="url(#gradientBlue)" strokeWidth="2"/>
          <text x="60" y="85" textAnchor="middle" fill="white" fontSize="12" fontWeight="bold">A</text>
        </g>
        <g filter="url(#glow)">
          <circle cx="60" cy="150" r="25" fill="#1e293b" stroke="url(#gradientBlue)" strokeWidth="2"/>
          <text x="60" y="155" textAnchor="middle" fill="white" fontSize="12" fontWeight="bold">B</text>
        </g>
        <g filter="url(#glow)">
          <circle cx="60" cy="220" r="25" fill="#1e293b" stroke="url(#gradientBlue)" strokeWidth="2"/>
          <text x="60" y="225" textAnchor="middle" fill="white" fontSize="12" fontWeight="bold">C</text>
        </g>

        {/* Right nodes - Organizations */}
        <g filter="url(#glow)">
          <circle cx="340" cy="80" r="25" fill="#1e293b" stroke="url(#gradientGreen)" strokeWidth="2"/>
          <text x="340" y="85" textAnchor="middle" fill="white" fontSize="12" fontWeight="bold">D</text>
        </g>
        <g filter="url(#glow)">
          <circle cx="340" cy="150" r="25" fill="#1e293b" stroke="url(#gradientGreen)" strokeWidth="2"/>
          <text x="340" y="155" textAnchor="middle" fill="white" fontSize="12" fontWeight="bold">E</text>
        </g>
        <g filter="url(#glow)">
          <circle cx="340" cy="220" r="25" fill="#1e293b" stroke="url(#gradientGreen)" strokeWidth="2"/>
          <text x="340" y="225" textAnchor="middle" fill="white" fontSize="12" fontWeight="bold">F</text>
        </g>

        {/* Center - Encrypted Model */}
        <g filter="url(#glow)">
          <rect x="160" y="110" width="80" height="80" rx="12" fill="#1e293b" stroke="url(#gradientBlue)" strokeWidth="2"/>
          <path d="M200 125 L200 135 M190 145 L210 145 L210 165 L190 165 Z M195 165 L195 175 M205 165 L205 175" stroke="white" strokeWidth="2" fill="none"/>
        </g>

        {/* Labels */}
        <text x="60" y="260" textAnchor="middle" fill="#64748b" fontSize="10">Encrypted Data</text>
        <text x="200" y="260" textAnchor="middle" fill="#64748b" fontSize="10">Shared Model</text>
        <text x="340" y="260" textAnchor="middle" fill="#64748b" fontSize="10">Encrypted Data</text>

        {/* Floating particles */}
        <circle cx="120" cy="100" r="3" fill="#3b82f6" opacity="0.6">
          <animate attributeName="cy" values="100;90;100" dur="3s" repeatCount="indefinite"/>
        </circle>
        <circle cx="280" cy="120" r="3" fill="#10b981" opacity="0.6">
          <animate attributeName="cy" values="120;130;120" dur="2.5s" repeatCount="indefinite"/>
        </circle>
        <circle cx="150" cy="200" r="2" fill="#8b5cf6" opacity="0.6">
          <animate attributeName="cy" values="200;210;200" dur="2s" repeatCount="indefinite"/>
        </circle>
      </svg>
    </div>
  )
}

// Icons
const icons = {
  finance: (
    <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18V10.5zm-12 0h.008v.008H6V10.5z" />
    </svg>
  ),
  healthcare: (
    <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z" />
    </svg>
  ),
  government: (
    <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 21v-8.25M15.75 21v-8.25M8.25 21v-8.25M3 9l9-6 9 6m-1.5 12V10.332A48.36 48.36 0 0012 9.75c-2.551 0-5.056.2-7.5.582V21M3 21h18M12 6.75h.008v.008H12V6.75z" />
    </svg>
  ),
  lock: (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
    </svg>
  ),
  shield: (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
    </svg>
  ),
  cube: (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M21 7.5l-9-5.25L3 7.5m18 0l-9 5.25m9-5.25v9l-9 5.25M3 7.5l9 5.25M3 7.5v9l9 5.25m0-9v9" />
    </svg>
  ),
  eye: (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
    </svg>
  ),
  check: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
    </svg>
  ),
  arrow: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 8.25L21 12m0 0l-3.75 3.75M21 12H3" />
    </svg>
  )
}

// Certification Badge
function CertBadge({ name, icon }) {
  return (
    <div className="flex items-center gap-2 bg-white/5 backdrop-blur-sm border border-white/10 rounded-lg px-4 py-2">
      <span className="text-emerald-400">{icon}</span>
      <span className="text-white/80 text-sm font-medium">{name}</span>
    </div>
  )
}

// Company Logo Placeholder
function CompanyLogo({ name }) {
  return (
    <div className="flex items-center justify-center h-8 px-4 opacity-40 hover:opacity-70 transition-opacity">
      <span className="text-white font-bold text-lg tracking-wider">{name}</span>
    </div>
  )
}

// Industry Card with 3D tilt effect and scroll animation
function IndustryCard({ icon, title, description, examples, link, color, ctaText = 'Ver soluciones', delay = 0, isVisible = true }) {
  const [transform, setTransform] = useState('')
  const [glare, setGlare] = useState({ x: 50, y: 50 })

  const handleMouseMove = (e) => {
    const card = e.currentTarget
    const rect = card.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    const centerX = rect.width / 2
    const centerY = rect.height / 2
    const rotateX = (y - centerY) / 20
    const rotateY = (centerX - x) / 20

    setTransform(`perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.02, 1.02, 1.02)`)
    setGlare({ x: (x / rect.width) * 100, y: (y / rect.height) * 100 })
  }

  const handleMouseLeave = () => {
    setTransform('')
    setGlare({ x: 50, y: 50 })
  }

  const colorClasses = {
    brand: {
      bg: 'bg-gradient-to-br from-brand-500/10 to-brand-600/5',
      border: 'border-brand-500/20 hover:border-brand-400/50',
      icon: 'bg-gradient-to-br from-brand-500 to-brand-600 text-white shadow-lg shadow-brand-500/30',
      badge: 'bg-brand-500/10 text-brand-300 border-brand-500/20',
      cta: 'text-brand-400 group-hover:text-brand-300',
      glare: 'from-brand-400/20'
    },
    emerald: {
      bg: 'bg-gradient-to-br from-emerald-500/10 to-emerald-600/5',
      border: 'border-emerald-500/20 hover:border-emerald-400/50',
      icon: 'bg-gradient-to-br from-emerald-500 to-emerald-600 text-white shadow-lg shadow-emerald-500/30',
      badge: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20',
      cta: 'text-emerald-400 group-hover:text-emerald-300',
      glare: 'from-emerald-400/20'
    },
    slate: {
      bg: 'bg-gradient-to-br from-slate-400/10 to-slate-500/5',
      border: 'border-slate-400/20 hover:border-slate-300/50',
      icon: 'bg-gradient-to-br from-slate-500 to-slate-600 text-white shadow-lg shadow-slate-500/30',
      badge: 'bg-slate-500/10 text-slate-300 border-slate-500/20',
      cta: 'text-slate-300 group-hover:text-white',
      glare: 'from-slate-400/20'
    }
  }

  const colors = colorClasses[color]

  return (
    <Link
      to={link}
      className={`group relative backdrop-blur-xl rounded-2xl p-6 lg:p-8 border transition-all duration-300 hover:shadow-2xl focus:outline-none focus:ring-2 focus:ring-white/20 ${colors.bg} ${colors.border}`}
      style={{
        transform: isVisible ? transform : 'translateY(30px)',
        transformStyle: 'preserve-3d',
        opacity: isVisible ? 1 : 0,
        transition: `opacity 0.6s ease ${delay}ms, transform 0.6s ease ${delay}ms`
      }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      {/* Glare effect */}
      <div
        className={`absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none bg-gradient-radial ${colors.glare} to-transparent`}
        style={{
          background: `radial-gradient(circle at ${glare.x}% ${glare.y}%, rgba(255,255,255,0.1) 0%, transparent 50%)`
        }}
      />

      <div className="relative" style={{ transform: 'translateZ(20px)' }}>
        <div className={`w-14 h-14 rounded-xl flex items-center justify-center mb-5 transition-transform duration-300 group-hover:scale-110 ${colors.icon}`}>
          {icon}
        </div>
        <h3 className="text-xl font-bold text-white mb-2">{title}</h3>
        <p className="text-slate-400 text-sm mb-5 leading-relaxed">{description}</p>
        <div className="flex flex-wrap gap-2 mb-5">
          {examples.map((example, i) => (
            <span key={i} className={`px-2.5 py-1 rounded-md text-xs font-medium border transition-all duration-300 group-hover:scale-105 ${colors.badge}`}>
              {example}
            </span>
          ))}
        </div>
        <div className={`flex items-center gap-2 text-sm font-semibold ${colors.cta} transition-all duration-300 group-hover:gap-3`}>
          <span>{ctaText}</span>
          {icons.arrow}
        </div>
      </div>
    </Link>
  )
}

// Animated stat card with staggered animation
function StatCard({ value, label, suffix = '', isVisible, delay = 0 }) {
  const count = useCounter(parseInt(value), 2000, true, isVisible)

  return (
    <div
      className="text-center"
      style={{
        opacity: isVisible ? 1 : 0,
        transform: isVisible ? 'translateY(0)' : 'translateY(20px)',
        transition: `all 0.6s ease ${delay}ms`
      }}
    >
      <div className="text-4xl lg:text-5xl font-bold text-white mb-2">
        {count}{suffix}
      </div>
      <div className="text-slate-400 text-sm">{label}</div>
    </div>
  )
}

// How It Works Step with animation
function HowItWorksStep({ number, title, description, icon, delay = 0, isVisible = true }) {
  return (
    <div
      className="relative flex flex-col items-center text-center group"
      style={{
        opacity: isVisible ? 1 : 0,
        transform: isVisible ? 'translateY(0)' : 'translateY(30px)',
        transition: `all 0.6s ease ${delay}ms`
      }}
    >
      <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-brand-500/20 to-indigo-500/20 border border-white/10 flex items-center justify-center mb-4 text-brand-400 group-hover:scale-110 transition-transform duration-300">
        {icon}
      </div>
      <div className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-brand-500 text-white text-xs font-bold flex items-center justify-center">
        {number}
      </div>
      <h4 className="text-white font-semibold mb-2">{title}</h4>
      <p className="text-slate-500 text-sm leading-relaxed">{description}</p>
    </div>
  )
}

export default function LandingHub() {
  const { i18n } = useTranslation()
  const lang = i18n.language?.startsWith('es') ? 'es' : 'en'
  const [mounted, setMounted] = useState(false)
  const [scrolled, setScrolled] = useState(false)

  // Scroll animations for each section
  const [statsRef, statsVisible] = useScrollAnimation(0.2)
  const [howItWorksRef, howItWorksVisible] = useScrollAnimation(0.2)
  const [industriesRef, industriesVisible] = useScrollAnimation(0.2)
  const [securityRef, securityVisible] = useScrollAnimation(0.2)
  const [ctaRef, ctaVisible] = useScrollAnimation(0.2)

  useEffect(() => {
    setMounted(true)
    const handleScroll = () => setScrolled(window.scrollY > 50)
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const content = {
    es: {
      nav: {
        product: 'Producto',
        security: 'Seguridad',
        docs: 'Documentación',
        login: 'Iniciar sesión',
        getStarted: 'Empezar gratis'
      },
      hero: {
        badge: 'Plataforma de ML Privacy-First',
        headline: 'Entrena modelos con datos',
        headlineHighlight: 'que no puedes ver.',
        subheadline: 'Múltiples organizaciones colaboran en UN modelo de ML sin exponer sus datos. Cifrado homomórfico de grado militar + Gobernanza descentralizada en blockchain.',
        cta: 'Solicitar Demo',
        ctaSecondary: 'Ver documentación'
      },
      trustedBy: 'Tecnología respaldada por',
      certifications: 'Certificaciones y Compliance',
      stats: {
        organizations: 'Organizaciones',
        dataProcessed: 'Datos procesados',
        accuracy: 'Precisión del modelo',
        uptime: 'Uptime'
      },
      howItWorks: {
        title: 'Cómo funciona',
        subtitle: 'Colaboración segura en 3 simples pasos',
        steps: [
          { title: 'Cifrado local', desc: 'Tus datos se cifran en tu infraestructura. La clave privada nunca sale.', icon: icons.lock },
          { title: 'Entrenamiento cifrado', desc: 'El modelo se entrena sobre datos cifrados. Nadie puede ver los datos originales.', icon: icons.eye },
          { title: 'Resultados privados', desc: 'Solo tú puedes descifrar tus predicciones con tu clave privada.', icon: icons.shield }
        ]
      },
      industries: {
        title: 'Soluciones por industria',
        subtitle: 'Casos de uso específicos para tu sector',
        list: [
          {
            icon: icons.finance,
            title: 'Finanzas y Banca',
            description: 'Fraude colaborativo, credit scoring multi-institucional y KYC/AML sin exponer datos de clientes.',
            examples: ['Fraude', 'Credit Scoring', 'KYC-AML'],
            link: '/fintech',
            color: 'brand'
          },
          {
            icon: icons.healthcare,
            title: 'Healthcare',
            description: 'Investigación médica multi-hospital y diagnóstico IA cumpliendo HIPAA sin exponer pacientes.',
            examples: ['Diagnóstico IA', 'Drug Discovery', 'Ensayos'],
            link: '/healthcare',
            color: 'emerald'
          },
          {
            icon: icons.government,
            title: 'Gobierno',
            description: 'Colaboración inter-agencias para fraude fiscal y políticas públicas data-driven.',
            examples: ['Fraude Fiscal', 'Políticas', 'Ventanilla Única'],
            link: '/gobierno',
            color: 'slate'
          }
        ]
      },
      otherIndustries: {
        text: '¿Otra industria?',
        subtext: 'Retail, seguros, telcos, logística y más',
        link: 'Explorar todas'
      },
      features: {
        title: 'Seguridad de nivel empresarial',
        list: [
          { title: 'Cifrado CKKS 128-bit', desc: 'Esquema homomórfico de última generación' },
          { title: 'Zero Knowledge', desc: 'Nadie ve tus datos, ni siquiera nosotros' },
          { title: 'Auditoría Blockchain', desc: 'Registro inmutable en Arbitrum L2' },
          { title: 'Open Source', desc: 'Código verificable y auditable' }
        ]
      },
      cta: {
        title: '¿Listo para colaborar sin compartir?',
        subtitle: 'Únete a las organizaciones que ya entrenan modelos sobre datos cifrados.',
        button: 'Solicitar Demo',
        note: 'Sin compromiso. Demo personalizada de 30 minutos.'
      },
      footer: {
        product: 'Producto',
        resources: 'Recursos',
        company: 'Empresa',
        legal: 'Legal',
        items: {
          features: 'Características',
          security: 'Seguridad',
          pricing: 'Precios',
          docs: 'Documentación',
          api: 'API Reference',
          github: 'GitHub',
          about: 'Sobre nosotros',
          blog: 'Blog',
          contact: 'Contacto',
          privacy: 'Privacidad',
          terms: 'Términos'
        },
        copyright: '© 2025 Xcapit Privacy. Todos los derechos reservados.',
        builtBy: 'Desarrollado por el equipo de'
      }
    },
    en: {
      nav: {
        product: 'Product',
        security: 'Security',
        docs: 'Documentation',
        login: 'Sign in',
        getStarted: 'Get started free'
      },
      hero: {
        badge: 'Privacy-First ML Platform',
        headline: 'Train models on data',
        headlineHighlight: 'you can\'t see.',
        subheadline: 'Multiple organizations collaborate on ONE ML model without exposing their data. Military-grade homomorphic encryption + Decentralized blockchain governance.',
        cta: 'Request Demo',
        ctaSecondary: 'View documentation'
      },
      trustedBy: 'Technology backed by',
      certifications: 'Certifications & Compliance',
      stats: {
        organizations: 'Organizations',
        dataProcessed: 'Data processed',
        accuracy: 'Model accuracy',
        uptime: 'Uptime'
      },
      howItWorks: {
        title: 'How it works',
        subtitle: 'Secure collaboration in 3 simple steps',
        steps: [
          { title: 'Local encryption', desc: 'Your data is encrypted in your infrastructure. Private key never leaves.', icon: icons.lock },
          { title: 'Encrypted training', desc: 'Model trains on encrypted data. No one can see original data.', icon: icons.eye },
          { title: 'Private results', desc: 'Only you can decrypt your predictions with your private key.', icon: icons.shield }
        ]
      },
      industries: {
        title: 'Solutions by industry',
        subtitle: 'Specific use cases for your sector',
        list: [
          {
            icon: icons.finance,
            title: 'Finance & Banking',
            description: 'Collaborative fraud, multi-institutional credit scoring and KYC/AML without exposing customer data.',
            examples: ['Fraud', 'Credit Scoring', 'KYC-AML'],
            link: '/fintech',
            color: 'brand'
          },
          {
            icon: icons.healthcare,
            title: 'Healthcare',
            description: 'Multi-hospital medical research and AI diagnosis compliant with HIPAA without exposing patients.',
            examples: ['AI Diagnosis', 'Drug Discovery', 'Trials'],
            link: '/healthcare',
            color: 'emerald'
          },
          {
            icon: icons.government,
            title: 'Government',
            description: 'Cross-agency collaboration for tax fraud and data-driven public policy.',
            examples: ['Tax Fraud', 'Policy', 'Single Window'],
            link: '/gobierno',
            color: 'slate'
          }
        ]
      },
      otherIndustries: {
        text: 'Different industry?',
        subtext: 'Retail, insurance, telcos, logistics and more',
        link: 'Explore all'
      },
      features: {
        title: 'Enterprise-grade security',
        list: [
          { title: 'CKKS 128-bit Encryption', desc: 'State-of-the-art homomorphic scheme' },
          { title: 'Zero Knowledge', desc: 'No one sees your data, not even us' },
          { title: 'Blockchain Audit', desc: 'Immutable record on Arbitrum L2' },
          { title: 'Open Source', desc: 'Verifiable and auditable code' }
        ]
      },
      cta: {
        title: 'Ready to collaborate without sharing?',
        subtitle: 'Join organizations already training models on encrypted data.',
        button: 'Request Demo',
        note: 'No commitment. Personalized 30-minute demo.'
      },
      footer: {
        product: 'Product',
        resources: 'Resources',
        company: 'Company',
        legal: 'Legal',
        items: {
          features: 'Features',
          security: 'Security',
          pricing: 'Pricing',
          docs: 'Documentation',
          api: 'API Reference',
          github: 'GitHub',
          about: 'About us',
          blog: 'Blog',
          contact: 'Contact',
          privacy: 'Privacy',
          terms: 'Terms'
        },
        copyright: '© 2025 Xcapit Privacy. All rights reserved.',
        builtBy: 'Built by the'
      }
    }
  }

  const t = content[lang]

  return (
    <div className="min-h-screen bg-[#0a0a0f] flex flex-col">
      <ParticleBackground />

      {/* Navigation */}
      <nav className={`fixed top-0 left-0 right-0 z-50 w-full transition-all duration-300 ${scrolled ? 'bg-[#0a0a0f]/80 backdrop-blur-xl border-b border-white/10 shadow-lg' : 'bg-transparent border-b border-white/5'}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-8">
              <Link to="/" className="flex items-center gap-2">
                <div className="w-9 h-9 bg-gradient-to-br from-brand-500 to-indigo-600 rounded-lg flex items-center justify-center">
                  {icons.lock}
                </div>
                <span className="text-lg font-bold text-white">Xcapit</span>
                <span className="text-lg font-light text-brand-400">Privacy</span>
              </Link>
              <div className="hidden md:flex items-center gap-6">
                <a href="#how-it-works" className="text-slate-400 hover:text-white text-sm font-medium transition">{t.nav.product}</a>
                <a href="#security" className="text-slate-400 hover:text-white text-sm font-medium transition">{t.nav.security}</a>
                <a href="#" className="text-slate-400 hover:text-white text-sm font-medium transition">{t.nav.docs}</a>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <LanguageSwitcher variant="minimal" />
              <Link to="/login" className="hidden sm:block text-slate-400 hover:text-white text-sm font-medium transition px-3 py-2">
                {t.nav.login}
              </Link>
              <Link to="/register" className="bg-brand-500 hover:bg-brand-600 text-white text-sm font-semibold px-4 py-2 rounded-lg transition shadow-lg shadow-brand-500/25">
                {t.nav.getStarted}
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-24 pb-20 lg:pt-32 lg:pb-32">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
            {/* Left - Content */}
            <div className={`transition-all duration-1000 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
              <div className="inline-flex items-center gap-2 bg-brand-500/10 border border-brand-500/20 rounded-full px-4 py-1.5 mb-6">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-brand-500"></span>
                </span>
                <span className="text-brand-300 text-sm font-medium">{t.hero.badge}</span>
              </div>

              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white mb-6 leading-[1.1]">
                {t.hero.headline}
                <br />
                <span className="bg-gradient-to-r from-brand-400 via-indigo-400 to-purple-400 bg-clip-text text-transparent">
                  {t.hero.headlineHighlight}
                </span>
              </h1>

              <p className="text-lg text-slate-400 mb-8 leading-relaxed max-w-xl">
                {t.hero.subheadline}
              </p>

              <div className="flex flex-col sm:flex-row gap-4 mb-10">
                <a href="#contact" className="inline-flex items-center justify-center gap-2 bg-brand-500 hover:bg-brand-600 text-white font-semibold px-6 py-3 rounded-xl transition shadow-lg shadow-brand-500/25">
                  {t.hero.cta}
                  {icons.arrow}
                </a>
                <a href="#" className="inline-flex items-center justify-center gap-2 bg-white/5 hover:bg-white/10 text-white font-semibold px-6 py-3 rounded-xl border border-white/10 transition">
                  {t.hero.ctaSecondary}
                </a>
              </div>

              {/* Certifications */}
              <div className="flex flex-wrap gap-3">
                <CertBadge name="SOC2" icon={icons.check} />
                <CertBadge name="GDPR" icon={icons.check} />
                <CertBadge name="HIPAA" icon={icons.check} />
                <CertBadge name="PCI-DSS" icon={icons.check} />
              </div>
            </div>

            {/* Right - Illustration */}
            <div className={`transition-all duration-1000 delay-300 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
              <HeroIllustration />
            </div>
          </div>
        </div>
      </section>

      {/* Trusted By */}
      <section className="relative py-12 border-y border-white/5">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-center text-slate-600 text-sm font-medium uppercase tracking-wider mb-8">
            {t.trustedBy}
          </p>
          <div className="flex flex-wrap justify-center items-center gap-8 md:gap-16">
            <CompanyLogo name="QuarkID" />
            <CompanyLogo name="Arbitrum" />
            <CompanyLogo name="Microsoft SEAL" />
            <CompanyLogo name="TenSEAL" />
            <CompanyLogo name="OpenZeppelin" />
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section
        ref={statsRef}
        className={`relative py-16 lg:py-20 transition-all duration-1000 ${statsVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            <StatCard value="50" suffix="+" label={t.stats.organizations} isVisible={statsVisible} delay={0} />
            <StatCard value="10" suffix="M+" label={t.stats.dataProcessed} isVisible={statsVisible} delay={150} />
            <StatCard value="99" suffix="%" label={t.stats.accuracy} isVisible={statsVisible} delay={300} />
            <StatCard value="99" suffix=".9%" label={t.stats.uptime} isVisible={statsVisible} delay={450} />
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section
        id="how-it-works"
        ref={howItWorksRef}
        className={`relative py-20 lg:py-28 transition-all duration-1000 ${howItWorksVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl lg:text-4xl font-bold text-white mb-4">{t.howItWorks.title}</h2>
            <p className="text-slate-400 text-lg">{t.howItWorks.subtitle}</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 lg:gap-12">
            {t.howItWorks.steps.map((step, index) => (
              <HowItWorksStep
                key={index}
                number={index + 1}
                title={step.title}
                description={step.desc}
                icon={step.icon}
                delay={index * 200}
                isVisible={howItWorksVisible}
              />
            ))}
          </div>

          {/* Connection lines */}
          <div className="hidden md:flex justify-center items-center mt-8">
            <div className="flex items-center gap-4">
              <div className="w-24 h-px bg-gradient-to-r from-transparent via-brand-500/50 to-transparent"></div>
              <div className="w-2 h-2 rounded-full bg-brand-500"></div>
              <div className="w-24 h-px bg-gradient-to-r from-transparent via-brand-500/50 to-transparent"></div>
              <div className="w-2 h-2 rounded-full bg-brand-500"></div>
              <div className="w-24 h-px bg-gradient-to-r from-transparent via-brand-500/50 to-transparent"></div>
            </div>
          </div>
        </div>
      </section>

      {/* Industries */}
      <section
        ref={industriesRef}
        className={`relative py-20 lg:py-28 bg-white/[0.02] transition-all duration-1000 ${industriesVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl lg:text-4xl font-bold text-white mb-4">{t.industries.title}</h2>
            <p className="text-slate-400 text-lg">{t.industries.subtitle}</p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 mb-10">
            {t.industries.list.map((industry, index) => (
              <IndustryCard
                key={index}
                icon={industry.icon}
                title={industry.title}
                description={industry.description}
                examples={industry.examples}
                link={industry.link}
                color={industry.color}
                delay={index * 150}
                isVisible={industriesVisible}
              />
            ))}
          </div>

          <div className="text-center">
            <Link to="/industrias" className="group inline-flex items-center gap-2 text-slate-400 hover:text-white transition">
              <span>{t.otherIndustries.text}</span>
              <span className="text-slate-500">{t.otherIndustries.subtext}</span>
              <span className="text-brand-400 font-semibold group-hover:translate-x-1 transition-transform">
                {t.otherIndustries.link} →
              </span>
            </Link>
          </div>
        </div>
      </section>

      {/* Security Features */}
      <section
        id="security"
        ref={securityRef}
        className={`relative py-20 lg:py-28 transition-all duration-1000 ${securityVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl lg:text-4xl font-bold text-white mb-4">{t.features.title}</h2>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {t.features.list.map((feature, index) => (
              <div
                key={index}
                className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6 hover:bg-white/[0.07] hover:border-white/20 hover:scale-105 transition-all duration-300"
                style={{
                  opacity: securityVisible ? 1 : 0,
                  transform: securityVisible ? 'translateY(0)' : 'translateY(30px)',
                  transition: `all 0.5s ease ${index * 100}ms`
                }}
              >
                <div className="w-10 h-10 rounded-lg bg-brand-500/20 flex items-center justify-center mb-4 text-brand-400">
                  {icons.shield}
                </div>
                <h3 className="text-white font-semibold mb-2">{feature.title}</h3>
                <p className="text-slate-500 text-sm">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section
        id="contact"
        ref={ctaRef}
        className={`relative py-20 lg:py-28 transition-all duration-1000 ${ctaVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}
      >
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="relative bg-gradient-to-br from-brand-500/20 to-indigo-500/20 border border-white/10 rounded-3xl p-8 lg:p-12 text-center overflow-hidden group hover:border-brand-500/30 transition-all duration-500">
            {/* Animated background gradient */}
            <div className="absolute inset-0 bg-gradient-to-br from-brand-500/5 to-indigo-500/5 group-hover:from-brand-500/10 group-hover:to-indigo-500/10 transition-all duration-500"></div>

            {/* Floating orbs */}
            <div className="absolute -top-20 -left-20 w-40 h-40 bg-brand-500/20 rounded-full blur-3xl group-hover:scale-150 transition-transform duration-700"></div>
            <div className="absolute -bottom-20 -right-20 w-40 h-40 bg-indigo-500/20 rounded-full blur-3xl group-hover:scale-150 transition-transform duration-700"></div>

            <div className="relative">
              <h2 className="text-3xl lg:text-4xl font-bold text-white mb-4">{t.cta.title}</h2>
              <p className="text-slate-300 text-lg mb-8 max-w-2xl mx-auto">{t.cta.subtitle}</p>
              <a
                href="mailto:consorcios@xcapit.com"
                className="inline-flex items-center justify-center gap-2 bg-white text-slate-900 font-semibold px-8 py-4 rounded-xl hover:bg-slate-100 hover:scale-105 active:scale-95 transition-all duration-300 shadow-xl hover:shadow-2xl hover:shadow-brand-500/20"
              >
                {t.cta.button}
                {icons.arrow}
              </a>
              <p className="text-slate-500 text-sm mt-4">{t.cta.note}</p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative border-t border-white/5 py-12 lg:py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-8 mb-12">
            <div className="col-span-2">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-9 h-9 bg-gradient-to-br from-brand-500 to-indigo-600 rounded-lg flex items-center justify-center">
                  {icons.lock}
                </div>
                <span className="text-lg font-bold text-white">Xcapit</span>
                <span className="text-lg font-light text-brand-400">Privacy</span>
              </div>
              <p className="text-slate-500 text-sm mb-4">
                {t.footer.builtBy}{' '}
                <a href="https://quarkid.org" target="_blank" rel="noopener noreferrer" className="text-white hover:text-brand-400 transition">
                  QuarkID
                </a>{' '}
                (3.6M+ users)
              </p>
            </div>

            <div>
              <h4 className="text-white font-semibold mb-4">{t.footer.product}</h4>
              <ul className="space-y-2">
                <li><a href="#" className="text-slate-500 hover:text-white text-sm transition">{t.footer.items.features}</a></li>
                <li><a href="#" className="text-slate-500 hover:text-white text-sm transition">{t.footer.items.security}</a></li>
                <li><a href="#" className="text-slate-500 hover:text-white text-sm transition">{t.footer.items.pricing}</a></li>
              </ul>
            </div>

            <div>
              <h4 className="text-white font-semibold mb-4">{t.footer.resources}</h4>
              <ul className="space-y-2">
                <li><a href="#" className="text-slate-500 hover:text-white text-sm transition">{t.footer.items.docs}</a></li>
                <li><a href="#" className="text-slate-500 hover:text-white text-sm transition">{t.footer.items.api}</a></li>
                <li><a href="https://github.com/xcapit" target="_blank" rel="noopener noreferrer" className="text-slate-500 hover:text-white text-sm transition">{t.footer.items.github}</a></li>
              </ul>
            </div>

            <div>
              <h4 className="text-white font-semibold mb-4">{t.footer.company}</h4>
              <ul className="space-y-2">
                <li><a href="#" className="text-slate-500 hover:text-white text-sm transition">{t.footer.items.about}</a></li>
                <li><a href="#" className="text-slate-500 hover:text-white text-sm transition">{t.footer.items.blog}</a></li>
                <li><a href="mailto:consorcios@xcapit.com" className="text-slate-500 hover:text-white text-sm transition">{t.footer.items.contact}</a></li>
              </ul>
            </div>
          </div>

          <div className="flex flex-col md:flex-row justify-between items-center pt-8 border-t border-white/5">
            <p className="text-slate-600 text-sm">{t.footer.copyright}</p>
            <div className="flex items-center gap-6 mt-4 md:mt-0">
              <a href="#" className="text-slate-600 hover:text-white text-sm transition">{t.footer.items.privacy}</a>
              <a href="#" className="text-slate-600 hover:text-white text-sm transition">{t.footer.items.terms}</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
