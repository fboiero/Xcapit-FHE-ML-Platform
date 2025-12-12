import { useState, useRef, useEffect } from 'react'
import { useTranslation } from 'react-i18next'

const languages = [
  { code: 'en', name: 'English', flag: 'US' },
  { code: 'es', name: 'Espanol', flag: 'ES' }
]

// Simple flag component using emoji flags
const Flag = ({ code }) => {
  const flags = {
    US: (
      <svg className="w-5 h-5" viewBox="0 0 512 512">
        <rect width="512" height="512" fill="#bf0a30"/>
        <rect y="39.4" width="512" height="39.4" fill="#fff"/>
        <rect y="118.2" width="512" height="39.4" fill="#fff"/>
        <rect y="197" width="512" height="39.4" fill="#fff"/>
        <rect y="275.8" width="512" height="39.4" fill="#fff"/>
        <rect y="354.6" width="512" height="39.4" fill="#fff"/>
        <rect y="433.4" width="512" height="39.4" fill="#fff"/>
        <rect width="204.8" height="275.8" fill="#002868"/>
      </svg>
    ),
    ES: (
      <svg className="w-5 h-5" viewBox="0 0 512 512">
        <rect width="512" height="512" fill="#c60b1e"/>
        <rect y="128" width="512" height="256" fill="#ffc400"/>
      </svg>
    )
  }
  return flags[code] || null
}

export default function LanguageSwitcher({ variant = 'dropdown' }) {
  const { i18n } = useTranslation()
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef(null)

  const currentLanguage = languages.find(l => l.code === i18n.language) || languages[0]

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const changeLanguage = (code) => {
    i18n.changeLanguage(code)
    localStorage.setItem('xcapit_language', code)
    setIsOpen(false)
  }

  // Toggle variant - simple buttons side by side
  if (variant === 'toggle') {
    return (
      <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
        {languages.map(lang => (
          <button
            key={lang.code}
            onClick={() => changeLanguage(lang.code)}
            className={`flex items-center gap-1 px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
              i18n.language === lang.code
                ? 'bg-white shadow text-indigo-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <Flag code={lang.flag} />
            <span className="hidden sm:inline">{lang.code.toUpperCase()}</span>
          </button>
        ))}
      </div>
    )
  }

  // Minimal variant - just flags
  if (variant === 'minimal') {
    return (
      <div className="flex items-center gap-2">
        {languages.map(lang => (
          <button
            key={lang.code}
            onClick={() => changeLanguage(lang.code)}
            className={`p-1.5 rounded-md transition-all ${
              i18n.language === lang.code
                ? 'ring-2 ring-indigo-500 ring-offset-2'
                : 'opacity-50 hover:opacity-100'
            }`}
            title={lang.name}
          >
            <Flag code={lang.flag} />
          </button>
        ))}
      </div>
    )
  }

  // Default dropdown variant
  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
      >
        <Flag code={currentLanguage.flag} />
        <span className="text-sm font-medium text-gray-700">
          {currentLanguage.code.toUpperCase()}
        </span>
        <svg
          className={`w-4 h-4 text-gray-500 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-40 bg-white border border-gray-200 rounded-lg shadow-lg z-50 overflow-hidden">
          {languages.map(lang => (
            <button
              key={lang.code}
              onClick={() => changeLanguage(lang.code)}
              className={`w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-50 transition-colors ${
                i18n.language === lang.code ? 'bg-indigo-50 text-indigo-600' : 'text-gray-700'
              }`}
            >
              <Flag code={lang.flag} />
              <span className="text-sm font-medium">{lang.name}</span>
              {i18n.language === lang.code && (
                <svg className="w-4 h-4 ml-auto" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
