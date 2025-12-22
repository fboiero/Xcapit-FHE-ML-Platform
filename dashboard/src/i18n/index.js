import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import LanguageDetector from 'i18next-browser-languagedetector'

import translationEN from './locales/en/translation.json'
import translationES from './locales/es/translation.json'

const resources = {
  en: {
    translation: translationEN
  },
  es: {
    translation: translationES
  }
}

i18n
  // Detect user language
  .use(LanguageDetector)
  // Pass the i18n instance to react-i18next
  .use(initReactI18next)
  // Init i18next
  .init({
    resources,
    fallbackLng: 'en',
    debug: false,

    detection: {
      // Order of language detection
      order: ['localStorage', 'navigator', 'htmlTag'],
      // Keys to look for in localStorage/sessionStorage
      lookupLocalStorage: 'xcapit_language',
      // Cache user language in localStorage
      caches: ['localStorage'],
    },

    interpolation: {
      escapeValue: false // React already safes from XSS
    },

    react: {
      useSuspense: false
    }
  })

export default i18n
