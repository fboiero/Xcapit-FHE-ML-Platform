import { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import LanguageSwitcher from './LanguageSwitcher'

export default function LandingHeader({ ctaText, ctaHref = '#contact' }) {
  const { i18n } = useTranslation()
  const lang = i18n.language?.startsWith('es') ? 'es' : 'en'
  const location = useLocation()
  const [scrolled, setScrolled] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 50)
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const content = {
    es: {
      product: 'Producto',
      industries: 'Industrias',
      docs: 'Docs',
      login: 'Iniciar sesión',
      getStarted: 'Empezar gratis',
      defaultCta: 'Solicitar Demo',
      verticals: [
        { name: 'Hub Principal', path: '/', icon: '🏠' },
        { name: 'Fintech & Banca', path: '/fintech', icon: '🏦' },
        { name: 'Healthcare', path: '/healthcare', icon: '🏥' },
        { name: 'Gobierno', path: '/gobierno', icon: '🏛️' },
        { name: 'Otras Industrias', path: '/industrias', icon: '🏭' },
      ]
    },
    en: {
      product: 'Product',
      industries: 'Industries',
      docs: 'Docs',
      login: 'Sign in',
      getStarted: 'Get started free',
      defaultCta: 'Request Demo',
      verticals: [
        { name: 'Main Hub', path: '/', icon: '🏠' },
        { name: 'Fintech & Banking', path: '/fintech', icon: '🏦' },
        { name: 'Healthcare', path: '/healthcare', icon: '🏥' },
        { name: 'Government', path: '/gobierno', icon: '🏛️' },
        { name: 'Other Industries', path: '/industrias', icon: '🏭' },
      ]
    }
  }

  const t = content[lang]
  const currentPath = location.pathname

  return (
    <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
      scrolled ? 'bg-[#0a0a0f]/95 backdrop-blur-xl border-b border-white/10 shadow-lg' : 'bg-transparent'
    }`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 group">
            <div className="w-9 h-9 bg-gradient-to-br from-brand-500 to-indigo-600 rounded-lg flex items-center justify-center group-hover:scale-105 transition-transform">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <span className="text-lg font-bold text-white">Xcapit</span>
            <span className="text-lg font-light text-brand-400">Privacy</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-1">
            {/* Industries Dropdown */}
            <div className="relative group">
              <button className="flex items-center gap-1 text-slate-400 hover:text-white text-sm font-medium px-3 py-2 rounded-lg hover:bg-white/5 transition">
                {t.industries}
                <svg className="w-4 h-4 group-hover:rotate-180 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {/* Dropdown Menu */}
              <div className="absolute top-full left-0 mt-1 w-56 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 transform group-hover:translate-y-0 translate-y-2">
                <div className="bg-slate-900/95 backdrop-blur-xl border border-white/10 rounded-xl shadow-2xl p-2">
                  {t.verticals.map((vertical) => (
                    <Link
                      key={vertical.path}
                      to={vertical.path}
                      className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all ${
                        currentPath === vertical.path
                          ? 'bg-brand-500/20 text-brand-400'
                          : 'text-slate-300 hover:bg-white/5 hover:text-white'
                      }`}
                    >
                      <span className="text-lg">{vertical.icon}</span>
                      <span className="text-sm font-medium">{vertical.name}</span>
                      {currentPath === vertical.path && (
                        <svg className="w-4 h-4 ml-auto text-brand-400" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      )}
                    </Link>
                  ))}
                </div>
              </div>
            </div>

            <a href="#how-it-works" className="text-slate-400 hover:text-white text-sm font-medium px-3 py-2 rounded-lg hover:bg-white/5 transition">
              {t.product}
            </a>
            <a href="#" className="text-slate-400 hover:text-white text-sm font-medium px-3 py-2 rounded-lg hover:bg-white/5 transition">
              {t.docs}
            </a>
          </div>

          {/* Right side */}
          <div className="flex items-center gap-3">
            <LanguageSwitcher variant="minimal" />

            <Link to="/login" className="hidden sm:block text-slate-400 hover:text-white text-sm font-medium px-3 py-2 transition">
              {t.login}
            </Link>

            <a
              href={ctaHref}
              className="bg-gradient-to-r from-brand-500 to-indigo-600 text-white text-sm font-semibold px-4 py-2 rounded-lg hover:from-brand-600 hover:to-indigo-700 transition shadow-lg shadow-brand-500/25"
            >
              {ctaText || t.defaultCta}
            </a>

            {/* Mobile menu button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 text-slate-400 hover:text-white transition"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                {mobileMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-white/10 py-4">
            <div className="space-y-1">
              {t.verticals.map((vertical) => (
                <Link
                  key={vertical.path}
                  to={vertical.path}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`flex items-center gap-3 px-3 py-3 rounded-lg transition-all ${
                    currentPath === vertical.path
                      ? 'bg-brand-500/20 text-brand-400'
                      : 'text-slate-300 hover:bg-white/5'
                  }`}
                >
                  <span className="text-lg">{vertical.icon}</span>
                  <span className="font-medium">{vertical.name}</span>
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>
    </nav>
  )
}
