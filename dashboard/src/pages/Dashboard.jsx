import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { listConsortiums, isDemoMode } from '../api/client'
import { useDemo } from '../context/DemoContext'
import {
  BuildingOffice2Icon,
  HeartIcon,
  ShoppingBagIcon,
  ShieldCheckIcon,
  SparklesIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline'

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
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-600"></div>
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

      {/* Demo Stats */}
      {isDemo && scenarioData && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          {Object.entries(scenarioData.stats).slice(0, 4).map(([key, value]) => (
            <div key={key} className="bg-white rounded-xl border border-slate-200 p-4">
              <div className="flex items-center gap-2 mb-1">
                <ChartBarIcon className="w-4 h-4 text-slate-400" />
                <span className="text-xs text-slate-500 capitalize">
                  {key.replace(/([A-Z])/g, ' $1').trim()}
                </span>
              </div>
              <div className="text-xl font-bold text-slate-900">{value}</div>
            </div>
          ))}
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between mb-8">
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
          className="bg-brand-600 text-white px-4 py-2 rounded-xl font-medium hover:bg-brand-700 transition flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
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
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center">
          <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-slate-900 mb-2">No hay consorcios</h3>
          <p className="text-slate-600 mb-6">
            Crea tu primer consorcio para comenzar a colaborar.
          </p>
          <Link
            to="/consortiums/new"
            className="inline-flex items-center gap-2 bg-brand-600 text-white px-4 py-2 rounded-xl font-medium hover:bg-brand-700 transition"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Crear Consorcio
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {consortiums.map((consortium) => (
            <Link
              key={consortium.id}
              to={`/consortiums/${consortium.id}`}
              className="bg-white rounded-2xl border border-slate-200 p-6 hover:shadow-lg hover:border-brand-200 transition group"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="w-12 h-12 bg-brand-100 rounded-xl flex items-center justify-center">
                  <svg className="w-6 h-6 text-brand-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${statusLabels[consortium.status]?.color || 'bg-slate-100'}`}>
                  {statusLabels[consortium.status]?.label || consortium.status}
                </span>
              </div>

              <h3 className="text-lg font-semibold text-slate-900 mb-2 group-hover:text-brand-600 transition">
                {consortium.name}
              </h3>
              <p className="text-slate-600 text-sm mb-4 line-clamp-2">
                {consortium.description}
              </p>

              <div className="flex items-center gap-4 text-sm text-slate-500">
                <div className="flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
                  </svg>
                  <span>{consortium.member_count || 1} miembros</span>
                </div>
                <div className="flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  <span>{consortium.model_type}</span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
