import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import LanguageSwitcher from '../components/LanguageSwitcher'

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
  const [status, setStatus] = useState('idle') // idle, sending, success, error

  const handleSubmit = async (e) => {
    e.preventDefault()
    setStatus('sending')

    try {
      const response = await fetch('https://api.web3forms.com/submit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
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
            className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:border-brand-500 transition bg-slate-50 focus:bg-white"
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
            className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:border-brand-500 transition bg-slate-50 focus:bg-white"
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
            className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:border-brand-500 transition bg-slate-50 focus:bg-white"
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
            className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:border-brand-500 transition bg-slate-50 focus:bg-white"
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
          className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:border-brand-500 transition bg-slate-50 focus:bg-white"
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
            className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:border-brand-500 transition bg-slate-50 focus:bg-white appearance-none"
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
            className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:border-brand-500 transition bg-slate-50 focus:bg-white appearance-none"
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
          className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:border-brand-500 transition bg-slate-50 focus:bg-white resize-none"
          placeholder={t('landing.contact.messagePlaceholder')}
        />
      </div>

      <button
        type="submit"
        disabled={status === 'sending'}
        className="w-full bg-brand-600 text-white py-4 px-6 rounded-xl font-semibold hover:bg-brand-700 transition disabled:opacity-50 flex items-center justify-center gap-2"
      >
        {status === 'sending' ? (
          t('landing.contact.sending')
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
        <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-xl">
          <p className="text-center text-green-700 font-medium">
            {t('landing.contact.successMessage')}
          </p>
        </div>
      )}
      {status === 'error' && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl">
          <p className="text-center text-red-700 font-medium">
            {t('landing.contact.errorMessage')}
          </p>
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
  const currentLang = i18n.language?.startsWith('es') ? 'es' : 'en'

  const features = [
    {
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
      ),
      title: t('landing.features.encrypted.title'),
      description: t('landing.features.encrypted.description')
    },
    {
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
      ),
      title: t('landing.features.privateML.title'),
      description: t('landing.features.privateML.description')
    },
    {
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      ),
      title: t('landing.features.secureCollab.title'),
      description: t('landing.features.secureCollab.description')
    },
  ]

  const useCases = [
    {
      icon: (
        <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
        </svg>
      ),
      title: t('landing.useCases.fraud.title'),
      description: t('landing.useCases.fraud.description'),
      color: 'blue'
    },
    {
      icon: (
        <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
        </svg>
      ),
      title: t('landing.useCases.health.title'),
      description: t('landing.useCases.health.description'),
      color: 'emerald'
    },
  ]

  const phases = [
    {
      number: '01',
      title: t('landing.phases.sdk.title'),
      description: t('landing.phases.sdk.description'),
      status: 'completed'
    },
    {
      number: '02',
      title: t('landing.phases.ml.title'),
      description: t('landing.phases.ml.description'),
      status: 'completed'
    },
    {
      number: '03',
      title: t('landing.phases.api.title'),
      description: t('landing.phases.api.description'),
      status: 'completed'
    },
    {
      number: '04',
      title: t('landing.phases.blockchain.title'),
      description: t('landing.phases.blockchain.description'),
      status: 'completed'
    },
    {
      number: '05',
      title: t('landing.phases.governance.title'),
      description: t('landing.phases.governance.description'),
      status: 'completed'
    },
  ]

  const demoVideos = [
    {
      title: t('landing.demoVideos.consortium.title'),
      description: t('landing.demoVideos.consortium.description'),
      video: currentLang === 'es' ? '/videos/es/demo_consorcio.mp4' : '/videos/en/demo_consorcio.mp4',
      color: 'purple'
    },
    {
      title: t('landing.demoVideos.governance.title'),
      description: t('landing.demoVideos.governance.description'),
      video: currentLang === 'es' ? '/videos/es/demo_governance.mp4' : '/videos/en/demo_governance.mp4',
      color: 'green'
    },
    {
      title: t('landing.demoVideos.platform.title'),
      description: t('landing.demoVideos.platform.description'),
      video: currentLang === 'es' ? '/videos/es/demo_web.mp4' : '/videos/en/demo_web.mp4',
      color: 'blue'
    }
  ]

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Navigation */}
      <nav className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <div className="w-10 h-10 bg-brand-600 rounded-lg flex items-center justify-center mr-2">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <span className="text-2xl font-semibold text-slate-900">Xcapit</span>
              <span className="text-2xl font-light text-brand-600 ml-1">Privacy</span>
            </div>
            <div className="flex items-center gap-4">
              <LanguageSwitcher variant="toggle" />
              <Link to="/demos" className="text-slate-600 hover:text-slate-900 font-medium">
                {t('landing.nav.demos')}
              </Link>
              <Link to="/login" className="text-slate-600 hover:text-slate-900 font-medium">
                {t('landing.nav.login')}
              </Link>
              <Link to="/register" className="bg-brand-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-brand-700 transition">
                {t('landing.nav.register')}
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-brand-600 to-indigo-800"></div>
        <div className="absolute inset-0 opacity-10">
          <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
            <defs>
              <pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse">
                <path d="M 10 0 L 0 0 0 10" fill="none" stroke="white" strokeWidth="0.5"/>
              </pattern>
            </defs>
            <rect width="100" height="100" fill="url(#grid)" />
          </svg>
        </div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 lg:py-24">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Left: Text Content */}
            <div className="text-center lg:text-left">
              <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm px-4 py-2 rounded-full mb-6">
                <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
                <span className="text-white/90 text-sm font-medium">{t('landing.hero.badge')}</span>
              </div>
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-6 leading-tight">
                {t('landing.hero.title')}
                <br />
                <span className="text-brand-200">{t('landing.hero.titleHighlight')}</span>
              </h1>
              <p className="text-lg lg:text-xl text-brand-100 mb-8 max-w-xl">
                {t('landing.hero.subtitle')}
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
                <Link
                  to="/demos"
                  className="inline-flex items-center justify-center gap-2 bg-white text-brand-600 px-8 py-4 rounded-xl font-semibold hover:bg-brand-50 transition text-lg shadow-lg"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  {t('landing.hero.watchDemo')}
                </Link>
                <Link
                  to="/register"
                  className="inline-flex items-center justify-center gap-2 bg-brand-500 text-white px-8 py-4 rounded-xl font-semibold hover:bg-brand-400 transition text-lg border border-brand-400"
                >
                  {t('landing.hero.startFree')}
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                  </svg>
                </Link>
              </div>
              {/* Trust indicators */}
              <div className="mt-10 pt-8 border-t border-white/20">
                <p className="text-white/60 text-sm mb-4">{t('landing.hero.trustedBy')}</p>
                <div className="flex flex-wrap gap-6 justify-center lg:justify-start">
                  <div className="flex items-center gap-2 text-white/80">
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span className="text-sm">{t('landing.hero.fheEncryption')}</span>
                  </div>
                  <div className="flex items-center gap-2 text-white/80">
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span className="text-sm">{t('landing.hero.gdprCompliant')}</span>
                  </div>
                  <div className="flex items-center gap-2 text-white/80">
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
                      <path fillRule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm9.707 5.707a1 1 0 00-1.414-1.414L9 12.586l-1.293-1.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span className="text-sm">{t('landing.hero.auditTrail')}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Right: Hero Video */}
            <div className="relative">
              <div className="relative rounded-2xl overflow-hidden shadow-2xl border-4 border-white/20">
                <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent z-10 pointer-events-none"></div>
                <video
                  src={currentLang === 'es' ? '/videos/es/demo_consorcio.mp4' : '/videos/en/demo_consorcio.mp4'}
                  autoPlay
                  loop
                  muted
                  playsInline
                  className="w-full aspect-video object-cover"
                />
                <div className="absolute bottom-4 left-4 right-4 z-20">
                  <div className="bg-black/60 backdrop-blur-sm rounded-lg p-3">
                    <div className="flex items-center gap-2 text-white text-sm">
                      <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
                      <span className="font-medium">{t('landing.hero.liveDemo')}</span>
                      <span className="text-white/70">— {t('landing.hero.videoCta')}</span>
                    </div>
                  </div>
                </div>
              </div>
              {/* Floating stats */}
              <div className="absolute -bottom-6 -left-6 bg-white rounded-xl shadow-xl p-4 hidden lg:block">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                    <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                    </svg>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-slate-900">100%</div>
                    <div className="text-sm text-slate-600">{t('landing.hero.dataPrivacy')}</div>
                  </div>
                </div>
              </div>
              <div className="absolute -top-4 -right-4 bg-white rounded-xl shadow-xl p-4 hidden lg:block">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-brand-100 rounded-lg flex items-center justify-center">
                    <svg className="w-6 h-6 text-brand-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-slate-900">N</div>
                    <div className="text-sm text-slate-600">{t('landing.hero.companies')}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900 mb-4">{t('landing.features.title')}</h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              {t('landing.features.subtitle')}
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <div key={index} className="bg-slate-50 rounded-2xl p-8 hover:shadow-lg transition">
                <div className="w-14 h-14 bg-brand-100 text-brand-600 rounded-xl flex items-center justify-center mb-6">
                  {feature.icon}
                </div>
                <h3 className="text-xl font-semibold text-slate-900 mb-3">{feature.title}</h3>
                <p className="text-slate-600">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Use Cases Section */}
      <section className="py-20 bg-slate-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900 mb-4">{t('landing.useCases.title')}</h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              {t('landing.useCases.subtitle')}
            </p>
          </div>
          <div className="grid md:grid-cols-2 gap-8">
            {useCases.map((useCase, index) => (
              <div key={index} className={`bg-white rounded-2xl p-8 border-l-4 ${useCase.color === 'blue' ? 'border-blue-500' : 'border-emerald-500'} hover:shadow-lg transition`}>
                <div className={`w-16 h-16 ${useCase.color === 'blue' ? 'bg-blue-100 text-blue-600' : 'bg-emerald-100 text-emerald-600'} rounded-xl flex items-center justify-center mb-6`}>
                  {useCase.icon}
                </div>
                <h3 className="text-xl font-semibold text-slate-900 mb-3">{useCase.title}</h3>
                <p className="text-slate-600 mb-4">{useCase.description}</p>
                <Link to="/demos" className={`inline-flex items-center ${useCase.color === 'blue' ? 'text-blue-600 hover:text-blue-700' : 'text-emerald-600 hover:text-emerald-700'} font-medium`}>
                  {t('landing.useCases.viewDemo')}
                  <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Phases Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900 mb-4">{t('landing.phases.title')}</h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              {t('landing.phases.subtitle')}
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-5 gap-6">
            {phases.map((phase, index) => (
              <div key={index} className="relative bg-slate-50 rounded-2xl p-6 hover:shadow-lg transition">
                <div className="flex items-center justify-between mb-4">
                  <span className="text-4xl font-bold text-brand-200">{phase.number}</span>
                  {phase.status === 'completed' && (
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                      {t('landing.phases.ready')}
                    </span>
                  )}
                </div>
                <h3 className="text-lg font-semibold text-slate-900 mb-2">{phase.title}</h3>
                <p className="text-sm text-slate-600">{phase.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Demo Videos Section */}
      <section className="py-20 bg-slate-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900 mb-4">{t('landing.demoVideos.title')}</h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              {t('landing.demoVideos.subtitle')}
            </p>
          </div>
          <div className="grid md:grid-cols-2 gap-8">
            {demoVideos.map((demo, index) => (
              <div key={index} className="bg-white rounded-2xl overflow-hidden shadow-lg hover:shadow-xl transition">
                <div className="aspect-video bg-slate-900 relative">
                  <video
                    src={demo.video}
                    controls
                    className="w-full h-full object-cover"
                    poster=""
                  >
                    {t('landing.demoVideos.videoNotSupported')}
                  </video>
                </div>
                <div className="p-6">
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                      demo.color === 'purple' ? 'bg-purple-100 text-purple-700' :
                      demo.color === 'green' ? 'bg-green-100 text-green-700' :
                      'bg-blue-100 text-blue-700'
                    }`}>
                      {demo.color === 'purple' ? t('landing.demoVideos.tags.consortium') : demo.color === 'green' ? t('landing.demoVideos.tags.governance') : t('landing.demoVideos.tags.platform')}
                    </span>
                  </div>
                  <h3 className="text-xl font-semibold text-slate-900 mb-2">{demo.title}</h3>
                  <p className="text-slate-600">{demo.description}</p>
                </div>
              </div>
            ))}
          </div>
          <div className="text-center mt-10">
            <Link
              to="/demos"
              className="inline-flex items-center gap-2 text-brand-600 font-medium hover:text-brand-700"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {t('landing.demoVideos.viewAllDemos')}
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          </div>
        </div>
      </section>

      {/* Contact Section */}
      <section id="colaboracion" className="py-20 bg-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-slate-900 mb-4">{t('landing.contact.title')}</h2>
            <p className="text-lg text-slate-600">
              {t('landing.contact.subtitle')}
            </p>
          </div>
          <ContactForm />
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-brand-600 to-indigo-700">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            {t('landing.cta.title')}
          </h2>
          <p className="text-xl text-brand-100 mb-8">
            {t('landing.cta.subtitle')}
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/register"
              className="inline-flex items-center justify-center bg-white text-brand-600 px-8 py-4 rounded-xl font-semibold hover:bg-brand-50 transition text-lg"
            >
              {t('landing.cta.createAccount')}
            </Link>
            <a
              href="#colaboracion"
              className="inline-flex items-center justify-center bg-transparent text-white px-8 py-4 rounded-xl font-semibold hover:bg-white/10 transition text-lg border-2 border-white/30"
            >
              {t('landing.cta.contactUs')}
            </a>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center mb-4 md:mb-0">
              <div className="w-8 h-8 bg-brand-600 rounded-lg flex items-center justify-center mr-2">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <span className="text-lg font-semibold text-white">Xcapit</span>
              <span className="text-lg font-light text-brand-400 ml-1">Privacy</span>
            </div>
            <p className="text-slate-400 text-sm">
              {t('landing.footer.copyright')}
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
