import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import LanguageSwitcher from '../components/LanguageSwitcher'

// Animated Counter Component
function AnimatedCounter({ end, duration = 2000, suffix = '', prefix = '' }) {
  const [count, setCount] = useState(0)

  useEffect(() => {
    let startTime = null
    const animate = (currentTime) => {
      if (!startTime) startTime = currentTime
      const progress = Math.min((currentTime - startTime) / duration, 1)
      setCount(Math.floor(progress * end))
      if (progress < 1) {
        requestAnimationFrame(animate)
      }
    }
    requestAnimationFrame(animate)
  }, [end, duration])

  return <span>{prefix}{count.toLocaleString()}{suffix}</span>
}

// FAQ Accordion Component
function FAQItem({ question, answer, isOpen, onClick }) {
  return (
    <div className="border-b border-slate-200 last:border-0">
      <button
        onClick={onClick}
        className="w-full py-5 flex items-center justify-between text-left hover:text-brand-600 transition"
      >
        <span className="text-lg font-medium text-slate-900">{question}</span>
        <svg
          className={`w-5 h-5 text-slate-500 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      <div className={`overflow-hidden transition-all duration-300 ${isOpen ? 'max-h-96 pb-5' : 'max-h-0'}`}>
        <p className="text-slate-600">{answer}</p>
      </div>
    </div>
  )
}

// Contact Form Component
function ContactForm() {
  const { t } = useTranslation()
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    company: '',
    phone: '',
    job_title: '',
    industry: '',
    use_case: '',
    message: ''
  })
  const [status, setStatus] = useState('idle')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setStatus('sending')

    try {
      const response = await fetch('https://api.web3forms.com/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          access_key: 'd7f419bc-95cf-498d-8d8b-5f4830622bf4',
          subject: 'Nueva solicitud - Xcapit Privacy',
          from_name: 'Xcapit Privacy',
          ...formData
        }),
      })

      if (response.ok) {
        setStatus('success')
        setFormData({
          name: '', email: '', company: '', phone: '',
          job_title: '', industry: '', use_case: '', message: ''
        })
      } else {
        setStatus('error')
      }
    } catch (err) {
      setStatus('error')
    }
  }

  const industries = [
    t('landing.contact.industries.financial'),
    t('landing.contact.industries.health'),
    t('landing.contact.industries.insurance'),
    t('landing.contact.industries.government'),
    t('landing.contact.industries.technology'),
    t('landing.contact.industries.retail'),
    t('landing.contact.industries.logistics'),
    t('landing.contact.industries.telecom'),
    t('landing.contact.industries.other')
  ]

  const useCasesOptions = [
    t('landing.contact.useCases.fraud'),
    t('landing.contact.useCases.credit'),
    t('landing.contact.useCases.medical'),
    t('landing.contact.useCases.segmentation'),
    t('landing.contact.useCases.demand'),
    t('landing.contact.useCases.other')
  ]

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-xl shadow-slate-200/50 p-8 border border-slate-100">
      <div className="grid md:grid-cols-2 gap-5 mb-5">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1.5">
            {t('landing.contact.fullName')} *
          </label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20 transition bg-slate-50 focus:bg-white"
            placeholder={t('landing.contact.namePlaceholder')}
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1.5">
            {t('landing.contact.company')} *
          </label>
          <input
            type="text"
            value={formData.company}
            onChange={(e) => setFormData({ ...formData, company: e.target.value })}
            className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20 transition bg-slate-50 focus:bg-white"
            placeholder={t('landing.contact.companyPlaceholder')}
            required
          />
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-5 mb-5">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1.5">
            {t('landing.contact.corporateEmail')} *
          </label>
          <input
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20 transition bg-slate-50 focus:bg-white"
            placeholder={t('landing.contact.emailPlaceholder')}
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1.5">
            {t('landing.contact.phone')}
          </label>
          <input
            type="tel"
            value={formData.phone}
            onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
            className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20 transition bg-slate-50 focus:bg-white"
            placeholder="+54 11 1234-5678"
          />
        </div>
      </div>

      <div className="mb-5">
        <label className="block text-sm font-medium text-slate-700 mb-1.5">
          {t('landing.contact.position')} *
        </label>
        <input
          type="text"
          value={formData.job_title}
          onChange={(e) => setFormData({ ...formData, job_title: e.target.value })}
          className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20 transition bg-slate-50 focus:bg-white"
          placeholder={t('landing.contact.positionPlaceholder')}
          required
        />
      </div>

      <div className="grid md:grid-cols-2 gap-5 mb-5">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1.5">
            {t('landing.contact.industry')} *
          </label>
          <select
            value={formData.industry}
            onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
            className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20 transition bg-slate-50 focus:bg-white appearance-none cursor-pointer"
            required
          >
            <option value="">{t('landing.contact.selectIndustry')}</option>
            {industries.map(ind => (
              <option key={ind} value={ind}>{ind}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1.5">
            {t('landing.contact.useCase')} *
          </label>
          <select
            value={formData.use_case}
            onChange={(e) => setFormData({ ...formData, use_case: e.target.value })}
            className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20 transition bg-slate-50 focus:bg-white appearance-none cursor-pointer"
            required
          >
            <option value="">{t('landing.contact.selectUseCase')}</option>
            {useCasesOptions.map(uc => (
              <option key={uc} value={uc}>{uc}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="mb-6">
        <label className="block text-sm font-medium text-slate-700 mb-1.5">
          {t('landing.contact.tellUsMore')}
        </label>
        <textarea
          value={formData.message}
          onChange={(e) => setFormData({ ...formData, message: e.target.value })}
          rows={4}
          className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20 transition bg-slate-50 focus:bg-white resize-none"
          placeholder={t('landing.contact.messagePlaceholder')}
        />
      </div>

      <button
        type="submit"
        disabled={status === 'sending'}
        className="w-full bg-gradient-to-r from-brand-600 to-indigo-600 text-white py-4 px-6 rounded-xl font-semibold hover:from-brand-700 hover:to-indigo-700 transition disabled:opacity-50 flex items-center justify-center gap-2 shadow-lg shadow-brand-600/25"
      >
        {status === 'sending' ? (
          <>
            <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {t('landing.contact.sending')}
          </>
        ) : (
          <>
            {t('landing.contact.requestInfo')}
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
          </>
        )}
      </button>

      {status === 'success' && (
        <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-xl flex items-center gap-3">
          <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-green-700 font-medium">{t('landing.contact.successMessage')}</p>
        </div>
      )}
      {status === 'error' && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl flex items-center gap-3">
          <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-red-700 font-medium">{t('landing.contact.errorMessage')}</p>
        </div>
      )}

      <div className="mt-6 pt-6 border-t border-slate-100 text-center">
        <p className="text-sm text-slate-500">
          {t('landing.contact.alsoContact')}{' '}
          <a href="mailto:consorcios@xcapit.com" className="text-brand-600 font-medium hover:text-brand-700">
            consorcios@xcapit.com
          </a>
        </p>
      </div>
    </form>
  )
}

export default function Landing() {
  const { t, i18n } = useTranslation()
  const currentLang = i18n.language?.startsWith('es') ? 'es' : i18n.language?.startsWith('de') ? 'de' : 'en'
  const [openFAQ, setOpenFAQ] = useState(0)
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 50)
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const stats = [
    { value: 566, suffix: '+', label: currentLang === 'es' ? 'Tests Pasando' : currentLang === 'de' ? 'Bestandene Tests' : 'Tests Passing' },
    { value: 100, suffix: '%', label: currentLang === 'es' ? 'Privacidad de Datos' : currentLang === 'de' ? 'Datenschutz' : 'Data Privacy' },
    { value: 5, suffix: '', label: currentLang === 'es' ? 'Modelos ML' : currentLang === 'de' ? 'ML-Modelle' : 'ML Models' },
    { value: 128, suffix: '-bit', label: currentLang === 'es' ? 'Encriptación' : currentLang === 'de' ? 'Verschlüsselung' : 'Encryption' },
  ]

  const features = [
    {
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
      ),
      title: t('landing.features.encrypted.title'),
      description: t('landing.features.encrypted.description'),
      gradient: 'from-purple-500 to-indigo-500'
    },
    {
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
      ),
      title: t('landing.features.privateML.title'),
      description: t('landing.features.privateML.description'),
      gradient: 'from-amber-500 to-orange-500'
    },
    {
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      ),
      title: t('landing.features.secureCollab.title'),
      description: t('landing.features.secureCollab.description'),
      gradient: 'from-emerald-500 to-teal-500'
    },
    {
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      ),
      title: currentLang === 'es' ? 'Compliance Automático' : currentLang === 'de' ? 'Auto-Compliance' : 'Auto Compliance',
      description: currentLang === 'es'
        ? 'GDPR, HIPAA, SOC2 y PCI-DSS verificados automáticamente con reportes en tiempo real.'
        : currentLang === 'de'
        ? 'DSGVO, HIPAA, SOC2 und PCI-DSS automatisch verifiziert mit Echtzeit-Berichten.'
        : 'GDPR, HIPAA, SOC2, and PCI-DSS automatically verified with real-time reports.',
      gradient: 'from-blue-500 to-cyan-500'
    },
    {
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
        </svg>
      ),
      title: currentLang === 'es' ? 'Gobernanza Blockchain' : currentLang === 'de' ? 'Blockchain-Governance' : 'Blockchain Governance',
      description: currentLang === 'es'
        ? 'Votación descentralizada, pruebas de contribución y distribución justa de ingresos en Arbitrum.'
        : currentLang === 'de'
        ? 'Dezentrale Abstimmung, Beitragsnachweise und faire Einnahmenverteilung auf Arbitrum.'
        : 'Decentralized voting, contribution proofs, and fair revenue distribution on Arbitrum.',
      gradient: 'from-rose-500 to-pink-500'
    },
    {
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
      title: currentLang === 'es' ? 'Inferencia Federada' : currentLang === 'de' ? 'Föderierte Inferenz' : 'Federated Inference',
      description: currentLang === 'es'
        ? 'Predicciones en el edge sin mover datos. Los modelos van a los datos, no al revés.'
        : currentLang === 'de'
        ? 'Edge-Vorhersagen ohne Datentransfer. Die Modelle kommen zu den Daten, nicht umgekehrt.'
        : 'Edge predictions without moving data. Models go to data, not the other way around.',
      gradient: 'from-violet-500 to-purple-500'
    },
  ]

  const useCases = [
    {
      icon: '🏦',
      title: currentLang === 'es' ? 'Servicios Financieros' : currentLang === 'de' ? 'Finanzdienstleistungen' : 'Financial Services',
      description: currentLang === 'es'
        ? 'Detección de fraude colaborativa entre bancos sin compartir datos de clientes.'
        : currentLang === 'de'
        ? 'Kollaborative Betrugserkennung zwischen Banken ohne Weitergabe von Kundendaten.'
        : 'Collaborative fraud detection across banks without sharing customer data.',
      examples: currentLang === 'es'
        ? ['Scoring crediticio multi-banco', 'Detección de lavado de dinero', 'Prevención de fraude']
        : currentLang === 'de'
        ? ['Multi-Bank-Kreditbewertung', 'Geldwäsche-Erkennung', 'Betrugsprävention']
        : ['Multi-bank credit scoring', 'AML detection', 'Fraud prevention'],
      color: 'blue',
      link: '/fintech'
    },
    {
      icon: '🏥',
      title: currentLang === 'es' ? 'Salud' : currentLang === 'de' ? 'Gesundheitswesen' : 'Healthcare',
      description: currentLang === 'es'
        ? 'Investigación médica colaborativa cumpliendo HIPAA sin exponer datos de pacientes.'
        : currentLang === 'de'
        ? 'Kollaborative medizinische Forschung HIPAA-konform ohne Offenlegung von Patientendaten.'
        : 'Collaborative medical research compliant with HIPAA without exposing patient data.',
      examples: currentLang === 'es'
        ? ['Predicción de riesgo de enfermedades', 'Descubrimiento de medicamentos', 'Estudios clínicos']
        : currentLang === 'de'
        ? ['Krankheitsrisiko-Vorhersage', 'Medikamentenentdeckung', 'Klinische Studien']
        : ['Disease risk prediction', 'Drug discovery', 'Clinical trials'],
      color: 'emerald',
      link: '/healthcare'
    },
    {
      icon: '🛡️',
      title: currentLang === 'es' ? 'Seguros' : currentLang === 'de' ? 'Versicherungen' : 'Insurance',
      description: currentLang === 'es'
        ? 'Modelos actuariales compartidos que mejoran la precisión sin revelar portafolios.'
        : currentLang === 'de'
        ? 'Geteilte aktuarielle Modelle für bessere Genauigkeit ohne Portfolio-Offenlegung.'
        : 'Shared actuarial models improving accuracy without revealing portfolios.',
      examples: currentLang === 'es'
        ? ['Pricing dinámico', 'Detección de fraude de siniestros', 'Análisis de riesgo']
        : currentLang === 'de'
        ? ['Dynamische Preisgestaltung', 'Schadensbetrug-Erkennung', 'Risikoanalyse']
        : ['Dynamic pricing', 'Claims fraud detection', 'Risk analysis'],
      color: 'amber',
      link: '/industrias'
    },
    {
      icon: '🏛️',
      title: currentLang === 'es' ? 'Gobierno' : currentLang === 'de' ? 'Regierung' : 'Government',
      description: currentLang === 'es'
        ? 'Análisis de datos sensibles entre agencias manteniendo privacidad ciudadana.'
        : currentLang === 'de'
        ? 'Behördenübergreifende Analyse sensibler Daten unter Wahrung des Bürgerdatenschutzes.'
        : 'Cross-agency sensitive data analysis while maintaining citizen privacy.',
      examples: currentLang === 'es'
        ? ['Detección de fraude fiscal', 'Análisis de seguridad', 'Políticas públicas']
        : currentLang === 'de'
        ? ['Steuerbetrug-Erkennung', 'Sicherheitsanalyse', 'Öffentliche Politik']
        : ['Tax fraud detection', 'Security analysis', 'Public policy'],
      color: 'slate',
      link: '/gobierno'
    },
  ]

  const comparison = [
    { feature: currentLang === 'es' ? 'ML sobre datos encriptados' : currentLang === 'de' ? 'ML auf verschlüsselten Daten' : 'ML on encrypted data', xcapit: true, traditional: false, mpc: 'partial' },
    { feature: currentLang === 'es' ? 'Gobernanza blockchain' : currentLang === 'de' ? 'Blockchain-Governance' : 'Blockchain governance', xcapit: true, traditional: false, mpc: false },
    { feature: currentLang === 'es' ? 'Marketplace de modelos' : currentLang === 'de' ? 'Modell-Marktplatz' : 'Model marketplace', xcapit: true, traditional: false, mpc: false },
    { feature: currentLang === 'es' ? 'Compliance automático' : currentLang === 'de' ? 'Auto-Compliance' : 'Auto compliance', xcapit: true, traditional: 'partial', mpc: false },
    { feature: currentLang === 'es' ? 'Sin confianza en terceros' : currentLang === 'de' ? 'Zero-Trust Drittparteien' : 'Zero trust third party', xcapit: true, traditional: false, mpc: true },
    { feature: currentLang === 'es' ? 'Explicabilidad del modelo' : currentLang === 'de' ? 'Modell-Erklärbarkeit' : 'Model explainability', xcapit: true, traditional: true, mpc: false },
    { feature: currentLang === 'es' ? 'Inferencia federada' : currentLang === 'de' ? 'Föderierte Inferenz' : 'Federated inference', xcapit: true, traditional: false, mpc: 'partial' },
    { feature: 'Open Source', xcapit: true, traditional: 'partial', mpc: 'partial' },
  ]

  const testimonials = [
    {
      quote: currentLang === 'es'
        ? "La plataforma nos permitió colaborar con competidores en detección de fraude sin comprometer datos de clientes. Revolucionario."
        : currentLang === 'de'
        ? "Die Plattform ermöglichte uns die Zusammenarbeit mit Wettbewerbern bei der Betrugserkennung ohne Kompromittierung von Kundendaten. Revolutionär."
        : "The platform allowed us to collaborate with competitors on fraud detection without compromising customer data. Revolutionary.",
      author: "CTO, Financial Services",
      company: currentLang === 'es' ? "Banco Regional" : currentLang === 'de' ? "Regionalbank" : "Regional Bank",
      avatar: "👤"
    },
    {
      quote: currentLang === 'es'
        ? "Finalmente podemos hacer investigación multi-hospital cumpliendo HIPAA. Los resultados son tan precisos como con datos en claro."
        : currentLang === 'de'
        ? "Endlich können wir Multi-Krankenhaus-Forschung HIPAA-konform durchführen. Die Ergebnisse sind genauso präzise wie mit Klartextdaten."
        : "We can finally do multi-hospital research while complying with HIPAA. Results are as accurate as with plaintext data.",
      author: "Chief Data Officer",
      company: currentLang === 'es' ? "Red de Hospitales" : currentLang === 'de' ? "Krankenhausnetzwerk" : "Hospital Network",
      avatar: "👤"
    },
    {
      quote: currentLang === 'es'
        ? "La gobernanza descentralizada resolvió nuestros problemas de confianza. Cada participante tiene control total sobre sus contribuciones."
        : currentLang === 'de'
        ? "Die dezentrale Governance löste unsere Vertrauensprobleme. Jeder Teilnehmer hat volle Kontrolle über seine Beiträge."
        : "Decentralized governance solved our trust issues. Every participant has full control over their contributions.",
      author: "VP of Data",
      company: currentLang === 'es' ? "Aseguradora Global" : currentLang === 'de' ? "Globale Versicherung AG" : "Global Insurance Co.",
      avatar: "👤"
    },
  ]

  const faqs = [
    {
      question: currentLang === 'es'
        ? "¿Qué tan seguro es el cifrado homomórfico?"
        : currentLang === 'de'
        ? "Wie sicher ist homomorphe Verschlüsselung?"
        : "How secure is homomorphic encryption?",
      answer: currentLang === 'es'
        ? "Usamos CKKS con 128-bit de seguridad, el mismo nivel usado por instituciones financieras y gobiernos. Los datos nunca se descifran durante el procesamiento - las operaciones matemáticas se realizan directamente sobre los datos encriptados."
        : currentLang === 'de'
        ? "Wir verwenden CKKS mit 128-Bit-Sicherheit, das gleiche Niveau wie Finanzinstitute und Regierungen. Daten werden während der Verarbeitung nie entschlüsselt - mathematische Operationen werden direkt auf verschlüsselten Daten ausgeführt."
        : "We use CKKS with 128-bit security, the same level used by financial institutions and governments. Data is never decrypted during processing - mathematical operations are performed directly on encrypted data."
    },
    {
      question: currentLang === 'es'
        ? "¿Cuál es el impacto en performance?"
        : currentLang === 'de'
        ? "Wie wirkt sich das auf die Leistung aus?"
        : "What's the performance impact?",
      answer: currentLang === 'es'
        ? "FHE es más lento que computación en claro (típicamente 10-100x), pero usamos batch processing y optimizaciones que hacen viable el uso en producción. Para casos donde la privacidad es crítica, el trade-off es aceptable."
        : currentLang === 'de'
        ? "FHE ist langsamer als Klartextberechnung (typischerweise 10-100x), aber wir nutzen Batch-Processing und Optimierungen für produktionstauglichen Einsatz. Für datenschutzkritische Fälle ist der Trade-off akzeptabel."
        : "FHE is slower than plaintext computation (typically 10-100x), but we use batch processing and optimizations that make production use viable. For cases where privacy is critical, the trade-off is acceptable."
    },
    {
      question: currentLang === 'es'
        ? "¿Qué algoritmos de ML soportan?"
        : currentLang === 'de'
        ? "Welche ML-Algorithmen werden unterstützt?"
        : "Which ML algorithms do you support?",
      answer: currentLang === 'es'
        ? "Actualmente: Regresión Lineal, Regresión Logística, Árboles de Decisión, KMeans y Ensemble de modelos. Estamos trabajando en soporte para redes neuronales básicas."
        : currentLang === 'de'
        ? "Aktuell: Lineare Regression, Logistische Regression, Entscheidungsbäume, KMeans und Modell-Ensembles. Wir arbeiten an der Unterstützung für grundlegende neuronale Netze."
        : "Currently: Linear Regression, Logistic Regression, Decision Trees, KMeans, and Model Ensembles. We're working on basic neural network support."
    },
    {
      question: currentLang === 'es'
        ? "¿Cómo funciona la gobernanza blockchain?"
        : currentLang === 'de'
        ? "Wie funktioniert die Blockchain-Governance?"
        : "How does blockchain governance work?",
      answer: currentLang === 'es'
        ? "Desplegamos smart contracts en Arbitrum que registran contribuciones, votos y distribución de ingresos. Todo es auditable y transparente. Los participantes votan propuestas y el sistema ejecuta automáticamente las decisiones."
        : currentLang === 'de'
        ? "Wir deployen Smart Contracts auf Arbitrum, die Beiträge, Abstimmungen und Einnahmenverteilung aufzeichnen. Alles ist auditierbar und transparent. Teilnehmer stimmen über Vorschläge ab und das System führt Entscheidungen automatisch aus."
        : "We deploy smart contracts on Arbitrum that record contributions, votes, and revenue distribution. Everything is auditable and transparent. Participants vote on proposals and the system automatically executes decisions."
    },
    {
      question: currentLang === 'es'
        ? "¿Cumple con GDPR/HIPAA?"
        : currentLang === 'de'
        ? "Ist es DSGVO/HIPAA-konform?"
        : "Is it GDPR/HIPAA compliant?",
      answer: currentLang === 'es'
        ? "Sí. Como los datos nunca se descifran, no hay exposición de información personal. Nuestro dashboard de compliance verifica automáticamente requisitos regulatorios y genera reportes de auditoría."
        : currentLang === 'de'
        ? "Ja. Da Daten nie entschlüsselt werden, gibt es keine Offenlegung persönlicher Informationen. Unser Compliance-Dashboard verifiziert automatisch regulatorische Anforderungen und erstellt Auditberichte."
        : "Yes. Since data is never decrypted, there's no exposure of personal information. Our compliance dashboard automatically verifies regulatory requirements and generates audit reports."
    },
    {
      question: currentLang === 'es'
        ? "¿Puedo probarlo antes de comprar?"
        : currentLang === 'de'
        ? "Kann ich es vor dem Kauf testen?"
        : "Can I try before buying?",
      answer: currentLang === 'es'
        ? "Absolutamente. Tenemos un Sandbox gratuito con datos sintéticos donde puedes probar toda la funcionalidad. También ofrecemos POCs personalizados para empresas."
        : currentLang === 'de'
        ? "Absolut. Wir haben eine kostenlose Sandbox mit synthetischen Daten, wo Sie alle Funktionen testen können. Wir bieten auch maßgeschneiderte POCs für Unternehmen an."
        : "Absolutely. We have a free Sandbox with synthetic data where you can test all functionality. We also offer custom POCs for enterprises."
    },
  ]

  const techStack = [
    { name: 'TenSEAL', desc: 'CKKS FHE' },
    { name: 'FastAPI', desc: 'REST API' },
    { name: 'Arbitrum', desc: 'Blockchain' },
    { name: 'React', desc: 'Dashboard' },
    { name: 'PostgreSQL', desc: 'Database' },
    { name: 'Docker', desc: 'Containers' },
  ]

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled ? 'bg-white/95 backdrop-blur-md shadow-sm' : 'bg-transparent'
      }`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center mr-2 transition-colors ${
                scrolled ? 'bg-brand-600' : 'bg-white/20 backdrop-blur-sm'
              }`}>
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <span className={`text-2xl font-bold transition-colors ${scrolled ? 'text-slate-900' : 'text-white'}`}>
                Xcapit
              </span>
              <span className={`text-2xl font-light ml-1 transition-colors ${scrolled ? 'text-brand-600' : 'text-brand-200'}`}>
                Privacy
              </span>
            </div>
            <div className="hidden md:flex items-center gap-6">
              <a href="#features" className={`font-medium transition-colors ${scrolled ? 'text-slate-600 hover:text-slate-900' : 'text-white/80 hover:text-white'}`}>
                {currentLang === 'es' ? 'Características' : currentLang === 'de' ? 'Funktionen' : 'Features'}
              </a>
              <a href="#use-cases" className={`font-medium transition-colors ${scrolled ? 'text-slate-600 hover:text-slate-900' : 'text-white/80 hover:text-white'}`}>
                {currentLang === 'es' ? 'Casos de Uso' : currentLang === 'de' ? 'Anwendungsfälle' : 'Use Cases'}
              </a>
              <a href="#pricing" className={`font-medium transition-colors ${scrolled ? 'text-slate-600 hover:text-slate-900' : 'text-white/80 hover:text-white'}`}>
                {currentLang === 'es' ? 'Precios' : currentLang === 'de' ? 'Preise' : 'Pricing'}
              </a>
              <Link to="/demos" className={`font-medium transition-colors ${scrolled ? 'text-slate-600 hover:text-slate-900' : 'text-white/80 hover:text-white'}`}>
                Demos
              </Link>
            </div>
            <div className="flex items-center gap-3">
              <LanguageSwitcher variant="toggle" />
              <Link to="/login" className={`hidden sm:block font-medium transition-colors ${scrolled ? 'text-slate-600 hover:text-slate-900' : 'text-white/80 hover:text-white'}`}>
                {t('landing.nav.login')}
              </Link>
              <Link to="/register" className="bg-brand-600 text-white px-5 py-2.5 rounded-lg font-medium hover:bg-brand-700 transition shadow-lg shadow-brand-600/25">
                {t('landing.nav.register')}
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center overflow-hidden">
        {/* Animated Background */}
        <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-brand-900 to-indigo-900"></div>
        <div className="absolute inset-0">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-brand-500/30 rounded-full blur-3xl animate-pulse"></div>
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-indigo-500/30 rounded-full blur-3xl animate-pulse delay-1000"></div>
        </div>
        <div className="absolute inset-0 opacity-20">
          <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
            <defs>
              <pattern id="grid" width="4" height="4" patternUnits="userSpaceOnUse">
                <path d="M 4 0 L 0 0 0 4" fill="none" stroke="white" strokeWidth="0.1"/>
              </pattern>
            </defs>
            <rect width="100" height="100" fill="url(#grid)" />
          </svg>
        </div>

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-16">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Left: Text Content */}
            <div className="text-center lg:text-left">
              <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm px-4 py-2 rounded-full mb-8 border border-white/20">
                <span className="relative flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
                </span>
                <span className="text-white/90 text-sm font-medium">
                  {currentLang === 'es' ? 'Plataforma v1.0 - Producción Lista' : currentLang === 'de' ? 'Plattform v1.0 - Produktionsbereit' : 'Platform v1.0 - Production Ready'}
                </span>
              </div>

              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-6 leading-tight">
                {currentLang === 'es' ? 'Machine Learning' : 'Machine Learning'}
                <br />
                <span className="bg-gradient-to-r from-brand-400 to-indigo-400 bg-clip-text text-transparent">
                  {currentLang === 'es' ? 'Sin Ver Tus Datos' : currentLang === 'de' ? 'Ohne Ihre Daten zu Sehen' : 'Without Seeing Your Data'}
                </span>
              </h1>

              <p className="text-lg lg:text-xl text-slate-300 mb-8 max-w-xl leading-relaxed">
                {currentLang === 'es'
                  ? 'Entrena modelos colaborativos entre empresas con cifrado homomórfico. Los datos nunca se descifran. Gobernanza transparente en blockchain.'
                  : currentLang === 'de'
                  ? 'Trainieren Sie kollaborative Modelle zwischen Unternehmen mit homomorpher Verschlüsselung. Daten werden nie entschlüsselt. Transparente Blockchain-Governance.'
                  : 'Train collaborative models across companies with homomorphic encryption. Data is never decrypted. Transparent blockchain governance.'}
              </p>

              <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start mb-12">
                <Link
                  to="/demos"
                  className="group inline-flex items-center justify-center gap-3 bg-white text-slate-900 px-8 py-4 rounded-xl font-semibold hover:bg-slate-100 transition text-lg shadow-2xl"
                >
                  <svg className="w-6 h-6 text-brand-600" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M8 5v14l11-7z"/>
                  </svg>
                  {currentLang === 'es' ? 'Ver Demo' : currentLang === 'de' ? 'Demo ansehen' : 'Watch Demo'}
                  <svg className="w-4 h-4 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </Link>
                <Link
                  to="/register"
                  className="inline-flex items-center justify-center gap-2 bg-gradient-to-r from-brand-500 to-indigo-500 text-white px-8 py-4 rounded-xl font-semibold hover:from-brand-600 hover:to-indigo-600 transition text-lg border border-white/20"
                >
                  {currentLang === 'es' ? 'Empezar Gratis' : currentLang === 'de' ? 'Kostenlos starten' : 'Start Free'}
                </Link>
              </div>

              {/* Stats Grid */}
              <div className="grid grid-cols-4 gap-4">
                {stats.map((stat, index) => (
                  <div key={index} className="text-center">
                    <div className="text-2xl md:text-3xl font-bold text-white">
                      <AnimatedCounter end={stat.value} suffix={stat.suffix} />
                    </div>
                    <div className="text-xs md:text-sm text-slate-400">{stat.label}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Right: Hero Visual */}
            <div className="relative hidden lg:block">
              <div className="relative">
                {/* Main Video/Image Container */}
                <div className="relative rounded-2xl overflow-hidden shadow-2xl border border-white/10 bg-slate-800/50 backdrop-blur-sm">
                  <video
                    src={currentLang === 'es' ? '/videos/es/demo_consorcio.mp4' : '/videos/en/demo_consorcio.mp4'}
                    autoPlay
                    loop
                    muted
                    playsInline
                    className="w-full aspect-video object-cover"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-slate-900/80 via-transparent to-transparent"></div>
                  <div className="absolute bottom-4 left-4 right-4">
                    <div className="flex items-center gap-3 text-white text-sm">
                      <span className="flex items-center gap-2 bg-red-500/90 px-3 py-1 rounded-full">
                        <span className="w-2 h-2 bg-white rounded-full animate-pulse"></span>
                        LIVE
                      </span>
                      <span className="text-white/80">
                        {currentLang === 'es' ? 'Demo en vivo del consorcio' : currentLang === 'de' ? 'Live-Konsortium-Demo' : 'Live consortium demo'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Floating Cards */}
                <div className="absolute -top-6 -right-6 bg-white rounded-xl shadow-xl p-4 animate-float">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                      <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                      </svg>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-slate-900">100%</div>
                      <div className="text-sm text-slate-600">{currentLang === 'es' ? 'Datos Privados' : currentLang === 'de' ? 'Daten Privat' : 'Data Private'}</div>
                    </div>
                  </div>
                </div>

                <div className="absolute -bottom-6 -left-6 bg-white rounded-xl shadow-xl p-4 animate-float-delayed">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-brand-100 rounded-lg flex items-center justify-center">
                      <svg className="w-6 h-6 text-brand-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-slate-900">FHE</div>
                      <div className="text-sm text-slate-600">{currentLang === 'es' ? 'Encriptación' : currentLang === 'de' ? 'Verschlüsselung' : 'Encryption'}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Scroll Indicator */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce">
          <svg className="w-6 h-6 text-white/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
        </div>
      </section>

      {/* Credentials Section */}
      <section className="py-12 bg-slate-50 border-y border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-2 gap-8 items-center">
            <div className="text-center md:text-left">
              <p className="text-sm text-slate-500 mb-2 uppercase tracking-wider">
                {currentLang === 'es' ? 'Respaldado por' : currentLang === 'de' ? 'Unterstützt von' : 'Backed by'}
              </p>
              <div className="flex items-center justify-center md:justify-start gap-4">
                <a href="https://quarkid.org" target="_blank" rel="noopener noreferrer" className="group">
                  <div className="text-3xl font-bold text-slate-700 group-hover:text-brand-600 transition">
                    QuarkID
                  </div>
                  <div className="text-sm text-slate-500">
                    {currentLang === 'es' ? '3.6M+ usuarios' : currentLang === 'de' ? '3.6M+ Nutzer' : '3.6M+ users'}
                  </div>
                </a>
              </div>
            </div>
            <div className="text-center md:text-right">
              <p className="text-sm text-slate-500 mb-4 uppercase tracking-wider">
                {currentLang === 'es' ? 'Tecnologías' : currentLang === 'de' ? 'Technologien' : 'Technologies'}
              </p>
              <div className="flex flex-wrap justify-center md:justify-end items-center gap-6">
                {techStack.map((tech, index) => (
                  <div key={index} className="flex flex-col items-center group">
                    <div className="text-lg font-semibold text-slate-400 group-hover:text-brand-600 transition">
                      {tech.name}
                    </div>
                    <div className="text-xs text-slate-400">{tech.desc}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <span className="inline-block px-4 py-1 bg-brand-100 text-brand-700 rounded-full text-sm font-medium mb-4">
              {currentLang === 'es' ? 'Características' : currentLang === 'de' ? 'Funktionen' : 'Features'}
            </span>
            <h2 className="text-4xl font-bold text-slate-900 mb-4">
              {currentLang === 'es' ? 'Todo lo que necesitas para ML privado' : currentLang === 'de' ? 'Alles für privates ML' : 'Everything you need for private ML'}
            </h2>
            <p className="text-xl text-slate-600 max-w-2xl mx-auto">
              {currentLang === 'es'
                ? 'Una plataforma completa para colaboración en machine learning preservando la privacidad.'
                : currentLang === 'de'
                ? 'Eine vollständige Plattform für datenschutzerhaltende ML-Zusammenarbeit.'
                : 'A complete platform for privacy-preserving machine learning collaboration.'}
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <div
                key={index}
                className="group relative bg-white rounded-2xl p-8 border border-slate-200 hover:border-transparent hover:shadow-xl transition-all duration-300"
              >
                <div className={`absolute inset-0 bg-gradient-to-br ${feature.gradient} opacity-0 group-hover:opacity-5 rounded-2xl transition-opacity`}></div>
                <div className={`w-14 h-14 bg-gradient-to-br ${feature.gradient} text-white rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform`}>
                  {feature.icon}
                </div>
                <h3 className="text-xl font-semibold text-slate-900 mb-3">{feature.title}</h3>
                <p className="text-slate-600 leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Use Cases Section */}
      <section id="use-cases" className="py-24 bg-slate-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <span className="inline-block px-4 py-1 bg-emerald-100 text-emerald-700 rounded-full text-sm font-medium mb-4">
              {currentLang === 'es' ? 'Casos de Uso' : currentLang === 'de' ? 'Anwendungsfälle' : 'Use Cases'}
            </span>
            <h2 className="text-4xl font-bold text-slate-900 mb-4">
              {currentLang === 'es' ? 'Industrias que transformamos' : currentLang === 'de' ? 'Branchen, die wir transformieren' : 'Industries we transform'}
            </h2>
            <p className="text-xl text-slate-600 max-w-2xl mx-auto">
              {currentLang === 'es'
                ? 'Soluciones adaptadas para los desafíos de privacidad de datos más críticos.'
                : currentLang === 'de'
                ? 'Lösungen für die kritischsten Datenschutz-Herausforderungen.'
                : 'Solutions tailored for the most critical data privacy challenges.'}
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            {useCases.map((useCase, index) => (
              <Link
                key={index}
                to={useCase.link}
                className={`group bg-white rounded-2xl p-8 border-l-4 ${
                  useCase.color === 'blue' ? 'border-blue-500 hover:border-blue-600' :
                  useCase.color === 'emerald' ? 'border-emerald-500 hover:border-emerald-600' :
                  useCase.color === 'amber' ? 'border-amber-500 hover:border-amber-600' :
                  'border-slate-500 hover:border-slate-600'
                } hover:shadow-xl hover:-translate-y-1 transition-all duration-300 cursor-pointer`}
              >
                <div className="text-4xl mb-4 group-hover:scale-110 transition-transform">{useCase.icon}</div>
                <h3 className="text-2xl font-semibold text-slate-900 mb-3 group-hover:text-brand-600 transition-colors">{useCase.title}</h3>
                <p className="text-slate-600 mb-6">{useCase.description}</p>
                <div className="flex flex-wrap gap-2 mb-4">
                  {useCase.examples.map((example, i) => (
                    <span key={i} className="px-3 py-1 bg-slate-100 text-slate-600 rounded-full text-sm">
                      {example}
                    </span>
                  ))}
                </div>
                <span className="inline-flex items-center gap-2 text-brand-600 font-semibold group-hover:gap-3 transition-all">
                  {currentLang === 'es' ? 'Ver soluciones' : currentLang === 'de' ? 'Lösungen ansehen' : 'View solutions'}
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                  </svg>
                </span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Comparison Section */}
      <section className="py-24 bg-white">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <span className="inline-block px-4 py-1 bg-purple-100 text-purple-700 rounded-full text-sm font-medium mb-4">
              {currentLang === 'es' ? 'Comparativa' : currentLang === 'de' ? 'Vergleich' : 'Comparison'}
            </span>
            <h2 className="text-4xl font-bold text-slate-900 mb-4">
              {currentLang === 'es' ? '¿Por qué Xcapit Privacy?' : currentLang === 'de' ? 'Warum Xcapit Privacy?' : 'Why Xcapit Privacy?'}
            </h2>
            <p className="text-xl text-slate-600 max-w-2xl mx-auto">
              {currentLang === 'es'
                ? 'Combinamos lo mejor del cifrado homomórfico con gobernanza blockchain.'
                : currentLang === 'de'
                ? 'Wir kombinieren das Beste aus homomorpher Verschlüsselung mit Blockchain-Governance.'
                : 'We combine the best of homomorphic encryption with blockchain governance.'}
            </p>
          </div>

          <div className="bg-slate-50 rounded-2xl overflow-hidden border border-slate-200">
            <div className="grid grid-cols-4 bg-slate-100 border-b border-slate-200">
              <div className="p-4 font-semibold text-slate-900">
                {currentLang === 'es' ? 'Característica' : currentLang === 'de' ? 'Funktion' : 'Feature'}
              </div>
              <div className="p-4 text-center font-semibold text-brand-600">Xcapit</div>
              <div className="p-4 text-center font-semibold text-slate-600">
                {currentLang === 'es' ? 'ML Tradicional' : currentLang === 'de' ? 'Traditionelles ML' : 'Traditional ML'}
              </div>
              <div className="p-4 text-center font-semibold text-slate-600">MPC</div>
            </div>
            {comparison.map((row, index) => (
              <div key={index} className="grid grid-cols-4 border-b border-slate-200 last:border-0 hover:bg-white transition">
                <div className="p-4 text-slate-700">{row.feature}</div>
                <div className="p-4 flex justify-center">
                  {row.xcapit === true ? (
                    <svg className="w-6 h-6 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  ) : row.xcapit === 'partial' ? (
                    <svg className="w-6 h-6 text-amber-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
                    </svg>
                  ) : (
                    <svg className="w-6 h-6 text-slate-300" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                  )}
                </div>
                <div className="p-4 flex justify-center">
                  {row.traditional === true ? (
                    <svg className="w-6 h-6 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  ) : row.traditional === 'partial' ? (
                    <svg className="w-6 h-6 text-amber-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
                    </svg>
                  ) : (
                    <svg className="w-6 h-6 text-slate-300" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                  )}
                </div>
                <div className="p-4 flex justify-center">
                  {row.mpc === true ? (
                    <svg className="w-6 h-6 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  ) : row.mpc === 'partial' ? (
                    <svg className="w-6 h-6 text-amber-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
                    </svg>
                  ) : (
                    <svg className="w-6 h-6 text-slate-300" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-24 bg-slate-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <span className="inline-block px-4 py-1 bg-brand-500/20 text-brand-400 rounded-full text-sm font-medium mb-4">
              {currentLang === 'es' ? 'Testimonios' : currentLang === 'de' ? 'Referenzen' : 'Testimonials'}
            </span>
            <h2 className="text-4xl font-bold text-white mb-4">
              {currentLang === 'es' ? 'Lo que dicen nuestros usuarios' : currentLang === 'de' ? 'Was unsere Nutzer sagen' : 'What our users say'}
            </h2>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <div key={index} className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-8 border border-slate-700">
                <div className="flex items-center gap-1 mb-4">
                  {[...Array(5)].map((_, i) => (
                    <svg key={i} className="w-5 h-5 text-amber-400" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                  ))}
                </div>
                <p className="text-slate-300 mb-6 italic">"{testimonial.quote}"</p>
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-slate-700 rounded-full flex items-center justify-center text-2xl">
                    {testimonial.avatar}
                  </div>
                  <div>
                    <div className="font-semibold text-white">{testimonial.author}</div>
                    <div className="text-sm text-slate-400">{testimonial.company}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <span className="inline-block px-4 py-1 bg-amber-100 text-amber-700 rounded-full text-sm font-medium mb-4">
              {currentLang === 'es' ? 'Precios' : currentLang === 'de' ? 'Preise' : 'Pricing'}
            </span>
            <h2 className="text-4xl font-bold text-slate-900 mb-4">
              {currentLang === 'es' ? 'Plan simple, valor extraordinario' : currentLang === 'de' ? 'Einfacher Plan, außergewöhnlicher Wert' : 'Simple plan, extraordinary value'}
            </h2>
            <p className="text-xl text-slate-600 max-w-2xl mx-auto">
              {currentLang === 'es'
                ? 'Comienza gratis, escala según tus necesidades.'
                : currentLang === 'de'
                ? 'Starten Sie kostenlos, skalieren Sie nach Bedarf.'
                : 'Start free, scale as you need.'}
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {/* Free Tier */}
            <div className="bg-white rounded-2xl p-8 border-2 border-slate-200 hover:border-slate-300 transition">
              <div className="text-lg font-semibold text-slate-900 mb-2">Sandbox</div>
              <div className="flex items-baseline gap-1 mb-4">
                <span className="text-4xl font-bold text-slate-900">{currentLang === 'es' ? 'Gratis' : currentLang === 'de' ? 'Kostenlos' : 'Free'}</span>
              </div>
              <p className="text-slate-600 mb-6">
                {currentLang === 'es' ? 'Perfecto para probar y aprender.' : currentLang === 'de' ? 'Perfekt zum Testen und Lernen.' : 'Perfect to test and learn.'}
              </p>
              <ul className="space-y-3 mb-8">
                {[
                  currentLang === 'es' ? 'Datos sintéticos' : currentLang === 'de' ? 'Synthetische Daten' : 'Synthetic data',
                  currentLang === 'es' ? 'Todos los modelos ML' : currentLang === 'de' ? 'Alle ML-Modelle' : 'All ML models',
                  currentLang === 'es' ? '1 consorcio de prueba' : currentLang === 'de' ? '1 Test-Konsortium' : '1 test consortium',
                  currentLang === 'es' ? 'Dashboard completo' : currentLang === 'de' ? 'Vollständiges Dashboard' : 'Full dashboard',
                ].map((feature, i) => (
                  <li key={i} className="flex items-center gap-2 text-slate-600">
                    <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    {feature}
                  </li>
                ))}
              </ul>
              <Link to="/register" className="block w-full text-center bg-slate-100 text-slate-700 py-3 rounded-xl font-semibold hover:bg-slate-200 transition">
                {currentLang === 'es' ? 'Empezar Gratis' : currentLang === 'de' ? 'Kostenlos starten' : 'Start Free'}
              </Link>
            </div>

            {/* Pro Tier */}
            <div className="bg-gradient-to-br from-brand-600 to-indigo-600 rounded-2xl p-8 text-white relative transform md:scale-105 shadow-xl">
              <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 bg-amber-400 text-amber-900 rounded-full text-sm font-bold">
                {currentLang === 'es' ? 'MÁS POPULAR' : currentLang === 'de' ? 'BELIEBTESTE' : 'MOST POPULAR'}
              </div>
              <div className="text-lg font-semibold mb-2">Pro</div>
              <div className="flex items-baseline gap-1 mb-4">
                <span className="text-4xl font-bold">$999</span>
                <span className="text-brand-200">/{currentLang === 'es' ? 'mes' : currentLang === 'de' ? 'Monat' : 'month'}</span>
              </div>
              <p className="text-brand-100 mb-6">
                {currentLang === 'es' ? 'Para equipos que necesitan colaboración real.' : currentLang === 'de' ? 'Für Teams, die echte Zusammenarbeit brauchen.' : 'For teams that need real collaboration.'}
              </p>
              <ul className="space-y-3 mb-8">
                {[
                  currentLang === 'es' ? 'Datos reales encriptados' : currentLang === 'de' ? 'Echte verschlüsselte Daten' : 'Real encrypted data',
                  currentLang === 'es' ? '5 consorcios activos' : currentLang === 'de' ? '5 aktive Konsortien' : '5 active consortiums',
                  currentLang === 'es' ? 'Gobernanza blockchain' : currentLang === 'de' ? 'Blockchain-Governance' : 'Blockchain governance',
                  currentLang === 'es' ? 'Dashboard de compliance' : currentLang === 'de' ? 'Compliance-Dashboard' : 'Compliance dashboard',
                  currentLang === 'es' ? 'Soporte prioritario' : currentLang === 'de' ? 'Prioritätssupport' : 'Priority support',
                ].map((feature, i) => (
                  <li key={i} className="flex items-center gap-2">
                    <svg className="w-5 h-5 text-brand-200" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    {feature}
                  </li>
                ))}
              </ul>
              <Link to="/register" className="block w-full text-center bg-white text-brand-600 py-3 rounded-xl font-semibold hover:bg-brand-50 transition">
                {currentLang === 'es' ? 'Comenzar Ahora' : currentLang === 'de' ? 'Jetzt starten' : 'Get Started'}
              </Link>
            </div>

            {/* Enterprise Tier */}
            <div className="bg-white rounded-2xl p-8 border-2 border-slate-200 hover:border-slate-300 transition">
              <div className="text-lg font-semibold text-slate-900 mb-2">Enterprise</div>
              <div className="flex items-baseline gap-1 mb-4">
                <span className="text-4xl font-bold text-slate-900">{currentLang === 'es' ? 'Custom' : currentLang === 'de' ? 'Individuell' : 'Custom'}</span>
              </div>
              <p className="text-slate-600 mb-6">
                {currentLang === 'es' ? 'Soluciones a medida para grandes organizaciones.' : currentLang === 'de' ? 'Maßgeschneiderte Lösungen für große Organisationen.' : 'Custom solutions for large organizations.'}
              </p>
              <ul className="space-y-3 mb-8">
                {[
                  currentLang === 'es' ? 'Consorcios ilimitados' : currentLang === 'de' ? 'Unbegrenzte Konsortien' : 'Unlimited consortiums',
                  currentLang === 'es' ? 'Despliegue on-premise' : currentLang === 'de' ? 'On-Premise-Bereitstellung' : 'On-premise deployment',
                  currentLang === 'es' ? 'SLA garantizado' : currentLang === 'de' ? 'Garantiertes SLA' : 'Guaranteed SLA',
                  currentLang === 'es' ? 'Integración personalizada' : currentLang === 'de' ? 'Individuelle Integration' : 'Custom integration',
                  currentLang === 'es' ? 'Account manager dedicado' : currentLang === 'de' ? 'Dedizierter Account Manager' : 'Dedicated account manager',
                ].map((feature, i) => (
                  <li key={i} className="flex items-center gap-2 text-slate-600">
                    <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    {feature}
                  </li>
                ))}
              </ul>
              <a href="#contact" className="block w-full text-center bg-slate-900 text-white py-3 rounded-xl font-semibold hover:bg-slate-800 transition">
                {currentLang === 'es' ? 'Contactar Ventas' : currentLang === 'de' ? 'Vertrieb kontaktieren' : 'Contact Sales'}
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-24 bg-slate-50">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <span className="inline-block px-4 py-1 bg-slate-200 text-slate-700 rounded-full text-sm font-medium mb-4">
              FAQ
            </span>
            <h2 className="text-4xl font-bold text-slate-900 mb-4">
              {currentLang === 'es' ? 'Preguntas Frecuentes' : currentLang === 'de' ? 'Häufig gestellte Fragen' : 'Frequently Asked Questions'}
            </h2>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 divide-y divide-slate-200">
            {faqs.map((faq, index) => (
              <FAQItem
                key={index}
                question={faq.question}
                answer={faq.answer}
                isOpen={openFAQ === index}
                onClick={() => setOpenFAQ(openFAQ === index ? -1 : index)}
              />
            ))}
          </div>
        </div>
      </section>

      {/* Contact Section */}
      <section id="contact" className="py-24 bg-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <span className="inline-block px-4 py-1 bg-brand-100 text-brand-700 rounded-full text-sm font-medium mb-4">
              {currentLang === 'es' ? 'Contacto' : currentLang === 'de' ? 'Kontakt' : 'Contact'}
            </span>
            <h2 className="text-4xl font-bold text-slate-900 mb-4">{t('landing.contact.title')}</h2>
            <p className="text-xl text-slate-600">{t('landing.contact.subtitle')}</p>
          </div>
          <ContactForm />
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-24 bg-gradient-to-br from-slate-900 via-brand-900 to-indigo-900 relative overflow-hidden">
        <div className="absolute inset-0">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-brand-500/20 rounded-full blur-3xl"></div>
        </div>
        <div className="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
            {currentLang === 'es'
              ? '¿Listo para revolucionar tu ML?'
              : currentLang === 'de'
              ? 'Bereit, Ihr ML zu revolutionieren?'
              : 'Ready to revolutionize your ML?'}
          </h2>
          <p className="text-xl text-slate-300 mb-10 max-w-2xl mx-auto">
            {currentLang === 'es'
              ? 'Únete a las empresas que ya colaboran de forma segura con sus datos más sensibles.'
              : currentLang === 'de'
              ? 'Schließen Sie sich Unternehmen an, die bereits sicher mit ihren sensibelsten Daten zusammenarbeiten.'
              : 'Join companies already collaborating securely with their most sensitive data.'}
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/register"
              className="inline-flex items-center justify-center bg-white text-slate-900 px-8 py-4 rounded-xl font-semibold hover:bg-slate-100 transition text-lg shadow-2xl"
            >
              {currentLang === 'es' ? 'Crear Cuenta Gratis' : currentLang === 'de' ? 'Kostenloses Konto erstellen' : 'Create Free Account'}
              <svg className="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
              </svg>
            </Link>
            <Link
              to="/demos"
              className="inline-flex items-center justify-center bg-white/10 backdrop-blur-sm text-white px-8 py-4 rounded-xl font-semibold hover:bg-white/20 transition text-lg border border-white/20"
            >
              <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z"/>
              </svg>
              {currentLang === 'es' ? 'Ver Demos' : currentLang === 'de' ? 'Demos ansehen' : 'Watch Demos'}
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8 mb-12">
            <div className="md:col-span-2">
              <div className="flex items-center mb-4">
                <div className="w-10 h-10 bg-brand-600 rounded-xl flex items-center justify-center mr-2">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                </div>
                <span className="text-xl font-bold text-white">Xcapit</span>
                <span className="text-xl font-light text-brand-400 ml-1">Privacy</span>
              </div>
              <p className="text-slate-400 max-w-md">
                {currentLang === 'es'
                  ? 'Plataforma de machine learning colaborativo con cifrado homomórfico y gobernanza blockchain.'
                  : currentLang === 'de'
                  ? 'Kollaborative Machine-Learning-Plattform mit homomorpher Verschlüsselung und Blockchain-Governance.'
                  : 'Collaborative machine learning platform with homomorphic encryption and blockchain governance.'}
              </p>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">{currentLang === 'es' ? 'Producto' : currentLang === 'de' ? 'Produkt' : 'Product'}</h4>
              <ul className="space-y-2">
                <li><Link to="/demos" className="text-slate-400 hover:text-white transition">Demos</Link></li>
                <li><a href="#features" className="text-slate-400 hover:text-white transition">{currentLang === 'es' ? 'Características' : currentLang === 'de' ? 'Funktionen' : 'Features'}</a></li>
                <li><a href="#pricing" className="text-slate-400 hover:text-white transition">{currentLang === 'es' ? 'Precios' : currentLang === 'de' ? 'Preise' : 'Pricing'}</a></li>
                <li><Link to="/register" className="text-slate-400 hover:text-white transition">{currentLang === 'es' ? 'Registrarse' : currentLang === 'de' ? 'Registrieren' : 'Sign Up'}</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">{currentLang === 'es' ? 'Contacto' : currentLang === 'de' ? 'Kontakt' : 'Contact'}</h4>
              <ul className="space-y-2">
                <li><a href="mailto:consorcios@xcapit.com" className="text-slate-400 hover:text-white transition">consorcios@xcapit.com</a></li>
                <li><a href="https://github.com/xcapit" className="text-slate-400 hover:text-white transition">GitHub</a></li>
                <li><a href="https://twitter.com/xcapit" className="text-slate-400 hover:text-white transition">Twitter</a></li>
              </ul>
            </div>
          </div>
          <div className="pt-8 border-t border-slate-800 flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-slate-500 text-sm">
              © 2025 Xcapit Privacy. {currentLang === 'es' ? 'Todos los derechos reservados.' : currentLang === 'de' ? 'Alle Rechte vorbehalten.' : 'All rights reserved.'}
            </p>
            <div className="flex items-center gap-6">
              <a href="#" className="text-slate-500 hover:text-slate-300 text-sm">{currentLang === 'es' ? 'Privacidad' : currentLang === 'de' ? 'Datenschutz' : 'Privacy'}</a>
              <a href="#" className="text-slate-500 hover:text-slate-300 text-sm">{currentLang === 'es' ? 'Términos' : currentLang === 'de' ? 'AGB' : 'Terms'}</a>
            </div>
          </div>
        </div>
      </footer>

      {/* Custom Animations */}
      <style>{`
        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-10px); }
        }
        .animate-float {
          animation: float 3s ease-in-out infinite;
        }
        .animate-float-delayed {
          animation: float 3s ease-in-out infinite;
          animation-delay: 1.5s;
        }
      `}</style>
    </div>
  )
}
