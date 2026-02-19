import { useState, useEffect } from 'react'
import { useSearchParams, useNavigate, Link } from 'react-router-dom'
import { acceptInvitation, isAuthenticated, setApiKey, getCurrentCompany } from '../api/client'

export default function JoinConsortium() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [inviteCode, setInviteCode] = useState(searchParams.get('code') || '')
  const [apiKey, setApiKeyValue] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(null)
  const [step, setStep] = useState(isAuthenticated() ? 'join' : 'auth')

  useEffect(() => {
    if (isAuthenticated()) {
      setStep('join')
    }
  }, [])

  const handleAuth = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      setApiKey(apiKey)
      await getCurrentCompany()
      setStep('join')
    } catch (err) {
      setApiKey('')
      setError('API Key invalida. Verifica que sea correcta.')
    } finally {
      setLoading(false)
    }
  }

  const handleJoin = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const result = await acceptInvitation(inviteCode)
      setSuccess(result)
      setTimeout(() => navigate(`/consortiums/${result.consortium_id}`), 2000)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-slate-900 mb-2">Te uniste al consorcio!</h2>
          <p className="text-slate-600 mb-6">
            Ahora puedes contribuir datos y participar en el entrenamiento.
          </p>
          <p className="text-sm text-slate-500">Redirigiendo...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
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

        <h1 className="text-2xl font-bold text-slate-900 text-center mb-2">Unirse a Consorcio</h1>
        <p className="text-slate-600 text-center mb-8">
          {step === 'auth'
            ? 'Primero, ingresa tu API Key para identificarte.'
            : 'Ingresa el codigo de invitacion para unirte.'}
        </p>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {step === 'auth' ? (
          <form onSubmit={handleAuth} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                API Key
              </label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKeyValue(e.target.value)}
                className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-brand-500 focus:border-transparent transition font-mono"
                placeholder="xcp_..."
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-brand-600 text-white py-3 px-4 rounded-xl font-medium hover:bg-brand-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Verificando...' : 'Continuar'}
            </button>

            <p className="text-center text-slate-600">
              No tienes cuenta?{' '}
              <Link to="/register" className="text-brand-600 font-medium hover:text-brand-700">
                Registrar empresa
              </Link>
            </p>
          </form>
        ) : (
          <form onSubmit={handleJoin} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Codigo de invitacion
              </label>
              <input
                type="text"
                value={inviteCode}
                onChange={(e) => setInviteCode(e.target.value)}
                className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-brand-500 focus:border-transparent transition font-mono text-center text-lg tracking-wider"
                placeholder="XXXXXX"
                maxLength={6}
                required
              />
              <p className="text-xs text-slate-500 mt-2 text-center">
                Recibiste este codigo por email al ser invitado.
              </p>
            </div>

            <button
              type="submit"
              disabled={loading || inviteCode.length < 6}
              className="w-full bg-brand-600 text-white py-3 px-4 rounded-xl font-medium hover:bg-brand-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Uniendose...' : 'Unirse al Consorcio'}
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
