import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  PlusCircleIcon,
  BeakerIcon,
  CloudArrowUpIcon,
  BookOpenIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline'

const STORAGE_KEY = 'xcapit_onboarding_completed'

const actions = [
  { labelKey: 'onboarding.createConsortium', to: '/consortiums/new', icon: PlusCircleIcon },
  { labelKey: 'onboarding.exploreSandbox', to: '/sandbox', icon: BeakerIcon },
  { labelKey: 'onboarding.uploadData', to: '/data-upload', icon: CloudArrowUpIcon },
  { labelKey: 'onboarding.documentation', to: '/demo', icon: BookOpenIcon },
]

export default function WelcomeOnboarding() {
  const { t } = useTranslation()
  const [dismissed, setDismissed] = useState(
    () => localStorage.getItem(STORAGE_KEY) === 'true'
  )

  if (dismissed) return null

  const handleDismiss = () => {
    localStorage.setItem(STORAGE_KEY, 'true')
    setDismissed(true)
  }

  return (
    <div className="bg-gradient-to-r from-brand-50 to-indigo-50 border border-brand-200 rounded-2xl p-6 mb-6 relative">
      <button
        onClick={handleDismiss}
        className="absolute top-4 right-4 p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-white/50 transition"
        aria-label={t('common.cancel')}
      >
        <XMarkIcon className="w-5 h-5" />
      </button>

      <h2 className="text-lg font-semibold text-slate-900 mb-1">
        {t('onboarding.title')}
      </h2>
      <p className="text-sm text-slate-600 mb-4">
        {t('onboarding.subtitle')}
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {actions.map((action) => (
          <Link
            key={action.to}
            to={action.to}
            className="flex items-center gap-3 bg-white rounded-xl border border-slate-200 p-4 hover:border-brand-300 hover:shadow-md transition-all group"
          >
            <div className="w-10 h-10 bg-brand-100 rounded-lg flex items-center justify-center group-hover:bg-brand-200 transition-colors flex-shrink-0">
              <action.icon className="w-5 h-5 text-brand-600" />
            </div>
            <span className="text-sm font-medium text-slate-700 group-hover:text-brand-600 transition-colors">
              {t(action.labelKey)}
            </span>
          </Link>
        ))}
      </div>
    </div>
  )
}
