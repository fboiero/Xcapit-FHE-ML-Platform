import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { listConsortiums, isDemoMode } from '../api/client'
import { useDemo } from '../context/DemoContext'
import { SkeletonCard, EmptyState } from '../components/ui'
import WelcomeOnboarding from '../components/WelcomeOnboarding'
import {
  BuildingOffice2Icon,
  HeartIcon,
  ShoppingBagIcon,
  ShieldCheckIcon,
  SparklesIcon,
  ChartBarIcon,
  PlusIcon,
  UserGroupIcon,
  CubeIcon
} from '@heroicons/react/24/outline'

// Animated counter hook
function useCounter(end, duration = 1500, startOnMount = true) {
  const [count, setCount] = useState(0)

  useEffect(() => {
    if (!startOnMount) return
    let startTime = null
    const endValue = parseInt(String(end).replace(/[^0-9]/g, '')) || 0

    const animate = (timestamp) => {
      if (!startTime) startTime = timestamp
      const progress = Math.min((timestamp - startTime) / duration, 1)
      setCount(Math.floor(progress * endValue))
      if (progress < 1) requestAnimationFrame(animate)
    }
    requestAnimationFrame(animate)
  }, [end, duration, startOnMount])

  return count
}

// Stat card with animation
function AnimatedStatCard({ label, value, icon: Icon, delay = 0 }) {
  const [visible, setVisible] = useState(false)
  const numericValue = parseInt(String(value).replace(/[^0-9]/g, '')) || 0
  const suffix = String(value).replace(/[0-9]/g, '')
  const count = useCounter(numericValue, 1500, visible)

  useEffect(() => {
    const timer = setTimeout(() => setVisible(true), delay)
    return () => clearTimeout(timer)
  }, [delay])

  return (
    <div
      className={`bg-white rounded-xl border border-slate-200 p-4 transition-all duration-500 hover:shadow-md hover:border-brand-200 ${
        visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
      }`}
    >
      <div className="flex items-center gap-2 mb-1">
        {Icon && <Icon className="w-4 h-4 text-brand-500" />}
        <span className="text-xs text-slate-500 capitalize">
          {label.replace(/([A-Z])/g, ' $1').trim()}
        </span>
      </div>
      <div className="text-2xl font-bold text-slate-900">
        {count}{suffix}
      </div>
    </div>
  )
}

const statusLabels = {
  draft: { label: 'Borrador', color: 'bg-slate-100 text-slate-700' },
  active: { label: 'Activo', color: 'bg-green-100 text-green-700' },
  training: { label: 'Entrenando', color: 'bg-blue-100 text-blue-700' },
  completed: { label: 'Completado', color: 'bg-purple-100 text-purple-700' },
  archived: { label: 'Archivado', color: 'bg-slate-100 text-slate-500' },
  pending: { label: 'Pendiente', color: 'bg-yellow-100 text-yellow-700' },
}

const ICONS = {
  BuildingOffice2Icon,
  HeartIcon,
  ShoppingBagIcon,
  ShieldCheckIcon
}

export default function Dashboard() {
  const { t, i18n } = useTranslation()
  const { isDemoMode: contextDemoMode, getScenarioData, scenarios, switchScenario, currentScenario } = useDemo()
  const [consortiums, setConsortiums] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [filter, setFilter] = useState('all')

  const isDemo = isDemoMode() || contextDemoMode
  const currentLang = i18n.language?.startsWith('es') ? 'es' : 'en'

  useEffect(() => {
    loadConsortiums()
  }, [filter, currentScenario])

  const loadConsortiums = async () => {
    // If in demo mode, use mock data
    if (isDemo) {
      const scenarioData = getScenarioData()
      let mockConsortiums = scenarioData?.consortiums || []

      if (filter !== 'all') {
        mockConsortiums = mockConsortiums.filter(c => c.status === filter)
      }

      setConsortiums(mockConsortiums)
      setLoading(false)
      return
    }

    try {
      const data = await listConsortiums(filter === 'all' ? null : filter)
      setConsortiums(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="pt-16">
        {/* Skeleton header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <div className="h-8 bg-slate-200 rounded w-48 mb-2 animate-pulse"></div>
            <div className="h-4 bg-slate-200 rounded w-64 animate-pulse"></div>
          </div>
          <div className="h-10 bg-slate-200 rounded-xl w-36 animate-pulse"></div>
        </div>
        {/* Skeleton filter tabs */}
        <div className="flex gap-2 mb-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-10 bg-slate-200 rounded-lg w-24 animate-pulse"></div>
          ))}
        </div>
        {/* Skeleton cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      </div>
    )
  }

  const scenarioData = isDemo ? getScenarioData() : null

  return (
    <div className="pt-16">
      {/* Demo Mode Banner */}
      {isDemo && (
        <div className="bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-xl p-4 mb-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <SparklesIcon className="w-6 h-6" />
            <div>
              <h3 className="font-semibold">
                {currentLang === 'es' ? 'Modo Demo Activo' : 'Demo Mode Active'}
              </h3>
              <p className="text-sm text-white/80">
                {currentLang === 'es'
                  ? 'Explorando con datos ficticios. Selecciona una industria para cambiar el escenario.'
                  : 'Exploring with mock data. Select an industry to change scenario.'}
              </p>
            </div>
          </div>
          <div className="flex gap-2 flex-wrap">
            {Object.entries(scenarios).map(([key, ind]) => {
              const IndIcon = ICONS[ind.icon]
              const isActive = currentScenario === key
              return (
                <button
                  key={key}
                  onClick={() => switchScenario(key)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition ${
                    isActive
                      ? 'bg-white text-orange-600'
                      : 'bg-white/20 hover:bg-white/30'
                  }`}
                >
                  <IndIcon className="w-4 h-4" />
                  {currentLang === 'es' ? ind.name : ind.nameEn}
                </button>
              )
            })}
          </div>
        </div>
      )}

      {/* Welcome Onboarding */}
      {!isDemo && <WelcomeOnboarding />}

      {/* Demo Stats */}
      {isDemo && scenarioData && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          {Object.entries(scenarioData.stats).slice(0, 4).map(([key, value], index) => (
            <AnimatedStatCard
              key={key}
              label={key}
              value={value}
              icon={ChartBarIcon}
              delay={index * 100}
            />
          ))}
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            {currentLang === 'es' ? 'Mis Consorcios' : 'My Consortiums'}
          </h1>
          <p className="text-slate-600">
            {currentLang === 'es' ? 'Gestiona tus colaboraciones de datos' : 'Manage your data collaborations'}
          </p>
        </div>
        <Link
          to="/consortiums/new"
          className="bg-gradient-to-r from-brand-600 to-brand-700 text-white px-5 py-2.5 rounded-xl font-medium hover:from-brand-700 hover:to-brand-800 hover:shadow-lg hover:shadow-brand-500/25 transition-all duration-300 flex items-center gap-2 group"
        >
          <PlusIcon className="w-5 h-5 group-hover:rotate-90 transition-transform duration-300" />
          {currentLang === 'es' ? 'Crear Consorcio' : 'Create Consortium'}
        </Link>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-2 mb-6">
        {[
          { key: 'all', label: 'Todos' },
          { key: 'active', label: 'Activos' },
          { key: 'training', label: 'Entrenando' },
          { key: 'completed', label: 'Completados' },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setFilter(tab.key)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
              filter === tab.key
                ? 'bg-brand-100 text-brand-700'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}

      {/* Consortiums grid */}
      {consortiums.length === 0 ? (
        <EmptyState
          icon={UserGroupIcon}
          title={t('emptyState.noConsortiums')}
          description={t('emptyState.noConsortiumsDescription')}
          action={{
            label: currentLang === 'es' ? 'Crear Consorcio' : 'Create Consortium',
            to: '/consortiums/new',
            icon: PlusIcon,
          }}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {consortiums.map((consortium, index) => (
            <Link
              key={consortium.id}
              to={`/consortiums/${consortium.id}`}
              className="bg-white rounded-2xl border border-slate-200 p-6 hover:shadow-xl hover:border-brand-300 hover:-translate-y-1 transition-all duration-300 group animate-fade-in"
              style={{ animationDelay: `${index * 75}ms` }}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="w-12 h-12 bg-gradient-to-br from-brand-100 to-brand-200 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                  <UserGroupIcon className="w-6 h-6 text-brand-600" />
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${statusLabels[consortium.status]?.color || 'bg-slate-100'}`}>
                  {statusLabels[consortium.status]?.label || consortium.status}
                </span>
              </div>

              <h3 className="text-lg font-semibold text-slate-900 mb-2 group-hover:text-brand-600 transition-colors">
                {consortium.name}
              </h3>
              <p className="text-slate-600 text-sm mb-4 line-clamp-2">
                {consortium.description}
              </p>

              <div className="flex items-center gap-4 text-sm text-slate-500">
                <div className="flex items-center gap-1.5">
                  <UserGroupIcon className="w-4 h-4" />
                  <span>{consortium.member_count || 1} miembros</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <CubeIcon className="w-4 h-4" />
                  <span>{consortium.model_type}</span>
                </div>
              </div>

              {/* Hover indicator */}
              <div className="mt-4 pt-4 border-t border-slate-100 opacity-0 group-hover:opacity-100 transition-opacity">
                <span className="text-brand-600 text-sm font-medium flex items-center gap-1">
                  Ver detalles
                  <svg className="w-4 h-4 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}

      <style>{`
        @keyframes fade-in {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fade-in {
          animation: fade-in 0.5s ease-out forwards;
          opacity: 0;
        }
      `}</style>
    </div>
  )
}
