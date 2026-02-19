/**
 * SandboxGate Component
 *
 * Email capture form that gates access to the sandbox.
 * Low friction - just email required.
 */

import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import {
  EnvelopeIcon,
  LockClosedIcon,
  SparklesIcon,
  ShieldCheckIcon,
  ClockIcon,
  ArrowRightIcon,
  ExclamationCircleIcon,
} from '@heroicons/react/24/outline'
import { requestSandboxAccess, getUTMParams } from '../../api/sandbox'

export default function SandboxGate({ onAccessGranted, color = 'indigo' }) {
  const { t, i18n } = useTranslation()
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const currentLang = i18n.language?.startsWith('es') ? 'es' : 'en'

  const colorClasses = {
    indigo: {
      button: 'bg-indigo-600 hover:bg-indigo-700 focus:ring-indigo-500',
      text: 'text-indigo-600',
      light: 'bg-indigo-100',
      border: 'border-indigo-300 focus:border-indigo-500',
    },
    emerald: {
      button: 'bg-emerald-600 hover:bg-emerald-700 focus:ring-emerald-500',
      text: 'text-emerald-600',
      light: 'bg-emerald-100',
      border: 'border-emerald-300 focus:border-emerald-500',
    },
    rose: {
      button: 'bg-rose-600 hover:bg-rose-700 focus:ring-rose-500',
      text: 'text-rose-600',
      light: 'bg-rose-100',
      border: 'border-rose-300 focus:border-rose-500',
    },
    purple: {
      button: 'bg-purple-600 hover:bg-purple-700 focus:ring-purple-500',
      text: 'text-purple-600',
      light: 'bg-purple-100',
      border: 'border-purple-300 focus:border-purple-500',
    },
  }

  const colors = colorClasses[color] || colorClasses.indigo

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const tracking = getUTMParams()
      const result = await requestSandboxAccess(email, tracking)
      onAccessGranted?.(result)
    } catch (err) {
      setError(err.message || (currentLang === 'es' ? 'Error al procesar' : 'Error processing request'))
    } finally {
      setLoading(false)
    }
  }

  const features = [
    {
      icon: ClockIcon,
      title: currentLang === 'es' ? '7 dias de acceso' : '7 days access',
      desc: currentLang === 'es' ? 'Sin compromiso' : 'No commitment',
    },
    {
      icon: ShieldCheckIcon,
      title: currentLang === 'es' ? 'Datos sinteticos' : 'Synthetic data',
      desc: currentLang === 'es' ? 'Sin riesgo' : 'No risk',
    },
    {
      icon: SparklesIcon,
      title: currentLang === 'es' ? 'Funciones completas' : 'Full features',
      desc: currentLang === 'es' ? 'Todo incluido' : 'All included',
    },
  ]

  return (
    <div className="w-full max-w-md mx-auto">
      {/* Header */}
      <div className="text-center mb-8">
        <div className={`w-16 h-16 mx-auto mb-4 rounded-2xl ${colors.light} flex items-center justify-center`}>
          <LockClosedIcon className={`w-8 h-8 ${colors.text}`} />
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">
          {currentLang === 'es' ? 'Acceso al Sandbox' : 'Sandbox Access'}
        </h2>
        <p className="text-slate-400">
          {currentLang === 'es'
            ? 'Ingresa tu email para comenzar a experimentar'
            : 'Enter your email to start experimenting'}
        </p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="email" className="sr-only">Email</label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <EnvelopeIcon className="h-5 w-5 text-slate-400" />
            </div>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder={currentLang === 'es' ? 'tu@email.com' : 'you@email.com'}
              className={`block w-full pl-11 pr-4 py-4 bg-slate-800 border ${colors.border} rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-slate-900 transition-colors`}
            />
          </div>
        </div>

        {error && (
          <div className="flex items-center gap-2 text-red-400 text-sm">
            <ExclamationCircleIcon className="w-5 h-5" />
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading || !email}
          className={`w-full flex items-center justify-center gap-2 py-4 px-6 ${colors.button} text-white rounded-xl font-semibold text-lg transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-slate-900 disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          {loading ? (
            <>
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              {currentLang === 'es' ? 'Procesando...' : 'Processing...'}
            </>
          ) : (
            <>
              {currentLang === 'es' ? 'Comenzar Gratis' : 'Start Free'}
              <ArrowRightIcon className="w-5 h-5" />
            </>
          )}
        </button>
      </form>

      {/* Features */}
      <div className="mt-8 grid grid-cols-3 gap-4">
        {features.map((feature, idx) => (
          <div key={idx} className="text-center">
            <feature.icon className="w-6 h-6 mx-auto mb-2 text-slate-400" />
            <div className="text-xs font-medium text-white">{feature.title}</div>
            <div className="text-xs text-slate-500">{feature.desc}</div>
          </div>
        ))}
      </div>

      {/* Privacy Note */}
      <p className="mt-8 text-center text-xs text-slate-500">
        {currentLang === 'es' ? (
          <>Solo usamos tu email para el sandbox. Sin spam.</>
        ) : (
          <>We only use your email for sandbox access. No spam.</>
        )}
      </p>
    </div>
  )
}
