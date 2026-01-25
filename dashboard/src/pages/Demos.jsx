import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import LanguageSwitcher from '../components/LanguageSwitcher'

function DemoCard({ demo, onPlay, t, currentLang }) {
  const [isHovered, setIsHovered] = useState(false)

  // Select video based on current language
  const videoPath = currentLang === 'es' ? demo.videoEs : demo.videoEn
  const gifPath = currentLang === 'es' ? demo.gifEs : demo.gifEn

  return (
    <div
      className="bg-white rounded-xl shadow-lg overflow-hidden transform transition-all duration-300 hover:scale-105 hover:shadow-2xl"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="relative aspect-video bg-gray-900">
        {isHovered ? (
          <video
            src={videoPath}
            className="w-full h-full object-cover"
            autoPlay
            muted
            loop
            playsInline
            preload="auto"
          />
        ) : (
          <img
            src={gifPath}
            alt={demo.title}
            className="w-full h-full object-cover"
          />
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
        <button
          onClick={() => onPlay(demo)}
          className="absolute inset-0 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity"
        >
          <div className="w-16 h-16 bg-white/90 rounded-full flex items-center justify-center">
            <svg className="w-8 h-8 text-indigo-600 ml-1" fill="currentColor" viewBox="0 0 20 20">
              <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
            </svg>
          </div>
        </button>
      </div>
      <div className="p-4">
        <h3 className="font-bold text-lg text-gray-900">{demo.title}</h3>
        <p className="text-gray-600 text-sm mt-1">{demo.description}</p>
        <div className="mt-3 flex gap-2">
          <button
            onClick={() => onPlay(demo)}
            className="flex-1 px-3 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors"
          >
            {t('demos.watchDemo')}
          </button>
          <a
            href={demo.route}
            className="flex-1 px-3 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors text-center"
          >
            {t('demos.tryIt')}
          </a>
        </div>
      </div>
    </div>
  )
}

function VideoModal({ demo, onClose, currentLang }) {
  if (!demo) return null

  const videoPath = currentLang === 'es' ? demo.videoEs : demo.videoEn

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80" onClick={onClose}>
      <div className="relative max-w-4xl w-full" onClick={e => e.stopPropagation()}>
        <button
          onClick={onClose}
          className="absolute -top-10 right-0 text-white hover:text-gray-300"
        >
          <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
        <div className="bg-black rounded-xl overflow-hidden">
          <video
            src={videoPath}
            className="w-full"
            controls
            autoPlay
            playsInline
            preload="auto"
          />
        </div>
        <div className="mt-4 text-center">
          <h3 className="text-xl font-bold text-white">{demo.title}</h3>
          <p className="text-gray-300 mt-1">{demo.description}</p>
        </div>
      </div>
    </div>
  )
}

export default function Demos() {
  const { t, i18n } = useTranslation()
  const [selectedDemo, setSelectedDemo] = useState(null)
  const currentLang = i18n.language?.startsWith('es') ? 'es' : 'en'

  const DEMOS = {
    tier3: {
      title: t('demos.tier3.title'),
      description: t('demos.tier3.description'),
      demos: [
        {
          id: "compliance",
          title: t('compliance.title'),
          description: t('compliance.description'),
          videoEn: "/videos/en/demo_compliance.mp4",
          videoEs: "/videos/es/demo_compliance.mp4",
          gifEn: "/videos/en/demo_compliance.gif",
          gifEs: "/videos/es/demo_compliance.gif",
          route: "/demo-compliance"
        },
        {
          id: "quality",
          title: t('dataQuality.title'),
          description: t('dataQuality.description'),
          videoEn: "/videos/en/demo_quality.mp4",
          videoEs: "/videos/es/demo_quality.mp4",
          gifEn: "/videos/en/demo_quality.gif",
          gifEs: "/videos/es/demo_quality.gif",
          route: "/demo-quality"
        },
        {
          id: "marketplace",
          title: t('marketplace.title'),
          description: t('marketplace.description'),
          videoEn: "/videos/en/demo_marketplace.mp4",
          videoEs: "/videos/es/demo_marketplace.mp4",
          gifEn: "/videos/en/demo_marketplace.gif",
          gifEs: "/videos/es/demo_marketplace.gif",
          route: "/demo-marketplace"
        },
        {
          id: "sandbox",
          title: t('sandbox.title'),
          description: t('sandbox.description'),
          videoEn: "/videos/en/demo_sandbox.mp4",
          videoEs: "/videos/es/demo_sandbox.mp4",
          gifEn: "/videos/en/demo_sandbox.gif",
          gifEs: "/videos/es/demo_sandbox.gif",
          route: "/demo-sandbox"
        }
      ]
    },
    tier4: {
      title: t('demos.tier4.title'),
      description: t('demos.tier4.description'),
      demos: [
        {
          id: "federated",
          title: t('federated.title'),
          description: t('federated.description'),
          videoEn: "/videos/en/demo_federated.mp4",
          videoEs: "/videos/es/demo_federated.mp4",
          gifEn: "/videos/en/demo_federated.gif",
          gifEs: "/videos/es/demo_federated.gif",
          route: "/demo-federated"
        },
        {
          id: "explainability",
          title: t('explainability.title'),
          description: t('explainability.description'),
          videoEn: "/videos/en/demo_explainability.mp4",
          videoEs: "/videos/es/demo_explainability.mp4",
          gifEn: "/videos/en/demo_explainability.gif",
          gifEs: "/videos/es/demo_explainability.gif",
          route: "/demo-explainability"
        },
        {
          id: "competitive",
          title: t('competitive.title'),
          description: t('competitive.description'),
          videoEn: "/videos/en/demo_competitive.mp4",
          videoEs: "/videos/es/demo_competitive.mp4",
          gifEn: "/videos/en/demo_competitive.gif",
          gifEs: "/videos/es/demo_competitive.gif",
          route: "/demo-competitive"
        },
        {
          id: "ensemble",
          title: t('ensemble.title'),
          description: t('ensemble.description'),
          videoEn: "/videos/en/demo_ensemble.mp4",
          videoEs: "/videos/es/demo_ensemble.mp4",
          gifEn: "/videos/en/demo_ensemble.gif",
          gifEs: "/videos/es/demo_ensemble.gif",
          route: "/demo-ensemble"
        }
      ]
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-indigo-50 py-12 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header with Language Switcher */}
        <div className="flex justify-end mb-4">
          <LanguageSwitcher variant="toggle" />
        </div>

        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            {t('demos.title')}
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            {t('demos.subtitle')}
          </p>
        </div>

        {/* Vertical Industry Demos */}
        <section className="mb-16">
          <div className="flex items-center gap-3 mb-6">
            <span className="px-3 py-1 bg-gradient-to-r from-purple-500 to-indigo-600 text-white rounded-full text-sm font-medium">
              INDUSTRY DEMOS
            </span>
            <h2 className="text-2xl font-bold text-gray-900">{t('demos.verticals.title', 'Industry-Specific Demos')}</h2>
          </div>
          <p className="text-gray-600 mb-8">{t('demos.verticals.description', 'Interactive step-by-step demos showing FHE consortiums in action for different industries')}</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Bank Fraud Detection */}
            <div className="bg-white rounded-xl shadow-lg overflow-hidden transform transition-all duration-300 hover:scale-105 hover:shadow-2xl">
              <div className="relative h-48 bg-gradient-to-br from-blue-500 via-indigo-600 to-purple-600">
                <div className="absolute inset-0 flex items-center justify-center">
                  <svg className="w-20 h-20 text-white/30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 21v-8.25M15.75 21v-8.25M8.25 21v-8.25M3 9l9-6 9 6m-1.5 12V10.332A48.36 48.36 0 0012 9.75c-2.551 0-5.056.2-7.5.582V21M3 21h18M12 6.75h.008v.008H12V6.75z" />
                  </svg>
                </div>
                <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/60 to-transparent">
                  <span className="px-2 py-1 bg-blue-500 text-white text-xs rounded">Fintech</span>
                </div>
              </div>
              <div className="p-4">
                <h3 className="font-bold text-lg text-gray-900">{t('demos.verticals.bank.title', 'Bank Fraud Detection')}</h3>
                <p className="text-gray-600 text-sm mt-1">{t('demos.verticals.bank.description', 'Two banks collaborate to detect fraud without sharing customer transaction data')}</p>
                <a href="/demo-bank" className="mt-4 block w-full px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg text-sm font-medium hover:from-blue-700 hover:to-indigo-700 transition-all text-center">
                  {t('demos.tryInteractive', 'Try Interactive Demo')}
                </a>
              </div>
            </div>
            {/* Insurance Fraud Detection */}
            <div className="bg-white rounded-xl shadow-lg overflow-hidden transform transition-all duration-300 hover:scale-105 hover:shadow-2xl">
              <div className="relative h-48 bg-gradient-to-br from-amber-500 via-rose-500 to-pink-600">
                <div className="absolute inset-0 flex items-center justify-center">
                  <svg className="w-20 h-20 text-white/30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
                  </svg>
                </div>
                <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/60 to-transparent">
                  <span className="px-2 py-1 bg-amber-500 text-white text-xs rounded">Insurance</span>
                </div>
              </div>
              <div className="p-4">
                <h3 className="font-bold text-lg text-gray-900">{t('demos.verticals.insurance.title', 'Insurance Claims Fraud')}</h3>
                <p className="text-gray-600 text-sm mt-1">{t('demos.verticals.insurance.description', 'Three insurers detect fraudulent claims while protecting client privacy')}</p>
                <a href="/demo-insurance" className="mt-4 block w-full px-4 py-2 bg-gradient-to-r from-amber-600 to-rose-600 text-white rounded-lg text-sm font-medium hover:from-amber-700 hover:to-rose-700 transition-all text-center">
                  {t('demos.tryInteractive', 'Try Interactive Demo')}
                </a>
              </div>
            </div>
            {/* Retail Churn Prediction */}
            <div className="bg-white rounded-xl shadow-lg overflow-hidden transform transition-all duration-300 hover:scale-105 hover:shadow-2xl">
              <div className="relative h-48 bg-gradient-to-br from-teal-500 via-cyan-500 to-indigo-600">
                <div className="absolute inset-0 flex items-center justify-center">
                  <svg className="w-20 h-20 text-white/30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15.75 10.5V6a3.75 3.75 0 10-7.5 0v4.5m11.356-1.993l1.263 12c.07.665-.45 1.243-1.119 1.243H4.25a1.125 1.125 0 01-1.12-1.243l1.264-12A1.125 1.125 0 015.513 7.5h12.974c.576 0 1.059.435 1.119 1.007zM8.625 10.5a.375.375 0 11-.75 0 .375.375 0 01.75 0zm7.5 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z" />
                  </svg>
                </div>
                <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/60 to-transparent">
                  <span className="px-2 py-1 bg-teal-500 text-white text-xs rounded">Retail</span>
                </div>
              </div>
              <div className="p-4">
                <h3 className="font-bold text-lg text-gray-900">{t('demos.verticals.retail.title', 'Customer Churn Prediction')}</h3>
                <p className="text-gray-600 text-sm mt-1">{t('demos.verticals.retail.description', 'Three retailers predict churn using RFM metrics without exposing purchase history')}</p>
                <a href="/demo-retail" className="mt-4 block w-full px-4 py-2 bg-gradient-to-r from-teal-600 to-cyan-600 text-white rounded-lg text-sm font-medium hover:from-teal-700 hover:to-cyan-700 transition-all text-center">
                  {t('demos.tryInteractive', 'Try Interactive Demo')}
                </a>
              </div>
            </div>
          </div>
        </section>

        {/* Featured Demos - Main Platform Videos */}
        <section className="mb-16">
          <div className="flex items-center gap-3 mb-6">
            <span className="px-3 py-1 bg-gradient-to-r from-brand-500 to-brand-600 text-white rounded-full text-sm font-medium">
              FEATURED
            </span>
            <h2 className="text-2xl font-bold text-gray-900">{t('demos.featured.title', 'Platform Overview')}</h2>
          </div>
          <p className="text-gray-600 mb-8">{t('demos.featured.description', 'Watch how the complete FHE-ML platform works in action')}</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Consortium Demo */}
            <DemoCard
              demo={{
                id: "consorcio",
                title: t('demos.featured.consortium.title', 'Consortium Creation'),
                description: t('demos.featured.consortium.description', 'Create and manage secure data-sharing consortiums between competing companies'),
                videoEn: "/videos/en/demo_consorcio.mp4",
                videoEs: "/videos/es/demo_consorcio.mp4",
                gifEn: "/videos/en/demo_consorcio.mp4",
                gifEs: "/videos/es/demo_consorcio.mp4",
                route: "/clients-demo"
              }}
              onPlay={setSelectedDemo}
              t={t}
              currentLang={currentLang}
            />
            {/* Governance Demo */}
            <DemoCard
              demo={{
                id: "governance",
                title: t('demos.featured.governance.title', 'Governance Dashboard'),
                description: t('demos.featured.governance.description', 'Blockchain-backed audit trail, voting system, and contribution tracking'),
                videoEn: "/videos/en/demo_governance.mp4",
                videoEs: "/videos/es/demo_governance.mp4",
                gifEn: "/videos/en/demo_governance.mp4",
                gifEs: "/videos/es/demo_governance.mp4",
                route: "/governance"
              }}
              onPlay={setSelectedDemo}
              t={t}
              currentLang={currentLang}
            />
            {/* Web Platform Demo */}
            <DemoCard
              demo={{
                id: "web",
                title: t('demos.featured.web.title', 'Web Platform Tour'),
                description: t('demos.featured.web.description', 'Complete walkthrough of the privacy-preserving ML platform interface'),
                videoEn: "/videos/en/demo_web.mp4",
                videoEs: "/videos/es/demo_web.mp4",
                gifEn: "/videos/en/demo_web.mp4",
                gifEs: "/videos/es/demo_web.mp4",
                route: "/"
              }}
              onPlay={setSelectedDemo}
              t={t}
              currentLang={currentLang}
            />
          </div>
        </section>

        {/* TIER 3 */}
        <section className="mb-16">
          <div className="flex items-center gap-3 mb-6">
            <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium">
              TIER 3
            </span>
            <h2 className="text-2xl font-bold text-gray-900">{DEMOS.tier3.title}</h2>
          </div>
          <p className="text-gray-600 mb-8">{DEMOS.tier3.description}</p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {DEMOS.tier3.demos.map(demo => (
              <DemoCard
                key={demo.id}
                demo={demo}
                onPlay={setSelectedDemo}
                t={t}
                currentLang={currentLang}
              />
            ))}
          </div>
        </section>

        {/* TIER 4 */}
        <section>
          <div className="flex items-center gap-3 mb-6">
            <span className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm font-medium">
              TIER 4
            </span>
            <h2 className="text-2xl font-bold text-gray-900">{DEMOS.tier4.title}</h2>
          </div>
          <p className="text-gray-600 mb-8">{DEMOS.tier4.description}</p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {DEMOS.tier4.demos.map(demo => (
              <DemoCard
                key={demo.id}
                demo={demo}
                onPlay={setSelectedDemo}
                t={t}
                currentLang={currentLang}
              />
            ))}
          </div>
        </section>

        {/* FHE Clients Demo - Special Section */}
        <section className="mt-16 mb-8">
          <div className="bg-gradient-to-r from-emerald-500 to-teal-600 rounded-2xl p-8 text-white">
            <div className="flex items-center gap-4 mb-4">
              <span className="px-3 py-1 bg-white/20 rounded-full text-sm font-medium">
                LIVE DEMO
              </span>
              <h2 className="text-2xl font-bold">{t('demos.clientsDemo.title', 'FHE Multi-Client Demo')}</h2>
            </div>
            <p className="text-emerald-100 mb-6 max-w-2xl">
              {t('demos.clientsDemo.description', 'Experience how two competing companies collaborate on ML training without exposing their sensitive data. Watch the complete FHE encryption and federated learning process in action.')}
            </p>
            <div className="flex flex-wrap gap-4">
              <a
                href="/clients-demo"
                className="inline-flex items-center gap-2 px-6 py-3 bg-white text-emerald-600 rounded-lg font-semibold hover:bg-emerald-50 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {t('demos.clientsDemo.cta', 'Run Interactive Demo')}
              </a>
              <div className="flex items-center gap-2 text-emerald-100">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
                <span>{t('demos.clientsDemo.feature1', 'Real FHE Encryption')}</span>
              </div>
              <div className="flex items-center gap-2 text-emerald-100">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
                <span>{t('demos.clientsDemo.feature2', 'Multi-Party Collaboration')}</span>
              </div>
              <div className="flex items-center gap-2 text-emerald-100">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <span>{t('demos.clientsDemo.feature3', 'Random Forest ML')}</span>
              </div>
            </div>
          </div>
        </section>

        {/* Footer */}
        <div className="mt-16 text-center">
          <p className="text-gray-500 text-sm">
            {t('demos.footer')}
          </p>
        </div>
      </div>

      {/* Video Modal */}
      <VideoModal
        demo={selectedDemo}
        onClose={() => setSelectedDemo(null)}
        currentLang={currentLang}
      />
    </div>
  )
}
