import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Sentry } from '../lib/sentry'
import {
  getConsortium,
  getConsortiumStats,
  listMembers,
  listInvitations,
  inviteToConsortium,
  activateConsortium,
  startTraining,
  getTrainingStatus,
  downloadResults,
} from '../api/client'

const statusLabels = {
  draft: { label: 'Borrador', color: 'bg-slate-100 text-slate-700' },
  active: { label: 'Activo', color: 'bg-green-100 text-green-700' },
  training: { label: 'Entrenando', color: 'bg-blue-100 text-blue-700' },
  completed: { label: 'Completado', color: 'bg-purple-100 text-purple-700' },
  archived: { label: 'Archivado', color: 'bg-slate-100 text-slate-500' },
}

const roleLabels = {
  owner: 'Propietario',
  admin: 'Administrador',
  contributor: 'Contribuidor',
  viewer: 'Visualizador',
}

export default function ConsortiumDetail() {
  const { id } = useParams()
  const [consortium, setConsortium] = useState(null)
  const [stats, setStats] = useState(null)
  const [members, setMembers] = useState([])
  const [invitations, setInvitations] = useState([])
  const [trainingStatus, setTrainingStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState('overview')

  // Invite modal
  const [showInviteModal, setShowInviteModal] = useState(false)
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteRole, setInviteRole] = useState('contributor')
  const [inviting, setInviting] = useState(false)

  useEffect(() => {
    loadData()
  }, [id])

  useEffect(() => {
    let interval
    if (consortium?.status === 'training') {
      interval = setInterval(loadTrainingStatus, 5000)
    }
    return () => clearInterval(interval)
  }, [consortium?.status])

  const loadData = async () => {
    try {
      const [consortiumData, statsData, membersData, invitationsData] = await Promise.all([
        getConsortium(id),
        getConsortiumStats(id),
        listMembers(id),
        listInvitations(id),
      ])
      setConsortium(consortiumData)
      setStats(statsData)
      setMembers(membersData)
      setInvitations(invitationsData)

      if (consortiumData.status === 'training') {
        loadTrainingStatus()
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const loadTrainingStatus = async () => {
    try {
      const status = await getTrainingStatus(id)
      setTrainingStatus(status)
      if (status.status === 'completed') {
        loadData() // Refresh all data
      }
    } catch (err) {
      Sentry.captureException(err)
    }
  }

  const handleInvite = async (e) => {
    e.preventDefault()
    setInviting(true)
    try {
      await inviteToConsortium(id, inviteEmail, inviteRole)
      setShowInviteModal(false)
      setInviteEmail('')
      setInviteRole('contributor')
      loadData()
    } catch (err) {
      setError(err.message)
    } finally {
      setInviting(false)
    }
  }

  const handleActivate = async () => {
    try {
      await activateConsortium(id)
      loadData()
    } catch (err) {
      setError(err.message)
    }
  }

  const handleStartTraining = async () => {
    try {
      await startTraining(id)
      loadData()
    } catch (err) {
      setError(err.message)
    }
  }

  const handleDownloadResults = async () => {
    try {
      const blob = await downloadResults(id)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${consortium.name}-results.json`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      a.remove()
    } catch (err) {
      setError(err.message)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-600"></div>
      </div>
    )
  }

  if (!consortium) {
    return (
      <div className="pt-16 text-center">
        <h2 className="text-xl font-bold text-slate-900">Consorcio no encontrado</h2>
        <Link to="/dashboard" className="text-brand-600 hover:text-brand-700 mt-4 inline-block">
          Volver al dashboard
        </Link>
      </div>
    )
  }

  return (
    <div className="pt-16">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-slate-500 mb-6">
        <Link to="/dashboard" className="hover:text-brand-600">Dashboard</Link>
        <span>/</span>
        <span className="text-slate-900">{consortium.name}</span>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
          {error}
          <button onClick={() => setError('')} className="float-right">&times;</button>
        </div>
      )}

      {/* Header */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 mb-6">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-2xl font-bold text-slate-900">{consortium.name}</h1>
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${statusLabels[consortium.status]?.color}`}>
                {statusLabels[consortium.status]?.label}
              </span>
            </div>
            <p className="text-slate-600">{consortium.description}</p>
          </div>

          <div className="flex gap-3">
            {consortium.status === 'draft' && (
              <button
                onClick={handleActivate}
                className="bg-green-600 text-white px-4 py-2 rounded-xl font-medium hover:bg-green-700 transition"
              >
                Activar Consorcio
              </button>
            )}
            {consortium.status === 'active' && (
              <>
                <Link
                  to={`/consortiums/${id}/upload`}
                  className="bg-brand-600 text-white px-4 py-2 rounded-xl font-medium hover:bg-brand-700 transition"
                >
                  Subir Datos
                </Link>
                <button
                  onClick={handleStartTraining}
                  className="bg-purple-600 text-white px-4 py-2 rounded-xl font-medium hover:bg-purple-700 transition"
                >
                  Iniciar Training
                </button>
              </>
            )}
            {consortium.status === 'completed' && (
              <button
                onClick={handleDownloadResults}
                className="bg-green-600 text-white px-4 py-2 rounded-xl font-medium hover:bg-green-700 transition"
              >
                Descargar Resultados
              </button>
            )}
          </div>
        </div>

        {/* Stats */}
        {stats && (
          <div className="grid grid-cols-4 gap-4 mt-6 pt-6 border-t border-slate-100">
            <div>
              <p className="text-sm text-slate-500">Miembros</p>
              <p className="text-2xl font-bold text-slate-900">{stats.total_members}</p>
            </div>
            <div>
              <p className="text-sm text-slate-500">Contribuciones</p>
              <p className="text-2xl font-bold text-slate-900">{stats.total_contributions}</p>
            </div>
            <div>
              <p className="text-sm text-slate-500">Registros totales</p>
              <p className="text-2xl font-bold text-slate-900">{stats.total_records?.toLocaleString() || 0}</p>
            </div>
            <div>
              <p className="text-sm text-slate-500">Tipo de modelo</p>
              <p className="text-lg font-medium text-slate-900">{consortium.model_type}</p>
            </div>
          </div>
        )}
      </div>

      {/* Training Progress */}
      {consortium.status === 'training' && trainingStatus && (
        <div className="bg-blue-50 border border-blue-200 rounded-2xl p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
            <h3 className="font-medium text-blue-900">Entrenamiento en progreso</h3>
          </div>
          <div className="bg-blue-200 rounded-full h-2 mb-2">
            <div
              className="bg-blue-600 rounded-full h-2 transition-all"
              style={{ width: `${trainingStatus.progress || 0}%` }}
            />
          </div>
          <p className="text-sm text-blue-700">
            {trainingStatus.current_step || 'Iniciando...'} - {trainingStatus.progress || 0}%
          </p>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        {[
          { key: 'overview', label: 'General' },
          { key: 'members', label: 'Miembros' },
          { key: 'data', label: 'Datos' },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
              activeTab === tab.key
                ? 'bg-brand-100 text-brand-700'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6">
          <h3 className="text-lg font-medium text-slate-900 mb-4">Informacion del Consorcio</h3>
          <dl className="space-y-4">
            <div>
              <dt className="text-sm text-slate-500">ID</dt>
              <dd className="font-mono text-sm text-slate-900">{consortium.id}</dd>
            </div>
            <div>
              <dt className="text-sm text-slate-500">Creado</dt>
              <dd className="text-slate-900">{new Date(consortium.created_at).toLocaleDateString('es-ES')}</dd>
            </div>
            <div>
              <dt className="text-sm text-slate-500">Tipo de Modelo</dt>
              <dd className="text-slate-900">{consortium.model_type}</dd>
            </div>
          </dl>
        </div>
      )}

      {activeTab === 'members' && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-medium text-slate-900">Miembros</h3>
            <button
              onClick={() => setShowInviteModal(true)}
              className="bg-brand-600 text-white px-4 py-2 rounded-xl text-sm font-medium hover:bg-brand-700 transition"
            >
              Invitar
            </button>
          </div>

          {/* Members list */}
          <div className="space-y-3">
            {members.map((member) => (
              <div
                key={member.company_id}
                className="flex items-center justify-between p-4 bg-slate-50 rounded-xl"
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-brand-600 rounded-full flex items-center justify-center">
                    <span className="text-white font-medium">
                      {member.company_name?.charAt(0) || '?'}
                    </span>
                  </div>
                  <div>
                    <p className="font-medium text-slate-900">{member.company_name}</p>
                    <p className="text-sm text-slate-500">{roleLabels[member.role]}</p>
                  </div>
                </div>
                <span className={`px-2 py-1 rounded text-xs ${
                  member.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-600'
                }`}>
                  {member.status === 'active' ? 'Activo' : member.status}
                </span>
              </div>
            ))}
          </div>

          {/* Pending invitations */}
          {invitations.length > 0 && (
            <div className="mt-6 pt-6 border-t border-slate-100">
              <h4 className="font-medium text-slate-900 mb-4">Invitaciones pendientes</h4>
              <div className="space-y-2">
                {invitations.filter(i => i.status === 'pending').map((inv) => (
                  <div
                    key={inv.id}
                    className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg"
                  >
                    <span className="text-slate-900">{inv.email}</span>
                    <span className="text-xs text-yellow-700">Pendiente</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'data' && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-medium text-slate-900">Contribuciones de Datos</h3>
            {consortium.status === 'active' && (
              <Link
                to={`/consortiums/${id}/upload`}
                className="bg-brand-600 text-white px-4 py-2 rounded-xl text-sm font-medium hover:bg-brand-700 transition"
              >
                Subir Datos
              </Link>
            )}
          </div>

          {stats?.total_contributions === 0 ? (
            <div className="text-center py-8">
              <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              </div>
              <p className="text-slate-600">No hay datos subidos todavia.</p>
              {consortium.status === 'active' && (
                <Link
                  to={`/consortiums/${id}/upload`}
                  className="text-brand-600 font-medium hover:text-brand-700 mt-2 inline-block"
                >
                  Subir primera contribucion
                </Link>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-slate-50 rounded-xl p-4">
                  <p className="text-sm text-slate-500">Contribuciones</p>
                  <p className="text-xl font-bold text-slate-900">{stats?.total_contributions}</p>
                </div>
                <div className="bg-slate-50 rounded-xl p-4">
                  <p className="text-sm text-slate-500">Registros</p>
                  <p className="text-xl font-bold text-slate-900">{stats?.total_records?.toLocaleString()}</p>
                </div>
                <div className="bg-slate-50 rounded-xl p-4">
                  <p className="text-sm text-slate-500">Contribuidores</p>
                  <p className="text-xl font-bold text-slate-900">{stats?.contributors_count}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Invite Modal */}
      {showInviteModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md">
            <h3 className="text-lg font-bold text-slate-900 mb-4">Invitar participante</h3>

            <form onSubmit={handleInvite} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Email
                </label>
                <input
                  type="email"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-brand-500 focus:border-transparent"
                  placeholder="contacto@empresa.com"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Rol
                </label>
                <select
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value)}
                  className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-brand-500 focus:border-transparent"
                >
                  <option value="contributor">Contribuidor</option>
                  <option value="admin">Administrador</option>
                  <option value="viewer">Visualizador</option>
                </select>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  type="button"
                  onClick={() => setShowInviteModal(false)}
                  className="flex-1 px-4 py-3 border border-slate-300 rounded-xl font-medium hover:bg-slate-50 transition"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={inviting}
                  className="flex-1 bg-brand-600 text-white px-4 py-3 rounded-xl font-medium hover:bg-brand-700 transition disabled:opacity-50"
                >
                  {inviting ? 'Enviando...' : 'Enviar invitacion'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
