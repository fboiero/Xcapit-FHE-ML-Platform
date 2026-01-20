import { NavLink, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { XMarkIcon, ArrowRightIcon } from '@heroicons/react/24/outline'
import { useEffect, useState } from 'react'

export default function Sidebar({ isOpen, onClose }) {
  const { t, i18n } = useTranslation()
  const location = useLocation()
  const currentLang = i18n.language?.startsWith('es') ? 'es' : 'en'
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  const navItems = [
    {
      label: t('nav.dashboard'),
      path: '/dashboard',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
        </svg>
      ),
    },
    {
      label: t('nav.useCases'),
      path: '/demo-consorcio',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
      ),
      highlight: true,
    },
    {
      label: t('nav.governance'),
      path: '/governance',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      ),
      highlight: true,
    },
    {
      label: t('nav.technicalDemo'),
      path: '/demo',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
        </svg>
      ),
    },
    {
      label: t('nav.createConsortium'),
      path: '/consortiums/new',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
        </svg>
      ),
    },
  ]

  // Handle link click on mobile - close sidebar
  const handleLinkClick = () => {
    if (window.innerWidth < 768) {
      onClose()
    }
  }

  return (
    <aside
      className={`
        fixed left-0 top-16 bottom-0 w-64 bg-white border-r border-slate-200 p-4
        transition-transform duration-300 ease-in-out z-40
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        md:translate-x-0
      `}
      aria-label={currentLang === 'es' ? 'Menú de navegación' : 'Navigation menu'}
    >
      {/* Close button - mobile only */}
      <button
        onClick={onClose}
        className="md:hidden absolute top-4 right-4 p-2 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition focus:outline-none focus:ring-2 focus:ring-brand-500"
        aria-label={currentLang === 'es' ? 'Cerrar menú' : 'Close menu'}
      >
        <XMarkIcon className="w-5 h-5" />
      </button>

      <nav className="space-y-1 mt-8 md:mt-0" role="navigation">
        {navItems.map((item, index) => (
          <NavLink
            key={item.path}
            to={item.path}
            onClick={handleLinkClick}
            className={({ isActive }) =>
              `group flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-brand-500 ${
                isActive
                  ? 'bg-gradient-to-r from-brand-50 to-brand-100 text-brand-600 shadow-sm'
                  : item.highlight
                  ? 'text-purple-600 bg-purple-50 hover:bg-purple-100 hover:translate-x-1'
                  : 'text-slate-600 hover:bg-slate-50 hover:translate-x-1'
              }`
            }
            style={{
              opacity: mounted ? 1 : 0,
              transform: mounted ? 'translateX(0)' : 'translateX(-10px)',
              transition: `all 0.3s ease ${index * 50}ms`
            }}
          >
            <span className="group-hover:scale-110 transition-transform duration-200">
              {item.icon}
            </span>
            <span className="font-medium">{item.label}</span>
            {item.highlight && (
              <span className="ml-auto text-xs bg-gradient-to-r from-purple-600 to-indigo-600 text-white px-2 py-0.5 rounded-full animate-pulse">
                {t('common.new')}
              </span>
            )}
            {location.pathname === item.path && (
              <ArrowRightIcon className="w-4 h-4 ml-auto text-brand-500" />
            )}
          </NavLink>
        ))}
      </nav>

      {/* Help section */}
      <div className="absolute bottom-4 left-4 right-4">
        <div className="bg-gradient-to-br from-slate-50 to-slate-100 rounded-xl p-4 border border-slate-200 hover:border-brand-200 hover:shadow-md transition-all duration-300 group">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-8 h-8 bg-brand-100 rounded-lg flex items-center justify-center group-hover:bg-brand-200 transition-colors">
              <svg className="w-4 h-4 text-brand-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h4 className="font-medium text-slate-900">{t('nav.needHelp')}</h4>
          </div>
          <p className="text-sm text-slate-600 mb-3">
            {t('nav.helpDescription')}
          </p>
          <a
            href="/#colaboracion"
            className="inline-flex items-center gap-1 text-sm text-brand-600 font-medium hover:text-brand-700 focus:outline-none focus:underline group-hover:gap-2 transition-all"
          >
            {t('nav.contactUs')}
            <ArrowRightIcon className="w-3 h-3" />
          </a>
        </div>
      </div>
    </aside>
  )
}
