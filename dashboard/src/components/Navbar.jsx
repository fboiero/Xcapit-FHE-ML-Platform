import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { getCurrentCompany, clearApiKey, isDemoMode } from '../api/client'
import { useDemo } from '../context/DemoContext'
import { SparklesIcon } from '@heroicons/react/24/outline'
import LanguageSwitcher from './LanguageSwitcher'

export default function Navbar() {
  const { t, i18n } = useTranslation()
  const { demoClient, getScenarioData } = useDemo()
  const [company, setCompany] = useState(null)
  const [showMenu, setShowMenu] = useState(false)
  const navigate = useNavigate()

  const isDemo = isDemoMode()
  const currentLang = i18n.language?.startsWith('es') ? 'es' : 'en'

  useEffect(() => {
    if (isDemo) {
      // Use demo client data
      const scenario = getScenarioData()
      setCompany({
        name: scenario?.client?.name || 'Demo Company',
        email: 'demo@xcapit.com',
        logo: scenario?.client?.logo || 'D'
      })
    } else {
      getCurrentCompany()
        .then(setCompany)
        .catch(console.error)
    }
  }, [isDemo])

  const handleLogout = () => {
    clearApiKey()
    navigate('/login')
  }

  return (
    <nav className="fixed top-0 left-0 right-0 h-16 bg-navy-900 border-b border-slate-800 z-50">
      <div className="h-full px-6 flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center">
          <div className="w-8 h-8 bg-brand-600 rounded-lg flex items-center justify-center mr-2">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </div>
          <span className="text-xl font-semibold text-white">Xcapit</span>
          <span className="text-xl font-light text-brand-400 ml-1">Privacy</span>
        </div>

        {/* Right side */}
        <div className="flex items-center gap-4">
          {isDemo && (
            <div className="flex items-center gap-1.5 px-3 py-1 bg-amber-500/20 rounded-full">
              <SparklesIcon className="w-4 h-4 text-amber-400" />
              <span className="text-xs font-medium text-amber-400">
                {currentLang === 'es' ? 'DEMO' : 'DEMO'}
              </span>
            </div>
          )}
          <LanguageSwitcher variant="minimal" />

          {/* User menu */}
          <div className="relative">
            <button
              onClick={() => setShowMenu(!showMenu)}
              className="flex items-center gap-3 px-4 py-2 rounded-lg hover:bg-slate-800 transition"
            >
              <div className="w-8 h-8 bg-brand-600 rounded-full flex items-center justify-center">
                <span className="text-white text-sm font-medium">
                  {company?.name?.charAt(0) || '?'}
                </span>
              </div>
              <span className="text-white text-sm">{company?.name || t('common.loading')}</span>
              <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {showMenu && (
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-xl shadow-lg border border-slate-200 py-1">
                <div className="px-4 py-2 border-b border-slate-100">
                  <p className="text-sm font-medium text-slate-900">{company?.name}</p>
                  <p className="text-xs text-slate-500">{company?.email}</p>
                </div>
                <button
                  onClick={handleLogout}
                  className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                >
                  {t('nav.closeSession')}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}
