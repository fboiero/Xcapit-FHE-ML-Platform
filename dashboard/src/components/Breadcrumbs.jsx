import { Link, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ChevronRightIcon } from '@heroicons/react/20/solid'

const ROUTE_LABELS = {
  dashboard: 'nav.dashboard',
  governance: 'nav.governance',
  compliance: 'compliance.title',
  quality: 'dataQuality.title',
  marketplace: 'marketplace.title',
  sandbox: 'sandbox.title',
  federated: 'federated.title',
  explainability: 'explainability.title',
  competitive: 'competitive.title',
  ensemble: 'ensemble.title',
  metrics: 'nav.metrics',
  'model-builder': 'nav.modelBuilder',
  'data-upload': 'nav.dataUpload',
  training: 'nav.training',
  results: 'nav.results',
  comparison: 'nav.comparison',
  'data-explorer': 'nav.dataExplorer',
  monitoring: 'nav.monitoring',
  settings: 'nav.settings',
  deployment: 'nav.deployment',
  'audit-log': 'nav.auditLog',
  'api-playground': 'nav.apiPlayground',
  notifications: 'nav.notifications',
  team: 'nav.team',
  billing: 'nav.billing',
  reports: 'nav.reports',
  workflows: 'nav.workflows',
  admin: 'nav.admin',
  demo: 'nav.technicalDemo',
  consortiums: 'dashboard.consortiums.title',
  new: 'nav.createConsortium',
}

export default function Breadcrumbs() {
  const { t } = useTranslation()
  const location = useLocation()

  const segments = location.pathname.split('/').filter(Boolean)

  // Hide on dashboard root
  if (segments.length <= 1 && segments[0] === 'dashboard') {
    return null
  }

  const crumbs = segments.map((segment, index) => {
    const path = '/' + segments.slice(0, index + 1).join('/')
    const isLast = index === segments.length - 1
    const labelKey = ROUTE_LABELS[segment]

    // Dynamic params (UUIDs, IDs) → show as "Detail"
    const isDynamic = !labelKey && /^[0-9a-f-]+$/i.test(segment)
    const label = labelKey ? t(labelKey) : isDynamic ? t('common.details') : segment

    return { label, path, isLast }
  })

  return (
    <nav aria-label="Breadcrumb" className="mb-4">
      <ol className="flex items-center gap-1.5 text-sm">
        <li>
          <Link to="/dashboard" className="text-slate-500 hover:text-brand-600 transition-colors">
            {t('nav.dashboard')}
          </Link>
        </li>
        {crumbs.map((crumb, index) => {
          // Skip the "dashboard" segment since we already show it as Home
          if (index === 0 && crumb.path === '/dashboard') return null

          return (
            <li key={crumb.path} className="flex items-center gap-1.5">
              <ChevronRightIcon className="w-3 h-3 text-slate-400 flex-shrink-0" />
              {crumb.isLast ? (
                <span className="font-medium text-slate-900">{crumb.label}</span>
              ) : (
                <Link
                  to={crumb.path}
                  className="text-slate-500 hover:text-brand-600 transition-colors"
                >
                  {crumb.label}
                </Link>
              )}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}
