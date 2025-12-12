import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  BuildingOffice2Icon,
  HeartIcon,
  ShoppingBagIcon,
  ShieldCheckIcon,
  PlayIcon,
  ChartBarIcon,
  LockClosedIcon,
  UserGroupIcon,
  CpuChipIcon,
  ArrowRightIcon,
  CheckCircleIcon,
  SparklesIcon,
  EyeSlashIcon,
  RocketLaunchIcon
} from '@heroicons/react/24/outline'
import LanguageSwitcher from '../components/LanguageSwitcher'
import { INDUSTRY_SCENARIOS, DEMO_API_KEY, ACME_CORP } from '../context/DemoContext'

const ICONS = {
  BuildingOffice2Icon,
  HeartIcon,
  ShoppingBagIcon,
  ShieldCheckIcon
}

export default function SandboxDemo() {
  const { t, i18n } = useTranslation()
  const navigate = useNavigate()
  const [selectedScenario, setSelectedScenario] = useState('finance')
  const [isAnimating, setIsAnimating] = useState(false)

  const currentLang = i18n.language?.startsWith('es') ? 'es' : 'en'
  const scenario = INDUSTRY_SCENARIOS[selectedScenario]
  const Icon = ICONS[scenario.icon]

  const handleStartDemo = (mode) => {
    setIsAnimating(true)
    localStorage.setItem('xcapit_api_key', DEMO_API_KEY)
    localStorage.setItem('xcapit_demo_scenario', selectedScenario)

    setTimeout(() => {
      if (mode === 'dashboard') {
        navigate('/dashboard')
      } else if (mode === 'interactive') {
        navigate('/demo-consorcio')
      }
    }, 500)
  }

  const colorClasses = {
    indigo: {
      bg: 'bg-indigo-50',
      border: 'border-indigo-200',
      text: 'text-indigo-600',
      button: 'bg-indigo-600 hover:bg-indigo-700',
      light: 'bg-indigo-100'
    },
    rose: {
      bg: 'bg-rose-50',
      border: 'border-rose-200',
      text: 'text-rose-600',
      button: 'bg-rose-600 hover:bg-rose-700',
      light: 'bg-rose-100'
    },
    purple: {
      bg: 'bg-purple-50',
      border: 'border-purple-200',
      text: 'text-purple-600',
      button: 'bg-purple-600 hover:bg-purple-700',
      light: 'bg-purple-100'
    },
    emerald: {
      bg: 'bg-emerald-50',
      border: 'border-emerald-200',
      text: 'text-emerald-600',
      button: 'bg-emerald-600 hover:bg-emerald-700',
      light: 'bg-emerald-100'
    }
  }

  const colors = colorClasses[scenario.color]

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="border-b border-slate-700/50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-brand-600 rounded-lg flex items-center justify-center">
              <LockClosedIcon className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-semibold text-white">Xcapit</span>
            <span className="text-xl font-light text-brand-400">Privacy</span>
          </Link>
          <div className="flex items-center gap-4">
            <LanguageSwitcher variant="minimal" />
            <Link to="/login" className="text-slate-300 hover:text-white text-sm">
              {currentLang === 'es' ? 'Iniciar sesion' : 'Sign in'}
            </Link>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-12">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-brand-600/20 rounded-full text-brand-400 text-sm mb-6">
            <SparklesIcon className="w-4 h-4" />
            {currentLang === 'es' ? 'Sandbox de Demostracion' : 'Demo Sandbox'}
          </div>
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
            {currentLang === 'es'
              ? 'Explora la Plataforma sin Registro'
              : 'Explore the Platform Without Signing Up'}
          </h1>
          <p className="text-xl text-slate-300 max-w-2xl mx-auto">
            {currentLang === 'es'
              ? 'Selecciona un escenario de industria y experimenta con datos de prueba'
              : 'Select an industry scenario and experiment with test data'}
          </p>
        </div>

        {/* Industry Selector */}
        <div className="mb-12">
          <h2 className="text-lg font-semibold text-white text-center mb-6">
            {currentLang === 'es' ? 'Selecciona tu industria' : 'Select your industry'}
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(INDUSTRY_SCENARIOS).map(([key, ind]) => {
              const IndIcon = ICONS[ind.icon]
              const isSelected = selectedScenario === key
              const indColors = colorClasses[ind.color]

              return (
                <button
                  key={key}
                  onClick={() => setSelectedScenario(key)}
                  className={`p-6 rounded-xl border-2 transition-all ${
                    isSelected
                      ? `${indColors.bg} ${indColors.border} scale-105 shadow-lg`
                      : 'bg-slate-800/50 border-slate-700 hover:border-slate-600'
                  }`}
                >
                  <IndIcon className={`w-8 h-8 mx-auto mb-3 ${
                    isSelected ? indColors.text : 'text-slate-400'
                  }`} />
                  <h3 className={`font-semibold ${
                    isSelected ? indColors.text : 'text-white'
                  }`}>
                    {currentLang === 'es' ? ind.name : ind.nameEn}
                  </h3>
                  <p className={`text-sm mt-1 ${
                    isSelected ? 'text-slate-600' : 'text-slate-400'
                  }`}>
                    {currentLang === 'es' ? ind.description : ind.descriptionEn}
                  </p>
                  {isSelected && (
                    <CheckCircleIcon className={`w-5 h-5 ${indColors.text} mx-auto mt-3`} />
                  )}
                </button>
              )
            })}
          </div>
        </div>

        {/* Selected Scenario Details */}
        <div className={`rounded-2xl border-2 ${colors.border} ${colors.bg} p-8 mb-12`}>
          <div className="flex flex-col lg:flex-row gap-8">
            {/* Left: Client Info */}
            <div className="lg:w-1/3">
              <div className="flex items-center gap-4 mb-6">
                <div className={`w-16 h-16 ${colors.button} rounded-xl flex items-center justify-center text-white text-2xl font-bold`}>
                  {scenario.client.logo}
                </div>
                <div>
                  <h3 className="text-xl font-bold text-slate-900">{scenario.client.name}</h3>
                  <p className="text-slate-600">{scenario.client.industry}</p>
                </div>
              </div>

              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-500">{currentLang === 'es' ? 'Empleados' : 'Employees'}</span>
                  <span className="font-medium text-slate-900">{scenario.client.employees}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">{currentLang === 'es' ? 'Region' : 'Region'}</span>
                  <span className="font-medium text-slate-900">{scenario.client.region}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">{currentLang === 'es' ? 'Consorcios' : 'Consortiums'}</span>
                  <span className="font-medium text-slate-900">{scenario.consortiums.length}</span>
                </div>
              </div>
            </div>

            {/* Right: Stats Grid */}
            <div className="lg:w-2/3">
              <h4 className="font-semibold text-slate-900 mb-4">
                {currentLang === 'es' ? 'Metricas del Escenario' : 'Scenario Metrics'}
              </h4>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {Object.entries(scenario.stats).slice(0, 6).map(([key, value]) => (
                  <div key={key} className="bg-white rounded-lg p-4 shadow-sm">
                    <div className={`text-2xl font-bold ${colors.text}`}>{value}</div>
                    <div className="text-xs text-slate-500 capitalize">
                      {key.replace(/([A-Z])/g, ' $1').trim()}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Consortiums Preview */}
          <div className="mt-8 pt-8 border-t border-slate-200">
            <h4 className="font-semibold text-slate-900 mb-4">
              {currentLang === 'es' ? 'Consorcios Activos' : 'Active Consortiums'}
            </h4>
            <div className="grid md:grid-cols-2 gap-4">
              {scenario.consortiums.map((cons) => (
                <div key={cons.id} className="bg-white rounded-lg p-4 shadow-sm">
                  <div className="flex items-start justify-between mb-2">
                    <h5 className="font-medium text-slate-900">{cons.name}</h5>
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                      cons.status === 'active' ? 'bg-green-100 text-green-700' :
                      cons.status === 'training' ? 'bg-blue-100 text-blue-700' :
                      'bg-gray-100 text-gray-700'
                    }`}>
                      {cons.status}
                    </span>
                  </div>
                  <p className="text-sm text-slate-600 mb-3">{cons.description}</p>
                  <div className="flex items-center gap-4 text-xs text-slate-500">
                    <span className="flex items-center gap-1">
                      <UserGroupIcon className="w-4 h-4" />
                      {cons.members} {currentLang === 'es' ? 'miembros' : 'members'}
                    </span>
                    <span className="flex items-center gap-1">
                      <CpuChipIcon className="w-4 h-4" />
                      {cons.model_type}
                    </span>
                    {cons.accuracy && (
                      <span className="flex items-center gap-1">
                        <ChartBarIcon className="w-4 h-4" />
                        {cons.accuracy}%
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
          <button
            onClick={() => handleStartDemo('dashboard')}
            disabled={isAnimating}
            className={`flex items-center justify-center gap-2 px-8 py-4 ${colors.button} text-white rounded-xl font-semibold text-lg transition-all shadow-lg hover:shadow-xl disabled:opacity-50`}
          >
            <RocketLaunchIcon className="w-6 h-6" />
            {currentLang === 'es' ? 'Entrar al Dashboard Demo' : 'Enter Demo Dashboard'}
            <ArrowRightIcon className="w-5 h-5" />
          </button>

          <button
            onClick={() => handleStartDemo('interactive')}
            disabled={isAnimating}
            className="flex items-center justify-center gap-2 px-8 py-4 bg-slate-700 hover:bg-slate-600 text-white rounded-xl font-semibold text-lg transition-all"
          >
            <PlayIcon className="w-6 h-6" />
            {currentLang === 'es' ? 'Ver Demo Interactiva' : 'View Interactive Demo'}
          </button>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-6 mb-12">
          <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
            <EyeSlashIcon className="w-10 h-10 text-brand-400 mb-4" />
            <h3 className="text-lg font-semibold text-white mb-2">
              {currentLang === 'es' ? 'Sin Datos Reales' : 'No Real Data'}
            </h3>
            <p className="text-slate-400 text-sm">
              {currentLang === 'es'
                ? 'Todos los datos son sinteticos y ficticios para propositos de demostracion'
                : 'All data is synthetic and fictional for demonstration purposes'}
            </p>
          </div>

          <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
            <LockClosedIcon className="w-10 h-10 text-brand-400 mb-4" />
            <h3 className="text-lg font-semibold text-white mb-2">
              {currentLang === 'es' ? 'FHE Simulado' : 'Simulated FHE'}
            </h3>
            <p className="text-slate-400 text-sm">
              {currentLang === 'es'
                ? 'Experimenta el flujo de encriptacion homomorfica sin configuracion'
                : 'Experience the homomorphic encryption flow without any setup'}
            </p>
          </div>

          <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
            <SparklesIcon className="w-10 h-10 text-brand-400 mb-4" />
            <h3 className="text-lg font-semibold text-white mb-2">
              {currentLang === 'es' ? 'Funcionalidad Completa' : 'Full Functionality'}
            </h3>
            <p className="text-slate-400 text-sm">
              {currentLang === 'es'
                ? 'Accede a todas las funciones: governance, compliance, training, etc.'
                : 'Access all features: governance, compliance, training, etc.'}
            </p>
          </div>
        </div>

        {/* Demo Credentials Box */}
        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 max-w-2xl mx-auto text-center">
          <h3 className="text-lg font-semibold text-white mb-4">
            {currentLang === 'es' ? 'O usa credenciales de demo directamente' : 'Or use demo credentials directly'}
          </h3>
          <div className="bg-slate-900 rounded-lg p-4 mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-slate-400 text-sm">API Key:</span>
              <code className="text-brand-400 font-mono text-sm">{DEMO_API_KEY}</code>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400 text-sm">Email:</span>
              <code className="text-brand-400 font-mono text-sm">demo@xcapit.com</code>
            </div>
          </div>
          <Link
            to="/login"
            className="text-brand-400 hover:text-brand-300 text-sm underline"
          >
            {currentLang === 'es' ? 'Ir a la pagina de login' : 'Go to login page'}
          </Link>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-slate-700/50 mt-12">
        <div className="max-w-7xl mx-auto px-6 py-8 text-center">
          <p className="text-slate-500 text-sm">
            {currentLang === 'es'
              ? 'Este es un ambiente de demostracion. Para uso en produccion, contactanos.'
              : 'This is a demo environment. For production use, contact us.'}
          </p>
          <div className="flex justify-center gap-6 mt-4">
            <Link to="/" className="text-slate-400 hover:text-white text-sm">
              {currentLang === 'es' ? 'Inicio' : 'Home'}
            </Link>
            <Link to="/demos" className="text-slate-400 hover:text-white text-sm">
              {currentLang === 'es' ? 'Mas Demos' : 'More Demos'}
            </Link>
            <Link to="/register" className="text-slate-400 hover:text-white text-sm">
              {currentLang === 'es' ? 'Registrarse' : 'Sign Up'}
            </Link>
          </div>
        </div>
      </footer>
    </div>
  )
}
