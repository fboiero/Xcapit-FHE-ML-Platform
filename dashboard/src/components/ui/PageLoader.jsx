import { useTranslation } from 'react-i18next'

const sizes = {
  sm: { spinner: 'w-6 h-6 border-2', container: 'min-h-[20vh]' },
  md: { spinner: 'w-10 h-10 border-4', container: 'min-h-[60vh]' },
  lg: { spinner: 'w-14 h-14 border-4', container: 'min-h-[80vh]' },
}

export default function PageLoader({ message, size = 'md', fullScreen = false }) {
  const { t } = useTranslation()
  const { spinner, container } = sizes[size] || sizes.md

  return (
    <div
      className={`flex items-center justify-center ${fullScreen ? 'min-h-screen' : container}`}
      role="status"
    >
      <div className="flex flex-col items-center gap-4">
        <div
          className={`${spinner} border-brand-600 border-t-transparent rounded-full animate-spin`}
        />
        <p className="text-sm text-slate-500">{message || t('common.loading')}</p>
      </div>
    </div>
  )
}
