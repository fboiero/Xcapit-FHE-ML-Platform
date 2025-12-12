import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { registerCompany } from '../api/client'
import LanguageSwitcher from '../components/LanguageSwitcher'

export default function Register() {
  const { t } = useTranslation()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(null)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const result = await registerCompany(name, email)
      setSuccess(result)
      // Redirect after showing API key
      setTimeout(() => navigate('/dashboard'), 3000)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
        <div className="absolute top-4 right-4">
          <LanguageSwitcher variant="toggle" />
        </div>

        <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-slate-900 mb-2">{t('auth.register.success.title')}</h2>
          <p className="text-slate-600 mb-6">{t('auth.register.success.subtitle')}</p>

          <div className="bg-slate-100 rounded-lg p-4 mb-6">
            <p className="text-xs text-slate-500 mb-1">{t('auth.register.success.yourApiKey')}</p>
            <code className="text-sm font-mono text-slate-900 break-all">{success.api_key}</code>
          </div>

          <p className="text-sm text-slate-500">{t('auth.register.success.redirecting')}</p>
        </div>
      </div>
    )
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

        <h1 className="text-2xl font-bold text-slate-900 text-center mb-2">{t('auth.register.title')}</h1>
        <p className="text-slate-600 text-center mb-8">
          {t('auth.register.subtitle')}
        </p>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              {t('auth.register.companyName')}
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-brand-500 focus:border-transparent transition"
              placeholder={t('auth.register.companyPlaceholder')}
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              {t('auth.register.corporateEmail')}
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-brand-500 focus:border-transparent transition"
              placeholder={t('auth.register.emailPlaceholder')}
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-brand-600 text-white py-3 px-4 rounded-xl font-medium hover:bg-brand-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? t('auth.register.registering') : t('auth.register.registerCompany')}
          </button>
        </form>

        <p className="text-center text-slate-600 mt-6">
          {t('auth.register.hasAccount')}{' '}
          <Link to="/login" className="text-brand-600 font-medium hover:text-brand-700">
            {t('auth.register.login')}
          </Link>
        </p>

        {/* Demo Link */}
        <div className="mt-8 pt-6 border-t border-slate-200">
          <p className="text-center text-slate-500 text-sm mb-3">
            {t('auth.register.wantToSeeFirst')}
          </p>
          <Link
            to="/demos"
            className="flex items-center justify-center gap-2 w-full py-3 px-4 rounded-xl font-medium border-2 border-indigo-200 text-indigo-600 hover:bg-indigo-50 transition"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {t('auth.register.watchDemo')}
          </Link>
        </div>
      </div>
    </div>
  )
}
