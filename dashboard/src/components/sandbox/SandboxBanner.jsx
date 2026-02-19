/**
 * SandboxBanner Component
 *
 * Shows sandbox status, remaining time, and upgrade CTA.
 */

import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  ClockIcon,
  SparklesIcon,
  XMarkIcon,
  ArrowRightIcon,
} from '@heroicons/react/24/outline'
import {
  getSandboxEmail,
  getSandboxTimeRemaining,
  clearSandboxAccess,
  hasSandboxAccess,
} from '../../api/sandbox'

export default function SandboxBanner({ onExpired, variant = 'floating' }) {
  const { i18n } = useTranslation()
  const [dismissed, setDismissed] = useState(false)
  const [timeRemaining, setTimeRemaining] = useState(null)
  const email = getSandboxEmail()

  const currentLang = i18n.language?.startsWith('es') ? 'es' : 'en'

  // Update time remaining every minute
  useEffect(() => {
    const updateTime = () => {
      if (!hasSandboxAccess()) {
        onExpired?.()
        return
      }
      setTimeRemaining(getSandboxTimeRemaining())
    }

    updateTime()
    const interval = setInterval(updateTime, 60000) // Update every minute

    return () => clearInterval(interval)
  }, [onExpired])

  if (dismissed || !timeRemaining) return null

  const formatTime = () => {
    const { days, hours, minutes } = timeRemaining

    if (days > 0) {
      return currentLang === 'es'
        ? `${days}d ${hours}h restantes`
        : `${days}d ${hours}h remaining`
    }
    if (hours > 0) {
      return currentLang === 'es'
        ? `${hours}h ${minutes}m restantes`
        : `${hours}h ${minutes}m remaining`
    }
    return currentLang === 'es'
      ? `${minutes}m restantes`
      : `${minutes}m remaining`
  }

  const isLowTime = timeRemaining.days === 0 && timeRemaining.hours < 24

  // Floating variant (fixed at bottom)
  if (variant === 'floating') {
    return (
      <div className={`fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:w-96 z-50 ${
        isLowTime ? 'bg-amber-900/95' : 'bg-slate-800/95'
      } backdrop-blur-sm rounded-xl border ${
        isLowTime ? 'border-amber-700' : 'border-slate-700'
      } shadow-xl`}>
        <div className="p-4">
          {/* Header */}
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <SparklesIcon className={`w-5 h-5 ${isLowTime ? 'text-amber-400' : 'text-brand-400'}`} />
              <span className="font-medium text-white text-sm">
                {currentLang === 'es' ? 'Modo Sandbox' : 'Sandbox Mode'}
              </span>
            </div>
            <button
              onClick={() => setDismissed(true)}
              className="text-slate-400 hover:text-white p-1"
            >
              <XMarkIcon className="w-4 h-4" />
            </button>
          </div>

          {/* Time remaining */}
          <div className="flex items-center gap-2 mb-3">
            <ClockIcon className={`w-4 h-4 ${isLowTime ? 'text-amber-400' : 'text-slate-400'}`} />
            <span className={`text-sm ${isLowTime ? 'text-amber-300' : 'text-slate-300'}`}>
              {formatTime()}
            </span>
          </div>

          {/* Email */}
          {email && (
            <div className="text-xs text-slate-500 mb-3 truncate">
              {email}
            </div>
          )}

          {/* CTA */}
          <Link
            to="/register"
            className={`flex items-center justify-center gap-2 w-full py-2 px-4 ${
              isLowTime
                ? 'bg-amber-600 hover:bg-amber-500'
                : 'bg-brand-600 hover:bg-brand-500'
            } text-white rounded-lg text-sm font-medium transition-colors`}
          >
            {currentLang === 'es' ? 'Crear cuenta completa' : 'Create full account'}
            <ArrowRightIcon className="w-4 h-4" />
          </Link>
        </div>
      </div>
    )
  }

  // Inline variant (for header)
  return (
    <div className={`flex items-center gap-4 px-4 py-2 rounded-lg ${
      isLowTime ? 'bg-amber-900/50 border border-amber-700' : 'bg-slate-800/50 border border-slate-700'
    }`}>
      <div className="flex items-center gap-2">
        <SparklesIcon className={`w-4 h-4 ${isLowTime ? 'text-amber-400' : 'text-brand-400'}`} />
        <span className="text-sm text-white font-medium">Sandbox</span>
      </div>

      <div className="flex items-center gap-1.5 text-sm">
        <ClockIcon className={`w-4 h-4 ${isLowTime ? 'text-amber-400' : 'text-slate-400'}`} />
        <span className={isLowTime ? 'text-amber-300' : 'text-slate-300'}>
          {formatTime()}
        </span>
      </div>

      <Link
        to="/register"
        className="text-xs text-brand-400 hover:text-brand-300 font-medium"
      >
        {currentLang === 'es' ? 'Upgrade' : 'Upgrade'}
      </Link>
    </div>
  )
}

/**
 * SandboxExpiredModal Component
 *
 * Shows when sandbox access has expired.
 */
export function SandboxExpiredModal({ onClose, onRenew }) {
  const { i18n } = useTranslation()
  const currentLang = i18n.language?.startsWith('es') ? 'es' : 'en'

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
      <div className="bg-slate-800 rounded-2xl border border-slate-700 p-8 max-w-md mx-4 text-center">
        <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-amber-900/50 flex items-center justify-center">
          <ClockIcon className="w-8 h-8 text-amber-400" />
        </div>

        <h2 className="text-xl font-bold text-white mb-2">
          {currentLang === 'es' ? 'Sandbox Expirado' : 'Sandbox Expired'}
        </h2>

        <p className="text-slate-400 mb-6">
          {currentLang === 'es'
            ? 'Tu acceso al sandbox ha expirado. Puedes renovarlo o crear una cuenta completa.'
            : 'Your sandbox access has expired. You can renew it or create a full account.'}
        </p>

        <div className="space-y-3">
          <Link
            to="/register"
            className="block w-full py-3 px-4 bg-brand-600 hover:bg-brand-500 text-white rounded-xl font-medium transition-colors"
          >
            {currentLang === 'es' ? 'Crear cuenta completa' : 'Create full account'}
          </Link>

          <button
            onClick={onRenew}
            className="block w-full py-3 px-4 bg-slate-700 hover:bg-slate-600 text-white rounded-xl font-medium transition-colors"
          >
            {currentLang === 'es' ? 'Renovar sandbox (email)' : 'Renew sandbox (email)'}
          </button>

          <button
            onClick={onClose}
            className="block w-full py-2 text-slate-400 hover:text-white text-sm transition-colors"
          >
            {currentLang === 'es' ? 'Cerrar' : 'Close'}
          </button>
        </div>
      </div>
    </div>
  )
}
