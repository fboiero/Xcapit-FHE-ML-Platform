import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import LanguageSwitcher from '../components/LanguageSwitcher'

function ParticleBackground() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      <div className="absolute w-2 h-2 bg-slate-400/30 rounded-full animate-pulse" style={{ top: '10%', left: '10%' }} />
      <div className="absolute w-3 h-3 bg-slate-400/20 rounded-full animate-pulse" style={{ top: '20%', right: '20%', animationDelay: '0.5s' }} />
      <div className="absolute w-2 h-2 bg-slate-300/30 rounded-full animate-pulse" style={{ top: '60%', left: '5%', animationDelay: '1s' }} />
      <div className="absolute w-4 h-4 bg-slate-400/20 rounded-full animate-pulse" style={{ top: '80%', right: '15%', animationDelay: '1.5s' }} />
    </div>
  )
}

function HeroIllustration() {
  return (
    <div className="relative w-full max-w-lg mx-auto">
      <svg viewBox="0 0 400 300" className="w-full h-auto">
        <defs>
          <linearGradient id="gradientSlate" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#64748b" />
            <stop offset="100%" stopColor="#475569" />
          </linearGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
            <feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge>
          </filter>
        </defs>

        {/* Agency nodes */}
        <g className="animate-pulse" style={{ animationDuration: '3s' }}>
          <rect x="20" y="40" width="80" height="55" rx="8" fill="#1e293b" stroke="url(#gradientSlate)" strokeWidth="2" />
          <text x="60" y="68" textAnchor="middle" fill="#94a3b8" fontSize="9" fontWeight="500">Tax Agency</text>
          <rect x="30" y="82" width="60" height="6" rx="2" fill="#334155" />

          <rect x="20" y="125" width="80" height="55" rx="8" fill="#1e293b" stroke="url(#gradientSlate)" strokeWidth="2" />
          <text x="60" y="153" textAnchor="middle" fill="#94a3b8" fontSize="9" fontWeight="500">Social Svc</text>
          <rect x="30" y="167" width="60" height="6" rx="2" fill="#334155" />

          <rect x="20" y="210" width="80" height="55" rx="8" fill="#1e293b" stroke="url(#gradientSlate)" strokeWidth="2" />
          <text x="60" y="238" textAnchor="middle" fill="#94a3b8" fontSize="9" fontWeight="500">Municipality</text>
          <rect x="30" y="252" width="60" height="6" rx="2" fill="#334155" />
        </g>

        {/* Connection lines */}
        <path d="M100 67 Q140 67 160 115" stroke="url(#gradientSlate)" strokeWidth="2" fill="none" strokeDasharray="5,5" opacity="0.6">
          <animate attributeName="stroke-dashoffset" from="0" to="-20" dur="2s" repeatCount="indefinite"/>
        </path>
        <path d="M100 152 L160 152" stroke="url(#gradientSlate)" strokeWidth="2" fill="none" strokeDasharray="5,5" opacity="0.6">
          <animate attributeName="stroke-dashoffset" from="0" to="-20" dur="2s" repeatCount="indefinite"/>
        </path>
        <path d="M100 237 Q140 237 160 190" stroke="url(#gradientSlate)" strokeWidth="2" fill="none" strokeDasharray="5,5" opacity="0.6">
          <animate attributeName="stroke-dashoffset" from="0" to="-20" dur="2s" repeatCount="indefinite"/>
        </path>

        {/* Central model */}
        <g filter="url(#glow)">
          <rect x="160" y="105" width="100" height="95" rx="12" fill="#1e293b" stroke="#64748b" strokeWidth="2"/>
          <path d="M200 130 L200 140 M195 145 L200 150 L205 145" stroke="white" strokeWidth="2" fill="none"/>
          <path d="M220 130 L220 140 M215 145 L220 150 L225 145" stroke="white" strokeWidth="2" fill="none"/>
          <rect x="185" y="160" width="50" height="25" rx="4" fill="#334155"/>
          <path d="M195 172 L200 177 L210 167" stroke="#10b981" strokeWidth="2" fill="none"/>
          <text x="210" y="193" textAnchor="middle" fill="#64748b" fontSize="7">Cross-Analysis</text>
        </g>

        {/* Output */}
        <path d="M260 152 L310 152" stroke="#10b981" strokeWidth="2" fill="none" strokeDasharray="5,5" opacity="0.6">
          <animate attributeName="stroke-dashoffset" from="-20" to="0" dur="2s" repeatCount="indefinite"/>
        </path>

        <g className="animate-pulse" style={{ animationDuration: '2s', animationDelay: '1s' }}>
          <rect x="310" y="115" width="75" height="75" rx="8" fill="#1e293b" stroke="#10b981" strokeWidth="1.5" />
          <text x="347" y="140" textAnchor="middle" fill="#10b981" fontSize="8">Fraud Detection</text>
          <text x="347" y="158" textAnchor="middle" fill="white" fontSize="14" fontWeight="bold">+300%</text>
          <text x="347" y="175" textAnchor="middle" fill="#94a3b8" fontSize="8">Accuracy</text>
        </g>
      </svg>
    </div>
  )
}

function StatCard({ value, label, icon }) {
  return (
    <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/10 hover:border-slate-400/30 transition-all">
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 bg-slate-500/20 rounded-xl flex items-center justify-center text-2xl">{icon}</div>
        <div>
          <div className="text-3xl font-bold text-white">{value}</div>
          <div className="text-slate-400 text-sm">{label}</div>
        </div>
      </div>
    </div>
  )
}

function ContactForm({ lang }) {
  const [formData, setFormData] = useState({ name: '', email: '', organization: '', phone: '', job_title: '', use_case: '' })
  const [status, setStatus] = useState('idle')

  const t = {
    es: {
      title: 'Solicitar Demo Gobierno',
      subtitle: 'Te mostramos el caso de Córdoba y cómo adaptarlo a tu jurisdicción.',
      name: 'Nombre completo', email: 'Email institucional', organization: 'Organismo',
      phone: 'Teléfono', position: 'Cargo', useCase: 'Caso de uso',
      useCases: ['Fraude fiscal', 'Políticas públicas', 'Ventanilla única', 'Otro'],
      submit: 'Solicitar Demo', sending: 'Enviando...', success: 'Solicitud enviada.',
      error: 'Error al enviar.', also: 'También puedes contactarnos en'
    },
    en: {
      title: 'Request Government Demo',
      subtitle: 'We\'ll show you the Córdoba case and how to adapt it to your jurisdiction.',
      name: 'Full name', email: 'Institutional email', organization: 'Agency',
      phone: 'Phone', position: 'Job title', useCase: 'Use case',
      useCases: ['Tax fraud', 'Public policy', 'Single window', 'Other'],
      submit: 'Request Demo', sending: 'Sending...', success: 'Request sent.',
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
          subject: 'Demo Request - Government - Xcapit Privacy',
          from_name: 'Xcapit Privacy', vertical: 'Government', ...formData
        }),
      })
      if (response.ok) {
        setStatus('success')
        setFormData({ name: '', email: '', organization: '', phone: '', job_title: '', use_case: '' })
      } else setStatus('error')
    } catch { setStatus('error') }
  }

  return (
    <div className="bg-white/10 backdrop-blur-md rounded-2xl p-8 border border-white/20 shadow-2xl">
      <h3 className="text-2xl font-bold text-white mb-2">{t.title}</h3>
      <p className="text-slate-300 mb-6">{t.subtitle}</p>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid md:grid-cols-2 gap-4">
          <input type="text" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} placeholder={t.name} required className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl focus:outline-none focus:border-slate-400 text-white placeholder-slate-400 transition" />
          <input type="email" value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })} placeholder={t.email} required className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl focus:outline-none focus:border-slate-400 text-white placeholder-slate-400 transition" />
        </div>
        <div className="grid md:grid-cols-2 gap-4">
          <input type="text" value={formData.organization} onChange={(e) => setFormData({ ...formData, organization: e.target.value })} placeholder={t.organization} required className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl focus:outline-none focus:border-slate-400 text-white placeholder-slate-400 transition" />
          <input type="tel" value={formData.phone} onChange={(e) => setFormData({ ...formData, phone: e.target.value })} placeholder={t.phone} className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl focus:outline-none focus:border-slate-400 text-white placeholder-slate-400 transition" />
        </div>
        <input type="text" value={formData.job_title} onChange={(e) => setFormData({ ...formData, job_title: e.target.value })} placeholder={t.position} required className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl focus:outline-none focus:border-slate-400 text-white placeholder-slate-400 transition" />
        <select value={formData.use_case} onChange={(e) => setFormData({ ...formData, use_case: e.target.value })} required className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl focus:outline-none focus:border-slate-400 text-white placeholder-slate-400 transition appearance-none cursor-pointer">
          <option value="" className="bg-slate-800">{t.useCase}</option>
          {t.useCases.map(uc => <option key={uc} value={uc} className="bg-slate-800">{uc}</option>)}
        </select>
        <button type="submit" disabled={status === 'sending'} className="w-full bg-gradient-to-r from-slate-600 to-slate-700 text-white py-4 px-6 rounded-xl font-semibold hover:from-slate-700 hover:to-slate-800 transition disabled:opacity-50 shadow-lg">
          {status === 'sending' ? t.sending : t.submit}
        </button>
        {status === 'success' && <p className="text-green-400 text-center font-medium">{t.success}</p>}
        {status === 'error' && <p className="text-red-400 text-center font-medium">{t.error}</p>}
      </form>
      <p className="mt-6 text-center text-sm text-slate-400">{t.also}{' '}<a href="mailto:consorcios@xcapit.com" className="text-slate-300 font-medium hover:underline">consorcios@xcapit.com</a></p>
    </div>
  )
}

function UseCaseCard({ title, problem, solution, metric, realCase, lang, icon }) {
  return (
    <div className="group bg-white rounded-2xl p-8 border border-slate-200 hover:shadow-2xl hover:shadow-slate-500/10 hover:-translate-y-1 transition-all duration-300">
      <div className="w-14 h-14 bg-slate-100 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">{icon}</div>
      <h3 className="text-xl font-bold text-slate-900 mb-4">{title}</h3>
      <div className="mb-4">
        <span className="inline-flex items-center gap-1.5 text-sm font-semibold text-red-600 uppercase tracking-wider">
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" /></svg>
          {lang === 'es' ? 'El Problema' : 'The Problem'}
        </span>
        <p className="text-slate-600 mt-2">{problem}</p>
      </div>
      <div className="mb-4">
        <span className="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-600 uppercase tracking-wider">
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" /></svg>
          {lang === 'es' ? 'La Solución' : 'The Solution'}
        </span>
        <p className="text-slate-600 mt-2">{solution}</p>
      </div>
      {realCase && (
        <div className="mb-4 p-3 bg-amber-50 rounded-lg border border-amber-200">
          <span className="text-xs font-semibold text-amber-700 uppercase tracking-wider">{lang === 'es' ? 'Caso Real' : 'Real Case'}</span>
          <p className="text-amber-800 text-sm mt-1">{realCase}</p>
        </div>
      )}
      <div className="mt-6 pt-4 border-t border-slate-100">
        <span className="text-3xl font-bold bg-gradient-to-r from-slate-700 to-slate-900 bg-clip-text text-transparent">{metric}</span>
      </div>
    </div>
  )
}

function StepCard({ number, title, description }) {
  return (
    <div className="relative group">
      <div className="absolute -inset-0.5 bg-gradient-to-r from-slate-500 to-slate-600 rounded-2xl blur opacity-0 group-hover:opacity-30 transition duration-500" />
      <div className="relative bg-white rounded-2xl p-8 border border-slate-200">
        <div className="w-12 h-12 bg-gradient-to-br from-slate-600 to-slate-700 rounded-xl flex items-center justify-center text-white font-bold text-lg mb-4">{number}</div>
        <h3 className="text-xl font-bold text-slate-900 mb-2">{title}</h3>
        <p className="text-slate-600">{description}</p>
      </div>
    </div>
  )
}

export default function LandingGobierno() {
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
      nav: { casosUso: 'Casos de Uso', comoFunciona: 'Cómo Funciona', piloto: 'Caso Córdoba', demo: 'Demo' },
      hero: {
        badge: 'Gobierno y Sector Público',
        headline: 'Colaboración inter-agencias',
        highlight: 'sin violar la privacidad ciudadana.',
        subheadline: 'Las agencias gubernamentales pueden cruzar datos para detectar fraude, mejorar políticas públicas y optimizar servicios. Sin centralizar información sensible.',
        cta: 'Solicitar Demo', ctaSecondary: 'Ver caso piloto',
        stats: { fraud: { value: '+300%', label: 'Detección fraude' }, time: { value: '-70%', label: 'Tiempo trámites' }, compliance: { value: '100%', label: 'Compliant' } }
      },
      trustedBy: { title: 'Caso piloto activo', partners: ['DGR Córdoba', 'Desarrollo Social', 'CIDI', 'Municipalidad'] },
      problem: {
        title: 'Los datos que necesitas existen. En otra agencia.',
        points: [
          { title: 'Silos por diseño legal', desc: 'Cada agencia tiene datos parciales. Cruzarlos detectaría fraude masivo. Pero la ley prohíbe compartir.', icon: '🔒' },
          { title: 'Políticas públicas a ciegas', desc: 'Diseñas programas sin saber a quién llegan. ¿Hay duplicación? Para responder necesitas datos que no puedes pedir.', icon: '📊' },
          { title: 'El costo de la fragmentación', desc: 'El ciudadano presenta los mismos documentos en 5 ventanillas. Millones de horas desperdiciadas.', icon: '📋' }
        ]
      },
      solution: {
        title: 'Colaboración real sin centralización',
        desc: 'Con cifrado homomórfico, cada agencia mantiene sus datos. Solo comparten versiones cifradas que permiten análisis cruzados.',
        steps: [
          { title: 'Cada agencia cifra', desc: 'Los datos sensibles se cifran localmente con clave propia.' },
          { title: 'Análisis cruzado', desc: 'El modelo analiza datos cifrados de múltiples agencias.' },
          { title: 'Resultados sin exposición', desc: 'Cada agencia recibe solo lo que necesita saber.' }
        ]
      },
      useCases: {
        title: 'Casos de Uso',
        cases: [
          { title: 'Fraude Fiscal Inter-Agencias', problem: 'Un contribuyente declara bajos ingresos mientras recibe transferencias millonarias.', solution: 'Análisis de inconsistencias entre Rentas, movimientos bancarios y beneficios sociales.', metric: '+300% detección', realCase: 'Piloto con Gobierno de Córdoba: DGR, Ministerio de Desarrollo Social, CIDI colaborando.' },
          { title: 'Políticas Públicas Inteligentes', problem: 'Diseñas un programa de vivienda sin saber cuántos ya tienen vivienda.', solution: 'Modelos que cruzan datos para identificar brechas y duplicaciones.', metric: '-45% duplicación', realCase: null },
          { title: 'Ventanilla Única Sin Centralización', problem: 'El ciudadano presenta los mismos documentos porque cada agencia no confía en otras.', solution: 'Verificación distribuida donde cada agencia confirma datos sin revelarlos.', metric: '-70% tiempo', realCase: null }
        ]
      },
      compliance: {
        title: 'Cumplimiento normativo sin excepciones legales',
        desc: 'No necesitas decretos especiales. El cifrado homomórfico permite colaboración sin transferencia de datos.',
        badges: ['Habeas Data', 'Ley de Acceso a la Información', 'LGPD/GDPR', 'Secreto Fiscal']
      },
      pilot: {
        title: 'Caso Real: Piloto con Gobierno de Córdoba',
        desc: 'Implementación activa con 4 organismos para detección de fraude fiscal:',
        participants: [
          { name: 'DGR (Dirección General de Rentas)', power: '35%', data: 'Datos tributarios' },
          { name: 'Ministerio de Desarrollo Social', power: '30%', data: 'Beneficios sociales' },
          { name: 'CIDI (Ciudadano Digital)', power: '25%', data: 'Identidad y verificación' },
          { name: 'Municipalidad de Córdoba', power: '10%', data: 'Registros locales' }
        ],
        features: ['Dashboard de gobernanza con votación', 'Registro de contribuciones en blockchain', 'Compliance automático verificado', 'Modelo de detección de inconsistencias']
      },
      cta: { title: '¿Listo para colaboración inter-agencias sin romper silos?', subtitle: 'Agenda una demo con nuestro equipo especializado en sector público.' },
      footer: { product: 'Producto', contact: 'Contacto', rights: '© 2025 Xcapit Privacy. Todos los derechos reservados.', links: { industries: 'Otras industrias', github: 'GitHub' } }
    },
    en: {
      nav: { casosUso: 'Use Cases', comoFunciona: 'How it Works', piloto: 'Córdoba Case', demo: 'Demo' },
      hero: {
        badge: 'Government & Public Sector',
        headline: 'Cross-agency collaboration',
        highlight: 'without violating citizen privacy.',
        subheadline: 'Government agencies can cross-reference data to detect fraud, improve public policy, and optimize services. Without centralizing sensitive information.',
        cta: 'Request Demo', ctaSecondary: 'See pilot case',
        stats: { fraud: { value: '+300%', label: 'Fraud detection' }, time: { value: '-70%', label: 'Processing time' }, compliance: { value: '100%', label: 'Compliant' } }
      },
      trustedBy: { title: 'Active pilot case', partners: ['DGR Córdoba', 'Social Development', 'CIDI', 'Municipality'] },
      problem: {
        title: 'The data you need exists. At another agency.',
        points: [
          { title: 'Silos by legal design', desc: 'Each agency has partial data. Crossing them would detect massive fraud. But the law forbids sharing.', icon: '🔒' },
          { title: 'Blind public policy', desc: 'You design programs without knowing who they reach. Is there duplication? To answer you need data you can\'t request.', icon: '📊' },
          { title: 'The cost of fragmentation', desc: 'Citizens submit the same documents at 5 windows. Millions of hours wasted.', icon: '📋' }
        ]
      },
      solution: {
        title: 'Real collaboration without centralization',
        desc: 'With homomorphic encryption, each agency keeps its data. They only share encrypted versions that enable cross-analysis.',
        steps: [
          { title: 'Each agency encrypts', desc: 'Sensitive data is encrypted locally with own key.' },
          { title: 'Cross-analysis', desc: 'Model analyzes encrypted data from multiple agencies.' },
          { title: 'Results without exposure', desc: 'Each agency receives only what it needs to know.' }
        ]
      },
      useCases: {
        title: 'Use Cases',
        cases: [
          { title: 'Cross-Agency Tax Fraud', problem: 'A taxpayer reports low income while receiving millions in transfers.', solution: 'Inconsistency analysis between Tax, bank movements, and social benefits.', metric: '+300% detection', realCase: 'Pilot with Córdoba Government: DGR, Ministry of Social Development, CIDI collaborating.' },
          { title: 'Data-Driven Public Policy', problem: 'You design a housing program without knowing how many already have housing.', solution: 'Models that cross data to identify gaps and duplications.', metric: '-45% duplication', realCase: null },
          { title: 'True Single Window', problem: 'Citizens submit same documents because each agency doesn\'t trust others.', solution: 'Distributed verification where each agency confirms data without revealing it.', metric: '-70% time', realCase: null }
        ]
      },
      compliance: {
        title: 'Regulatory compliance without legal exceptions',
        desc: 'You don\'t need special decrees. Homomorphic encryption enables collaboration without data transfer.',
        badges: ['Habeas Data', 'Freedom of Information', 'LGPD/GDPR', 'Tax Secrecy']
      },
      pilot: {
        title: 'Real Case: Córdoba Government Pilot',
        desc: 'Active implementation with 4 agencies for tax fraud detection:',
        participants: [
          { name: 'DGR (General Tax Directorate)', power: '35%', data: 'Tax data' },
          { name: 'Ministry of Social Development', power: '30%', data: 'Social benefits' },
          { name: 'CIDI (Digital Citizen)', power: '25%', data: 'Identity and verification' },
          { name: 'Municipality of Córdoba', power: '10%', data: 'Local records' }
        ],
        features: ['Governance dashboard with voting', 'Blockchain contribution registry', 'Automatic compliance verification', 'Inconsistency detection model']
      },
      cta: { title: 'Ready for cross-agency collaboration without breaking silos?', subtitle: 'Book a demo with our public sector team.' },
      footer: { product: 'Product', contact: 'Contact', rights: '© 2025 Xcapit Privacy. All rights reserved.', links: { industries: 'Other industries', github: 'GitHub' } }
    }
  }

  const t = content[lang]
  const useCaseIcons = [
    <svg key="fraud" className="w-7 h-7 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>,
    <svg key="policy" className="w-7 h-7 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>,
    <svg key="window" className="w-7 h-7 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>
  ]

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Navigation */}
      <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${scrolled ? 'bg-slate-900/95 backdrop-blur-md shadow-lg' : 'bg-transparent'}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link to="/hub" className="flex items-center group">
              <div className="w-10 h-10 bg-gradient-to-br from-slate-600 to-slate-700 rounded-xl flex items-center justify-center mr-2 group-hover:scale-105 transition-transform">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
              </div>
              <span className="text-xl font-bold text-white">Xcapit</span>
              <span className="text-xl font-light text-slate-400 ml-1">Privacy</span>
            </Link>
            <div className="hidden md:flex items-center gap-6">
              <a href="#use-cases" className="text-slate-300 hover:text-white font-medium transition">{t.nav.casosUso}</a>
              <a href="#how-it-works" className="text-slate-300 hover:text-white font-medium transition">{t.nav.comoFunciona}</a>
              <a href="#pilot" className="text-slate-300 hover:text-white font-medium transition">{t.nav.piloto}</a>
            </div>
            <div className="flex items-center gap-3">
              <LanguageSwitcher variant="toggle" />
              <a href="#contact" className="bg-gradient-to-r from-slate-600 to-slate-700 text-white px-5 py-2.5 rounded-lg font-medium hover:from-slate-700 hover:to-slate-800 transition shadow-lg">{t.hero.cta}</a>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center pt-16 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800" />
        <div className="absolute inset-0">
          <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-slate-600/10 rounded-full blur-3xl" />
          <div className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] bg-slate-500/10 rounded-full blur-3xl" />
        </div>
        <ParticleBackground />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <div className="inline-flex items-center gap-2 bg-white/5 backdrop-blur-sm px-4 py-2 rounded-full mb-8 border border-white/10">
                <span className="text-2xl">🏛️</span>
                <span className="text-white/90 text-sm font-medium">{t.hero.badge}</span>
              </div>

              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-6 leading-tight">
                {t.hero.headline}<br />
                <span className="bg-gradient-to-r from-slate-300 via-slate-200 to-white bg-clip-text text-transparent">{t.hero.highlight}</span>
              </h1>

              <p className="text-lg lg:text-xl text-slate-300 mb-8 max-w-xl leading-relaxed">{t.hero.subheadline}</p>

              <div className="flex flex-col sm:flex-row gap-4 mb-12">
                <a href="#contact" className="inline-flex items-center justify-center gap-3 bg-white text-slate-900 px-8 py-4 rounded-xl font-semibold hover:bg-slate-100 transition text-lg shadow-2xl">
                  {t.hero.cta}
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" /></svg>
                </a>
                <a href="#pilot" className="inline-flex items-center justify-center gap-2 bg-white/5 backdrop-blur-sm text-white px-8 py-4 rounded-xl font-semibold hover:bg-white/10 transition text-lg border border-white/10">{t.hero.ctaSecondary}</a>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <StatCard value={t.hero.stats.fraud.value} label={t.hero.stats.fraud.label} icon="📈" />
                <StatCard value={t.hero.stats.time.value} label={t.hero.stats.time.label} icon="⏱️" />
                <StatCard value={t.hero.stats.compliance.value} label={t.hero.stats.compliance.label} icon="✓" />
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

      {/* Use Cases Section */}
      <section id="use-cases" className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4">{t.useCases.title}</h2>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {t.useCases.cases.map((useCase, index) => (
              <UseCaseCard key={index} title={useCase.title} problem={useCase.problem} solution={useCase.solution} metric={useCase.metric} realCase={useCase.realCase} lang={lang} icon={useCaseIcons[index]} />
            ))}
          </div>
        </div>
      </section>

      {/* Pilot Section */}
      <section id="pilot" className="py-24 bg-slate-50">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <span className="inline-block px-4 py-1 bg-amber-100 text-amber-800 rounded-full text-sm font-semibold mb-4">{lang === 'es' ? 'CASO REAL' : 'REAL CASE'}</span>
            <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4">{t.pilot.title}</h2>
            <p className="text-xl text-slate-600">{t.pilot.desc}</p>
          </div>
          <div className="bg-white rounded-2xl p-8 border border-slate-200 mb-8 shadow-lg">
            <h3 className="font-semibold text-slate-900 mb-4">{lang === 'es' ? 'Participantes' : 'Participants'}</h3>
            <div className="space-y-3">
              {t.pilot.participants.map((p, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                  <div><span className="font-medium text-slate-900">{p.name}</span><span className="text-slate-500 text-sm ml-2">- {p.data}</span></div>
                  <span className="text-sm font-semibold text-slate-700 bg-slate-200 px-3 py-1 rounded-full">{p.power}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="grid md:grid-cols-2 gap-4">
            {t.pilot.features.map((feature, index) => (
              <div key={index} className="flex items-center gap-3 bg-emerald-50 p-4 rounded-xl border border-emerald-200">
                <svg className="w-5 h-5 text-emerald-600 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                <span className="text-emerald-800 font-medium">{feature}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Compliance Section */}
      <section className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4">{t.compliance.title}</h2>
            <p className="text-xl text-slate-600 max-w-3xl mx-auto">{t.compliance.desc}</p>
          </div>
          <div className="flex flex-wrap justify-center gap-4">
            {t.compliance.badges.map((badge, index) => (
              <div key={index} className="flex items-center gap-2 bg-slate-100 border border-slate-200 px-6 py-3 rounded-full hover:scale-105 transition-transform">
                <svg className="w-5 h-5 text-slate-700" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                <span className="font-semibold text-slate-800">{badge}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Contact Section */}
      <section id="contact" className="py-24 bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 relative overflow-hidden">
        <div className="absolute inset-0">
          <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-slate-600/10 rounded-full blur-3xl" />
          <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-slate-500/10 rounded-full blur-3xl" />
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
              <div className="w-10 h-10 bg-gradient-to-br from-slate-600 to-slate-700 rounded-xl flex items-center justify-center mr-2">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
              </div>
              <span className="text-xl font-bold text-white">Xcapit</span>
              <span className="text-xl font-light text-slate-400 ml-1">Privacy</span>
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
