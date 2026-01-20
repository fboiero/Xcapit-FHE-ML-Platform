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

function ParticleBackground() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {/* Large gradient blurs */}
      <div className="absolute top-0 -left-40 w-[500px] h-[500px] bg-purple-500/20 rounded-full blur-[150px] animate-pulse" />
      <div className="absolute bottom-0 -right-40 w-[500px] h-[500px] bg-indigo-500/20 rounded-full blur-[150px] animate-pulse" style={{ animationDelay: '1s' }} />

      {/* Floating particles */}
      {[...Array(15)].map((_, i) => (
        <div
          key={i}
          className="absolute w-1 h-1 bg-purple-400/40 rounded-full"
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

function HeroIllustration() {
  return (
    <div className="relative w-full max-w-lg mx-auto">
      <svg viewBox="0 0 400 300" className="w-full h-auto">
        <defs>
          <linearGradient id="gradientPurple" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#9333ea" />
            <stop offset="100%" stopColor="#6366f1" />
          </linearGradient>
          <filter id="glow"><feGaussianBlur stdDeviation="3" result="coloredBlur"/><feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
        </defs>

        {/* Company nodes */}
        <g className="animate-pulse" style={{ animationDuration: '3s' }}>
          <rect x="20" y="40" width="70" height="50" rx="8" fill="#1e293b" stroke="url(#gradientPurple)" strokeWidth="2" />
          <text x="55" y="68" textAnchor="middle" fill="#94a3b8" fontSize="9">Company A</text>

          <rect x="20" y="105" width="70" height="50" rx="8" fill="#1e293b" stroke="url(#gradientPurple)" strokeWidth="2" />
          <text x="55" y="133" textAnchor="middle" fill="#94a3b8" fontSize="9">Company B</text>

          <rect x="20" y="170" width="70" height="50" rx="8" fill="#1e293b" stroke="url(#gradientPurple)" strokeWidth="2" />
          <text x="55" y="198" textAnchor="middle" fill="#94a3b8" fontSize="9">Company C</text>

          <rect x="20" y="235" width="70" height="50" rx="8" fill="#1e293b" stroke="url(#gradientPurple)" strokeWidth="2" />
          <text x="55" y="263" textAnchor="middle" fill="#94a3b8" fontSize="9">Company D</text>
        </g>

        {/* Connection lines */}
        {[65, 130, 195, 260].map((y, i) => (
          <path key={i} d={`M90 ${y} Q130 ${y} 155 150`} stroke="url(#gradientPurple)" strokeWidth="2" fill="none" strokeDasharray="5,5" opacity="0.5">
            <animate attributeName="stroke-dashoffset" from="0" to="-20" dur={`${2 + i * 0.3}s`} repeatCount="indefinite"/>
          </path>
        ))}

        {/* Central model */}
        <g filter="url(#glow)">
          <rect x="155" y="100" width="110" height="100" rx="12" fill="#1e293b" stroke="url(#gradientPurple)" strokeWidth="2"/>
          <text x="210" y="130" textAnchor="middle" fill="white" fontSize="11" fontWeight="bold">Industry ML</text>
          <rect x="170" y="145" width="80" height="30" rx="6" fill="#334155"/>
          <path d="M185 160 L195 170 L215 150" stroke="#10b981" strokeWidth="3" fill="none" strokeLinecap="round"/>
          <text x="210" y="190" textAnchor="middle" fill="#a855f7" fontSize="8">Encrypted Training</text>
        </g>

        {/* Output */}
        <path d="M265 150 L310 150" stroke="#10b981" strokeWidth="2" fill="none" strokeDasharray="5,5" opacity="0.6">
          <animate attributeName="stroke-dashoffset" from="-20" to="0" dur="2s" repeatCount="indefinite"/>
        </path>

        <g className="animate-pulse" style={{ animationDuration: '2s', animationDelay: '1s' }}>
          <rect x="310" y="110" width="75" height="80" rx="8" fill="#1e293b" stroke="#10b981" strokeWidth="1.5" />
          <text x="347" y="135" textAnchor="middle" fill="#10b981" fontSize="9">Results</text>
          <text x="347" y="155" textAnchor="middle" fill="white" fontSize="12" fontWeight="bold">+25%</text>
          <text x="347" y="175" textAnchor="middle" fill="#94a3b8" fontSize="8">Better Predictions</text>
        </g>
      </svg>
    </div>
  )
}

function StatCard({ value, label, icon }) {
  return (
    <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/10 hover:border-purple-400/30 transition-all">
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 bg-purple-500/20 rounded-xl flex items-center justify-center text-2xl">{icon}</div>
        <div>
          <div className="text-3xl font-bold text-white">{value}</div>
          <div className="text-slate-400 text-sm">{label}</div>
        </div>
      </div>
    </div>
  )
}

function ContactForm({ lang }) {
  const [formData, setFormData] = useState({ name: '', email: '', company: '', phone: '', job_title: '', industry: '', use_case: '' })
  const [status, setStatus] = useState('idle')

  const t = {
    es: {
      title: 'Agendar Demo', subtitle: 'Contanos tu caso de uso y te mostramos cómo armar un consorcio.',
      name: 'Nombre completo', email: 'Email corporativo', company: 'Empresa', phone: 'Teléfono', position: 'Cargo',
      industry: 'Industria', industries: ['Retail', 'Seguros', 'Telecomunicaciones', 'Logística', 'Manufactura', 'Otra'],
      useCase: 'Describe tu caso de uso', submit: 'Agendar Demo', sending: 'Enviando...', success: 'Mensaje enviado.',
      error: 'Error al enviar.', also: 'También puedes contactarnos en'
    },
    en: {
      title: 'Book Demo', subtitle: 'Tell us your use case and we\'ll show you how to build a consortium.',
      name: 'Full name', email: 'Corporate email', company: 'Company', phone: 'Phone', position: 'Job title',
      industry: 'Industry', industries: ['Retail', 'Insurance', 'Telecommunications', 'Logistics', 'Manufacturing', 'Other'],
      useCase: 'Describe your use case', submit: 'Book Demo', sending: 'Sending...', success: 'Message sent.',
      error: 'Error sending.', also: 'You can also contact us at'
    }
  }[lang]

  const handleSubmit = async (e) => {
    e.preventDefault()
    setStatus('sending')
    try {
      const response = await fetch('https://api.web3forms.com/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          access_key: 'd7f419bc-95cf-498d-8d8b-5f4830622bf4',
          subject: 'Demo Request - Other Industries - Xcapit Privacy',
          from_name: 'Xcapit Privacy', vertical: 'Other Industries', ...formData
        }),
      })
      if (response.ok) {
        setStatus('success')
        setFormData({ name: '', email: '', company: '', phone: '', job_title: '', industry: '', use_case: '' })
      } else setStatus('error')
    } catch { setStatus('error') }
  }

  return (
    <div className="bg-white/10 backdrop-blur-md rounded-2xl p-8 border border-white/20 shadow-2xl">
      <h3 className="text-2xl font-bold text-white mb-2">{t.title}</h3>
      <p className="text-slate-300 mb-6">{t.subtitle}</p>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid md:grid-cols-2 gap-4">
          <input type="text" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} placeholder={t.name} required className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl focus:outline-none focus:border-purple-400 text-white placeholder-slate-400 transition" />
          <input type="email" value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })} placeholder={t.email} required className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl focus:outline-none focus:border-purple-400 text-white placeholder-slate-400 transition" />
        </div>
        <div className="grid md:grid-cols-2 gap-4">
          <input type="text" value={formData.company} onChange={(e) => setFormData({ ...formData, company: e.target.value })} placeholder={t.company} required className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl focus:outline-none focus:border-purple-400 text-white placeholder-slate-400 transition" />
          <input type="tel" value={formData.phone} onChange={(e) => setFormData({ ...formData, phone: e.target.value })} placeholder={t.phone} className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl focus:outline-none focus:border-purple-400 text-white placeholder-slate-400 transition" />
        </div>
        <div className="grid md:grid-cols-2 gap-4">
          <input type="text" value={formData.job_title} onChange={(e) => setFormData({ ...formData, job_title: e.target.value })} placeholder={t.position} required className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl focus:outline-none focus:border-purple-400 text-white placeholder-slate-400 transition" />
          <select value={formData.industry} onChange={(e) => setFormData({ ...formData, industry: e.target.value })} required className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl focus:outline-none focus:border-purple-400 text-white placeholder-slate-400 transition appearance-none cursor-pointer">
            <option value="" className="bg-slate-800">{t.industry}</option>
            {t.industries.map(ind => <option key={ind} value={ind} className="bg-slate-800">{ind}</option>)}
          </select>
        </div>
        <textarea value={formData.use_case} onChange={(e) => setFormData({ ...formData, use_case: e.target.value })} placeholder={t.useCase} rows={3} className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl focus:outline-none focus:border-purple-400 text-white placeholder-slate-400 transition resize-none" />
        <button type="submit" disabled={status === 'sending'} className="w-full bg-gradient-to-r from-purple-600 to-indigo-600 text-white py-4 px-6 rounded-xl font-semibold hover:from-purple-700 hover:to-indigo-700 transition disabled:opacity-50 shadow-lg shadow-purple-500/25">
          {status === 'sending' ? t.sending : t.submit}
        </button>
        {status === 'success' && <p className="text-green-400 text-center font-medium">{t.success}</p>}
        {status === 'error' && <p className="text-red-400 text-center font-medium">{t.error}</p>}
      </form>
      <p className="mt-6 text-center text-sm text-slate-400">{t.also}{' '}<a href="mailto:consorcios@xcapit.com" className="text-purple-400 font-medium hover:underline">consorcios@xcapit.com</a></p>
    </div>
  )
}

function IndustryCard({ icon, title, problem, solution, metric }) {
  return (
    <div className="group bg-white rounded-2xl p-6 border border-slate-200 hover:shadow-2xl hover:shadow-purple-500/10 hover:-translate-y-1 transition-all duration-300">
      <div className="w-14 h-14 bg-gradient-to-br from-purple-500/10 to-indigo-500/10 rounded-2xl flex items-center justify-center mb-4 text-3xl group-hover:scale-110 transition-transform">{icon}</div>
      <h3 className="text-xl font-bold text-slate-900 mb-3">{title}</h3>
      <p className="text-slate-600 text-sm mb-3">{problem}</p>
      <p className="text-purple-600 text-sm font-medium mb-4">{solution}</p>
      <div className="pt-4 border-t border-slate-100">
        <span className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-indigo-600 bg-clip-text text-transparent">{metric}</span>
      </div>
    </div>
  )
}

function StepCard({ number, title, description }) {
  return (
    <div className="relative group">
      <div className="absolute -inset-0.5 bg-gradient-to-r from-purple-500 to-indigo-500 rounded-2xl blur opacity-0 group-hover:opacity-30 transition duration-500" />
      <div className="relative bg-white rounded-2xl p-8 border border-slate-200">
        <div className="w-12 h-12 bg-gradient-to-br from-purple-600 to-indigo-600 rounded-xl flex items-center justify-center text-white font-bold text-lg mb-4">{number}</div>
        <h3 className="text-xl font-bold text-slate-900 mb-2">{title}</h3>
        <p className="text-slate-600">{description}</p>
      </div>
    </div>
  )
}

export default function LandingOtros() {
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
      nav: { industrias: 'Industrias', comoFunciona: 'Cómo Funciona', gobernanza: 'Gobernanza', demo: 'Demo' },
      hero: {
        badge: 'Todas las Industrias',
        headline: 'Modelos de ML entrenados con datos de toda tu industria.',
        highlight: 'Sin compartir los tuyos.',
        subheadline: 'Empresas competidoras pueden colaborar en modelos de predicción, detección y optimización. Cada una mejora sus resultados. Ninguna ve los datos del otro.',
        cta: 'Agendar Demo', ctaSecondary: 'Ver cómo funciona',
        stats: { accuracy: { value: '+25%', label: 'Mejor precisión' }, privacy: { value: '100%', label: 'Privacidad' }, trade: { value: '0%', label: 'Exposición datos' } }
      },
      trustedBy: { title: 'Tecnología utilizada por', partners: ['Microsoft SEAL', 'TenSEAL', 'OpenFHE', 'HElib'] },
      problem: {
        title: 'Tus datos son valiosos. Los de tu competencia, también.',
        points: [
          { title: 'Modelos limitados', desc: 'Tu modelo está limitado a tus propios datos. Tu competencia tiene patrones diferentes que mejorarían tu modelo.', icon: '📊' },
          { title: 'Industrias que podrían colaborar', desc: 'Retailers podrían predecir demanda juntos. Aseguradoras detectar fraude en red. Telcos optimizar redes.', icon: '🤝' },
          { title: 'Datos externos = dependencia', desc: 'Compras datos de proveedores externos. Son caros, incompletos, y no reflejan tu mercado específico.', icon: '💰' }
        ]
      },
      solution: {
        title: 'Colaboración entre competidores. Sin compartir secretos.',
        desc: 'Con cifrado homomórfico, múltiples empresas pueden entrenar UN modelo compartido sin que nadie vea los datos del otro.',
        steps: [
          { title: 'Cifras tus datos', desc: 'Tu información comercial se cifra con tu clave. Nunca sale de tu control.' },
          { title: 'Entrenas en conjunto', desc: 'El modelo aprende de datos cifrados de múltiples empresas.' },
          { title: 'Mejores predicciones', desc: 'Obtenés un modelo entrenado con datos de toda la industria.' }
        ]
      },
      industries: {
        title: 'Casos de Uso por Industria',
        cases: [
          { icon: '🛒', title: 'Retail / E-commerce', problem: 'Predecir demanda con solo tus datos es limitado.', solution: 'Modelo entrenado con datos de múltiples retailers.', metric: '+25% precisión' },
          { icon: '🛡️', title: 'Seguros', problem: 'Las redes de fraude operan entre múltiples aseguradoras.', solution: 'Detección de patrones de fraude coordinado.', metric: '+60% detección' },
          { icon: '📡', title: 'Telecomunicaciones', problem: 'Optimizar la red con solo tus datos pierde patrones.', solution: 'Modelos basados en datos de múltiples operadores.', metric: '-30% congestión' },
          { icon: '📦', title: 'Logística', problem: 'Cada empresa ve solo su parte de la cadena.', solution: 'Modelo predictivo para anticipar disrupciones.', metric: '+40% anticipación' },
          { icon: '🏭', title: 'Manufactura', problem: 'Tu modelo de mantenimiento solo ve tus fallas.', solution: 'Modelo con datos de equipamiento similar.', metric: '-35% downtime' },
          { icon: '🔮', title: 'Tu Industria', problem: '¿Tenés un caso de uso específico?', solution: 'Contanos y te mostramos cómo armar un consorcio.', metric: 'Personalizado' }
        ]
      },
      compliance: {
        title: 'Secreto comercial 100% protegido',
        desc: 'El cifrado homomórfico garantiza que tus datos comerciales nunca son visibles para nadie.',
        badges: ['Secreto Comercial', 'GDPR/LGPD', 'Acuerdos NDA', 'Propiedad Intelectual']
      },
      consortium: {
        title: 'Crear un consorcio de datos es simple',
        steps: [
          { title: 'Identifica participantes', desc: 'Empresas con datos complementarios' },
          { title: 'Define el caso de uso', desc: '¿Qué modelo quieren entrenar juntos?' },
          { title: 'Establece gobernanza', desc: 'Voting power, reglas, distribución de valor' },
          { title: 'Integra y entrena', desc: 'Cada participante cifra y aporta' },
          { title: 'Usa y mejora', desc: 'Predicciones mejoradas para todos' }
        ]
      },
      governance: {
        title: 'Gobernanza transparente entre competidores',
        features: [
          { title: 'Blockchain', desc: 'Todas las decisiones registradas' },
          { title: 'Votación', desc: 'Voto proporcional' },
          { title: 'Transparencia', desc: 'Cualquier participante puede auditar' },
          { title: 'Neutralidad', desc: 'Nadie puede ver datos de otros' }
        ]
      },
      cta: { title: '¿Listo para modelos entrenados con datos de toda tu industria?', subtitle: 'Contanos tu caso de uso y te mostramos cómo.' },
      footer: { product: 'Producto', contact: 'Contacto', rights: '© 2025 Xcapit Privacy. Todos los derechos reservados.', links: { industries: 'Otras industrias', github: 'GitHub' } }
    },
    en: {
      nav: { industrias: 'Industries', comoFunciona: 'How it Works', gobernanza: 'Governance', demo: 'Demo' },
      hero: {
        badge: 'All Industries',
        headline: 'ML models trained on industry-wide data.',
        highlight: 'Without sharing yours.',
        subheadline: 'Competing companies can collaborate on prediction, detection, and optimization models. Each improves their results. None sees each other\'s data.',
        cta: 'Book Demo', ctaSecondary: 'See how it works',
        stats: { accuracy: { value: '+25%', label: 'Better accuracy' }, privacy: { value: '100%', label: 'Privacy' }, trade: { value: '0%', label: 'Data exposure' } }
      },
      trustedBy: { title: 'Technology used by', partners: ['Microsoft SEAL', 'TenSEAL', 'OpenFHE', 'HElib'] },
      problem: {
        title: 'Your data is valuable. So is your competitors\'.',
        points: [
          { title: 'Limited models', desc: 'Your model is limited to your own data. Your competitors have different patterns that would improve your model.', icon: '📊' },
          { title: 'Industries that could collaborate', desc: 'Retailers could predict demand together. Insurers detect networked fraud. Telcos optimize networks.', icon: '🤝' },
          { title: 'External data = dependency', desc: 'You buy data from external providers. It\'s expensive, incomplete, and doesn\'t reflect your market.', icon: '💰' }
        ]
      },
      solution: {
        title: 'Collaboration among competitors. Without sharing secrets.',
        desc: 'With homomorphic encryption, multiple companies can train ONE shared model without anyone seeing each other\'s data.',
        steps: [
          { title: 'Encrypt your data', desc: 'Your business information is encrypted with your key. Never leaves your control.' },
          { title: 'Train together', desc: 'Model learns from encrypted data from multiple companies.' },
          { title: 'Better predictions', desc: 'You get a model trained on industry-wide data.' }
        ]
      },
      industries: {
        title: 'Use Cases by Industry',
        cases: [
          { icon: '🛒', title: 'Retail / E-commerce', problem: 'Predicting demand with only your data is limited.', solution: 'Model trained on data from multiple retailers.', metric: '+25% accuracy' },
          { icon: '🛡️', title: 'Insurance', problem: 'Fraud networks operate across multiple insurers.', solution: 'Detection of coordinated fraud patterns.', metric: '+60% detection' },
          { icon: '📡', title: 'Telecommunications', problem: 'Optimizing with only your data misses patterns.', solution: 'Models based on data from multiple operators.', metric: '-30% congestion' },
          { icon: '📦', title: 'Logistics', problem: 'Each company sees only its part of the chain.', solution: 'Predictive model to anticipate disruptions.', metric: '+40% anticipation' },
          { icon: '🏭', title: 'Manufacturing', problem: 'Your maintenance model only sees your failures.', solution: 'Model with similar equipment data.', metric: '-35% downtime' },
          { icon: '🔮', title: 'Your Industry', problem: 'Have a specific use case?', solution: 'Tell us and we\'ll show you how to build a consortium.', metric: 'Custom' }
        ]
      },
      compliance: {
        title: 'Trade secrets 100% protected',
        desc: 'Homomorphic encryption guarantees your business data is never visible to anyone.',
        badges: ['Trade Secrets', 'GDPR/LGPD', 'NDA Agreements', 'Intellectual Property']
      },
      consortium: {
        title: 'Creating a data consortium is simple',
        steps: [
          { title: 'Identify participants', desc: 'Companies with complementary data' },
          { title: 'Define the use case', desc: 'What model do you want to train?' },
          { title: 'Establish governance', desc: 'Voting power, rules, value distribution' },
          { title: 'Integrate and train', desc: 'Each participant encrypts and contributes' },
          { title: 'Use and improve', desc: 'Improved predictions for all' }
        ]
      },
      governance: {
        title: 'Transparent governance among competitors',
        features: [
          { title: 'Blockchain', desc: 'All decisions recorded' },
          { title: 'Voting', desc: 'Proportional vote' },
          { title: 'Transparency', desc: 'Any participant can audit' },
          { title: 'Neutrality', desc: 'No one can see others\' data' }
        ]
      },
      cta: { title: 'Ready for models trained on industry-wide data?', subtitle: 'Tell us your use case and we\'ll show you how.' },
      footer: { product: 'Product', contact: 'Contact', rights: '© 2025 Xcapit Privacy. All rights reserved.', links: { industries: 'Other industries', github: 'GitHub' } }
    }
  }

  const t = content[lang]

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Navigation */}
      <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${scrolled ? 'bg-slate-900/95 backdrop-blur-md shadow-lg' : 'bg-transparent'}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link to="/hub" className="flex items-center group">
              <div className="w-10 h-10 bg-gradient-to-br from-purple-600 to-indigo-600 rounded-xl flex items-center justify-center mr-2 group-hover:scale-105 transition-transform">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
              </div>
              <span className="text-xl font-bold text-white">Xcapit</span>
              <span className="text-xl font-light text-purple-400 ml-1">Privacy</span>
            </Link>
            <div className="hidden md:flex items-center gap-6">
              <a href="#industries" className="text-slate-300 hover:text-white font-medium transition">{t.nav.industrias}</a>
              <a href="#how-it-works" className="text-slate-300 hover:text-white font-medium transition">{t.nav.comoFunciona}</a>
              <a href="#governance" className="text-slate-300 hover:text-white font-medium transition">{t.nav.gobernanza}</a>
            </div>
            <div className="flex items-center gap-3">
              <LanguageSwitcher variant="toggle" />
              <a href="#contact" className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white px-5 py-2.5 rounded-lg font-medium hover:from-purple-700 hover:to-indigo-700 transition shadow-lg shadow-purple-500/25">{t.hero.cta}</a>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center pt-16 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-slate-950 via-purple-950/30 to-indigo-950" />
        <div className="absolute inset-0">
          <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-purple-500/10 rounded-full blur-3xl" />
          <div className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] bg-indigo-500/10 rounded-full blur-3xl" />
        </div>
        <ParticleBackground />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <div className="inline-flex items-center gap-2 bg-white/5 backdrop-blur-sm px-4 py-2 rounded-full mb-8 border border-white/10">
                <span className="text-2xl">🏢</span>
                <span className="text-white/90 text-sm font-medium">{t.hero.badge}</span>
              </div>

              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-6 leading-tight">
                {t.hero.headline}<br />
                <span className="bg-gradient-to-r from-purple-400 via-violet-400 to-indigo-400 bg-clip-text text-transparent">{t.hero.highlight}</span>
              </h1>

              <p className="text-lg lg:text-xl text-slate-300 mb-8 max-w-xl leading-relaxed">{t.hero.subheadline}</p>

              <div className="flex flex-col sm:flex-row gap-4 mb-12">
                <a href="#contact" className="inline-flex items-center justify-center gap-3 bg-gradient-to-r from-purple-600 to-indigo-600 text-white px-8 py-4 rounded-xl font-semibold hover:from-purple-700 hover:to-indigo-700 transition text-lg shadow-2xl shadow-purple-500/25">
                  {t.hero.cta}
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" /></svg>
                </a>
                <a href="#how-it-works" className="inline-flex items-center justify-center gap-2 bg-white/5 backdrop-blur-sm text-white px-8 py-4 rounded-xl font-semibold hover:bg-white/10 transition text-lg border border-white/10">{t.hero.ctaSecondary}</a>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <StatCard value={t.hero.stats.accuracy.value} label={t.hero.stats.accuracy.label} icon="📈" />
                <StatCard value={t.hero.stats.privacy.value} label={t.hero.stats.privacy.label} icon="🔒" />
                <StatCard value={t.hero.stats.trade.value} label={t.hero.stats.trade.label} icon="✓" />
              </div>
            </div>
            <div className="hidden lg:block"><HeroIllustration /></div>
          </div>
        </div>
      </section>

      {/* Trusted By Section */}
      <section className="relative py-12 border-y border-white/5 bg-slate-900/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-center text-slate-500 text-sm uppercase tracking-wider mb-8">{t.trustedBy.title}</p>
          <div className="flex flex-wrap justify-center items-center gap-8 md:gap-16">
            {t.trustedBy.partners.map((partner, idx) => (
              <div key={idx} className="text-slate-400 font-semibold text-lg hover:text-white transition cursor-default">{partner}</div>
            ))}
          </div>
        </div>
      </section>

      {/* Problem Section */}
      <section className="py-24 bg-slate-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">{t.problem.title}</h2>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {t.problem.points.map((point, index) => (
              <div key={index} className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-8 border border-slate-700 hover:border-red-500/30 transition-colors">
                <div className="w-14 h-14 bg-red-500/10 rounded-2xl flex items-center justify-center mb-6"><span className="text-3xl">{point.icon}</span></div>
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
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">{t.solution.title}</h2>
            <p className="text-xl text-slate-400 max-w-3xl mx-auto">{t.solution.desc}</p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {t.solution.steps.map((step, index) => (
              <StepCard key={index} number={index + 1} title={step.title} description={step.desc} />
            ))}
          </div>
        </div>
      </section>

      {/* Industries Section */}
      <section id="industries" className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4">{t.industries.title}</h2>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {t.industries.cases.map((industry, index) => (
              <IndustryCard key={index} icon={industry.icon} title={industry.title} problem={industry.problem} solution={industry.solution} metric={industry.metric} />
            ))}
          </div>
        </div>
      </section>

      {/* Consortium Steps */}
      <section className="py-24 bg-slate-50">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl md:text-4xl font-bold text-slate-900 text-center mb-12">{t.consortium.title}</h2>
          <div className="space-y-6">
            {t.consortium.steps.map((step, index) => (
              <div key={index} className="flex items-start gap-4 bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                <div className="w-10 h-10 bg-purple-600 text-white rounded-full flex items-center justify-center font-bold flex-shrink-0">{index + 1}</div>
                <div>
                  <h3 className="font-semibold text-slate-900 mb-1">{step.title}</h3>
                  <p className="text-slate-600">{step.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Governance Section */}
      <section id="governance" className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl md:text-4xl font-bold text-slate-900 text-center mb-12">{t.governance.title}</h2>
          <div className="grid md:grid-cols-4 gap-6">
            {t.governance.features.map((feature, index) => (
              <div key={index} className="bg-slate-50 p-6 rounded-xl border border-slate-200 text-center">
                <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl">{index === 0 ? '⛓️' : index === 1 ? '🗳️' : index === 2 ? '🔍' : '🔐'}</span>
                </div>
                <h3 className="font-semibold text-slate-900 mb-2">{feature.title}</h3>
                <p className="text-sm text-slate-600">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Compliance Section */}
      <section className="py-24 bg-slate-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4">{t.compliance.title}</h2>
            <p className="text-xl text-slate-600 max-w-3xl mx-auto">{t.compliance.desc}</p>
          </div>
          <div className="flex flex-wrap justify-center gap-4">
            {t.compliance.badges.map((badge, index) => (
              <div key={index} className="flex items-center gap-2 bg-purple-50 border border-purple-200 px-6 py-3 rounded-full hover:scale-105 transition-transform">
                <svg className="w-5 h-5 text-purple-600" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                <span className="font-semibold text-purple-800">{badge}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Contact Section */}
      <section id="contact" className="py-24 bg-gradient-to-br from-slate-950 via-purple-950/30 to-indigo-950 relative overflow-hidden">
        <div className="absolute inset-0">
          <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-purple-500/10 rounded-full blur-3xl" />
          <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-indigo-500/10 rounded-full blur-3xl" />
        </div>
        <div className="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">{t.cta.title}</h2>
            <p className="text-xl text-slate-300">{t.cta.subtitle}</p>
          </div>
          <ContactForm lang={lang} />
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-950 py-16 border-t border-white/5">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="flex items-center">
              <div className="w-10 h-10 bg-gradient-to-br from-purple-600 to-indigo-600 rounded-xl flex items-center justify-center mr-2">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
              </div>
              <span className="text-xl font-bold text-white">Xcapit</span>
              <span className="text-xl font-light text-purple-400 ml-1">Privacy</span>
            </div>
            <div className="flex items-center gap-6">
              <Link to="/hub" className="text-slate-400 hover:text-white text-sm transition">{t.footer.links.industries}</Link>
              <a href="mailto:consorcios@xcapit.com" className="text-slate-400 hover:text-white text-sm transition">consorcios@xcapit.com</a>
              <a href="https://github.com/xcapit" target="_blank" rel="noopener noreferrer" className="text-slate-400 hover:text-white text-sm transition">{t.footer.links.github}</a>
            </div>
          </div>
          <div className="mt-8 pt-8 border-t border-white/5 text-center">
            <p className="text-slate-500 text-sm">{t.footer.rights}</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
