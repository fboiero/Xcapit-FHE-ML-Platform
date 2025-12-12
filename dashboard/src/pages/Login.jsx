import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { setApiKey, getCurrentCompany } from '../api/client'
import LanguageSwitcher from '../components/LanguageSwitcher'

export default function Login() {
  const { t } = useTranslation()
  const [apiKey, setApiKeyValue] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      // Set the API key first
      setApiKey(apiKey)

      // Validate by fetching current company
      await getCurrentCompany()

      // Success - redirect to dashboard
      navigate('/dashboard')
    } catch (err) {
      // Clear invalid key
      setApiKey('')
      setError(t('auth.login.invalidKey'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="absolute top-4 right-4">
        <LanguageSwitcher variant="toggle" />
      </div>

      <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md">
        {/* Logo */}
        <div className="flex items-center justify-center mb-8">
          <div className="w-10 h-10 bg-brand-600 rounded-lg flex items-center justify-center mr-2">
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </div>
          <span className="text-2xl font-semibold text-slate-900">Xcapit</span>
          <span className="text-2xl font-light text-brand-600 ml-1">Privacy</span>
        </div>

        <h1 className="text-2xl font-bold text-slate-900 text-center mb-2">{t('auth.login.title')}</h1>
        <p className="text-slate-600 text-center mb-8">
          {t('auth.login.subtitle')}
        </p>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              {t('auth.login.apiKey')}
            </label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKeyValue(e.target.value)}
              className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-brand-500 focus:border-transparent transition font-mono"
              placeholder={t('auth.login.apiKeyPlaceholder')}
              required
            />
            <p className="text-xs text-slate-500 mt-2">
              {t('auth.login.apiKeyHelp')}
            </p>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-brand-600 text-white py-3 px-4 rounded-xl font-medium hover:bg-brand-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? t('auth.login.verifying') : t('auth.login.title')}
          </button>
        </form>

        <p className="text-center text-slate-600 mt-6">
          {t('auth.login.noAccount')}{' '}
          <Link to="/register" className="text-brand-600 font-medium hover:text-brand-700">
            {t('auth.login.registerCompany')}
          </Link>
        </p>

        {/* Demo Link */}
        <div className="mt-8 pt-6 border-t border-slate-200">
          <p className="text-center text-slate-500 text-sm mb-3">
            {t('auth.login.wantToSee')}
          </p>
          <div className="space-y-3">
            <Link
              to="/sandbox-demo"
              className="flex items-center justify-center gap-2 w-full py-3 px-4 rounded-xl font-medium bg-amber-500 text-white hover:bg-amber-600 transition"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              {t('auth.login.trySandbox') || 'Probar Sandbox Demo'}
            </Link>
            <Link
              to="/demos"
              className="flex items-center justify-center gap-2 w-full py-3 px-4 rounded-xl font-medium border-2 border-indigo-200 text-indigo-600 hover:bg-indigo-50 transition"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {t('auth.login.watchDemo')}
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
