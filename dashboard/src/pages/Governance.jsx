import { useState, useEffect, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import {
  ShieldCheckIcon,
  DocumentTextIcon,
  UserGroupIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  ChartBarIcon,
  PlusIcon,
  HandThumbUpIcon,
  HandThumbDownIcon,
  ArrowPathIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline'
import * as governanceApi from '../api/governance'
import { isDemoMode } from '../api/client'
import { Sentry } from '../lib/sentry'

// Mock data for demo mode (fallback when API is unavailable)
const MOCK_CONTRIBUTIONS = [
  { id: '1', contributor_name: 'Banco Alpha', record_count: 125000, feature_count: 15, contribution_weight: 45.2, timestamp: '2024-12-08T10:30:00Z', verified: true },
  { id: '2', contributor_name: 'Banco Beta', record_count: 89000, feature_count: 15, contribution_weight: 32.1, timestamp: '2024-12-08T11:00:00Z', verified: true },
  { id: '3', contributor_name: 'Banco Gamma', record_count: 63000, feature_count: 15, contribution_weight: 22.7, timestamp: '2024-12-08T11:30:00Z', verified: false },
]

const MOCK_PROPOSALS = [
  {
    id: 'prop_1',
    title: 'Agregar nuevo miembro: Banco Delta',
    proposal_type: 'add_member',
    proposer_name: 'Banco Alpha',
    status: 'active',
    yes_votes: 2,
    no_votes: 0,
    voting_weight_yes: 77.3,
    voting_weight_no: 0,
    created_at: '2024-12-08T09:00:00Z',
    expires_at: '2024-12-09T09:00:00Z',
  },
  {
    id: 'prop_2',
    title: 'Iniciar entrenamiento de modelo v2',
    proposal_type: 'start_training',
    proposer_name: 'Banco Beta',
    status: 'passed',
    yes_votes: 3,
    no_votes: 0,
    voting_weight_yes: 100,
    voting_weight_no: 0,
    created_at: '2024-12-07T14:00:00Z',
    expires_at: '2024-12-08T14:00:00Z',
    executed_at: '2024-12-08T14:05:00Z',
  },
]

const MOCK_AUDIT = [
  { id: 'audit_1', event_type: 'data_contributed', actor_name: 'Banco Alpha', timestamp: '2024-12-08T10:30:00Z', data: { record_count: 125000 } },
  { id: 'audit_2', event_type: 'proposal_created', actor_name: 'Banco Alpha', timestamp: '2024-12-08T09:00:00Z', data: { title: 'Agregar nuevo miembro' } },
  { id: 'audit_3', event_type: 'member_joined', actor_name: 'Banco Gamma', timestamp: '2024-12-07T15:00:00Z', data: {} },
  { id: 'audit_4', event_type: 'consortium_created', actor_name: 'Banco Alpha', timestamp: '2024-12-07T10:00:00Z', data: {} },
]

const ProposalTypeLabels = {
  add_member: { label: 'Agregar Miembro', color: 'bg-green-100 text-green-800' },
  remove_member: { label: 'Remover Miembro', color: 'bg-red-100 text-red-800' },
  change_model: { label: 'Cambiar Modelo', color: 'bg-blue-100 text-blue-800' },
  start_training: { label: 'Iniciar Training', color: 'bg-purple-100 text-purple-800' },
  distribute_rewards: { label: 'Distribuir Rewards', color: 'bg-yellow-100 text-yellow-800' },
  update_config: { label: 'Actualizar Config', color: 'bg-gray-100 text-gray-800' },
  dissolve: { label: 'Disolver', color: 'bg-red-100 text-red-800' },
}

const AuditEventLabels = {
  consortium_created: 'Consorcio creado',
  member_joined: 'Miembro agregado',
  member_left: 'Miembro salio',
  member_removed: 'Miembro removido',
  data_contributed: 'Datos contribuidos',
  training_started: 'Training iniciado',
  training_completed: 'Training completado',
  proposal_created: 'Propuesta creada',
  proposal_voted: 'Voto registrado',
  proposal_executed: 'Propuesta ejecutada',
  rewards_distributed: 'Rewards distribuidos',
  config_updated: 'Config actualizada',
}

function ContributionCard({ contribution }) {
  return (
    <div className="bg-white rounded-lg border p-4 hover:shadow-md transition">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-10 h-10 bg-brand-100 rounded-full flex items-center justify-center">
            <span className="text-brand-600 font-semibold">
              {contribution.contributor_name.charAt(0)}
            </span>
          </div>
          <div>
            <h4 className="font-medium text-gray-900">{contribution.contributor_name}</h4>
            <p className="text-xs text-gray-500">
              {new Date(contribution.timestamp).toLocaleDateString()}
            </p>
          </div>
        </div>
        {contribution.verified ? (
          <span className="flex items-center gap-1 text-xs text-green-600 bg-green-50 px-2 py-1 rounded-full">
            <CheckCircleIcon className="w-3 h-3" />
            Verificado
          </span>
        ) : (
          <span className="flex items-center gap-1 text-xs text-yellow-600 bg-yellow-50 px-2 py-1 rounded-full">
            <ClockIcon className="w-3 h-3" />
            Pendiente
          </span>
        )}
      </div>
      <div className="grid grid-cols-3 gap-2 text-center">
        <div className="bg-gray-50 rounded p-2">
          <div className="text-lg font-semibold text-gray-900">
            {contribution.record_count.toLocaleString()}
          </div>
          <div className="text-xs text-gray-500">Registros</div>
        </div>
        <div className="bg-gray-50 rounded p-2">
          <div className="text-lg font-semibold text-gray-900">{contribution.feature_count}</div>
          <div className="text-xs text-gray-500">Features</div>
        </div>
        <div className="bg-brand-50 rounded p-2">
          <div className="text-lg font-semibold text-brand-600">
            {contribution.contribution_weight.toFixed(1)}%
          </div>
          <div className="text-xs text-gray-500">Peso</div>
        </div>
      </div>
    </div>
  )
}

function ProposalCard({ proposal, onVote }) {
  const typeInfo = ProposalTypeLabels[proposal.proposal_type] || { label: proposal.proposal_type, color: 'bg-gray-100' }
  const isActive = proposal.status === 'active'
  const totalWeight = proposal.voting_weight_yes + proposal.voting_weight_no
  const yesPercent = totalWeight > 0 ? (proposal.voting_weight_yes / totalWeight) * 100 : 50

  return (
    <div className="bg-white rounded-lg border p-4 hover:shadow-md transition">
      <div className="flex items-start justify-between mb-3">
        <div>
          <span className={`text-xs px-2 py-0.5 rounded-full ${typeInfo.color}`}>
            {typeInfo.label}
          </span>
          <h4 className="font-medium text-gray-900 mt-2">{proposal.title}</h4>
          <p className="text-xs text-gray-500 mt-1">
            Propuesto por {proposal.proposer_name}
          </p>
        </div>
        {proposal.status === 'active' ? (
          <span className="flex items-center gap-1 text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded-full">
            <ClockIcon className="w-3 h-3" />
            Votando
          </span>
        ) : proposal.status === 'passed' ? (
          <span className="flex items-center gap-1 text-xs text-green-600 bg-green-50 px-2 py-1 rounded-full">
            <CheckCircleIcon className="w-3 h-3" />
            Aprobada
          </span>
        ) : (
          <span className="flex items-center gap-1 text-xs text-red-600 bg-red-50 px-2 py-1 rounded-full">
            <XCircleIcon className="w-3 h-3" />
            Rechazada
          </span>
        )}
      </div>

      {/* Voting Progress */}
      <div className="mb-3">
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span>A favor: {proposal.voting_weight_yes.toFixed(1)}%</span>
          <span>En contra: {proposal.voting_weight_no.toFixed(1)}%</span>
        </div>
        <div className="h-2 bg-red-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-green-500 transition-all"
            style={{ width: `${yesPercent}%` }}
          />
        </div>
        <div className="flex justify-between text-xs text-gray-400 mt-1">
          <span>{proposal.yes_votes} votos</span>
          <span>{proposal.no_votes} votos</span>
        </div>
      </div>

      {/* Voting Buttons */}
      {isActive && (
        <div className="flex gap-2">
          <button
            onClick={() => onVote(proposal.id, true)}
            className="flex-1 flex items-center justify-center gap-1 py-2 bg-green-50 text-green-700 rounded-lg hover:bg-green-100 transition text-sm font-medium"
          >
            <HandThumbUpIcon className="w-4 h-4" />
            A favor
          </button>
          <button
            onClick={() => onVote(proposal.id, false)}
            className="flex-1 flex items-center justify-center gap-1 py-2 bg-red-50 text-red-700 rounded-lg hover:bg-red-100 transition text-sm font-medium"
          >
            <HandThumbDownIcon className="w-4 h-4" />
            En contra
          </button>
        </div>
      )}

      {/* Expiration */}
      <div className="mt-3 text-xs text-gray-400">
        {isActive ? (
          <>Expira: {new Date(proposal.expires_at).toLocaleString()}</>
        ) : (
          <>Ejecutada: {new Date(proposal.executed_at || proposal.expires_at).toLocaleString()}</>
        )}
      </div>
    </div>
  )
}

function AuditEvent({ event }) {
  const label = AuditEventLabels[event.event_type] || event.event_type

  return (
    <div className="flex items-start gap-3 py-3 border-b last:border-0">
      <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center flex-shrink-0">
        <DocumentTextIcon className="w-4 h-4 text-gray-500" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-gray-900">
          <span className="font-medium">{event.actor_name}</span>
          {' - '}
          {label}
        </p>
        {event.data && Object.keys(event.data).length > 0 && (
          <p className="text-xs text-gray-500 mt-0.5">
            {JSON.stringify(event.data).slice(0, 50)}...
          </p>
        )}
        <p className="text-xs text-gray-400 mt-1">
          {new Date(event.timestamp).toLocaleString()}
        </p>
      </div>
    </div>
  )
}

export default function Governance() {
  const { consortiumId } = useParams()
  const [activeTab, setActiveTab] = useState('contributions')
  const [contributions, setContributions] = useState([])
  const [proposals, setProposals] = useState([])
  const [auditEvents, setAuditEvents] = useState([])
  const [showNewProposal, setShowNewProposal] = useState(false)
  const [auditValid, setAuditValid] = useState(true)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [usingMockData, setUsingMockData] = useState(false)

  // Default consortium ID for demo purposes
  const effectiveConsortiumId = consortiumId || 'demo_consortium'

  const loadData = useCallback(async () => {
    setLoading(true)
    setError(null)

    // If in demo mode or no consortium ID, use mock data
    if (isDemoMode() || !consortiumId) {
      setContributions(MOCK_CONTRIBUTIONS)
      setProposals(MOCK_PROPOSALS)
      setAuditEvents(MOCK_AUDIT)
      setUsingMockData(true)
      setLoading(false)
      return
    }

    try {
      // Try to load real data from API
      const [contributionsData, proposalsData, auditData] = await Promise.all([
        governanceApi.getContributionSummary(effectiveConsortiumId).catch(() => null),
        governanceApi.getProposals(effectiveConsortiumId).catch(() => null),
        governanceApi.getAuditTrail(effectiveConsortiumId).catch(() => null),
      ])

      if (contributionsData) {
        setContributions(contributionsData)
        setUsingMockData(false)
      } else {
        setContributions(MOCK_CONTRIBUTIONS)
        setUsingMockData(true)
      }

      if (proposalsData) {
        setProposals(proposalsData)
      } else {
        setProposals(MOCK_PROPOSALS)
      }

      if (auditData) {
        setAuditEvents(auditData)
      } else {
        setAuditEvents(MOCK_AUDIT)
      }
    } catch (err) {
      Sentry.captureException(err)
      // Fallback to mock data
      setContributions(MOCK_CONTRIBUTIONS)
      setProposals(MOCK_PROPOSALS)
      setAuditEvents(MOCK_AUDIT)
      setUsingMockData(true)
    } finally {
      setLoading(false)
    }
  }, [consortiumId, effectiveConsortiumId])

  useEffect(() => {
    loadData()
  }, [loadData])

  const handleVote = async (proposalId, support) => {
    if (usingMockData) {
      // Mock vote in demo mode
      setProposals(prev => prev.map(p => {
        if (p.id === proposalId) {
          const newYes = support ? p.yes_votes + 1 : p.yes_votes
          const newNo = support ? p.no_votes : p.no_votes + 1
          const weightChange = 15 // Simulated weight
          return {
            ...p,
            yes_votes: newYes,
            no_votes: newNo,
            voting_weight_yes: support ? p.voting_weight_yes + weightChange : p.voting_weight_yes,
            voting_weight_no: support ? p.voting_weight_no : p.voting_weight_no + weightChange,
          }
        }
        return p
      }))
      alert(`Votaste ${support ? 'A FAVOR' : 'EN CONTRA'} de la propuesta (Demo Mode)`)
      return
    }

    try {
      await governanceApi.castVote(proposalId, support)
      // Reload proposals after voting
      const updatedProposals = await governanceApi.getProposals(effectiveConsortiumId)
      setProposals(updatedProposals)
    } catch (err) {
      alert(`Error al votar: ${err.message}`)
    }
  }

  const handleVerifyAudit = async () => {
    if (usingMockData) {
      setAuditValid(true)
      alert('Audit trail verificado exitosamente (Demo Mode)')
      return
    }

    try {
      const result = await governanceApi.verifyAuditTrail(effectiveConsortiumId)
      setAuditValid(result.valid)
      alert(result.valid
        ? 'Audit trail verificado exitosamente'
        : 'Error de integridad detectado')
    } catch (err) {
      alert(`Error al verificar: ${err.message}`)
    }
  }

  const tabs = [
    { id: 'contributions', label: 'Contribuciones', icon: ChartBarIcon },
    { id: 'proposals', label: 'Propuestas', icon: DocumentTextIcon },
    { id: 'audit', label: 'Audit Trail', icon: ShieldCheckIcon },
  ]

  const totalRecords = contributions.reduce((sum, c) => sum + c.record_count, 0)

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-600"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 py-6 px-4 sm:px-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-2">
            <ShieldCheckIcon className="w-8 h-8 text-brand-600" />
            <h1 className="text-2xl font-bold text-gray-900">Governance</h1>
            {usingMockData && (
              <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full">
                Demo Mode
              </span>
            )}
          </div>
          <p className="text-gray-600">
            Gestiona contribuciones, propuestas y audita todas las operaciones del consorcio
          </p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-xl p-4 border">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-brand-100 rounded-lg flex items-center justify-center">
                <UserGroupIcon className="w-5 h-5 text-brand-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">{contributions.length}</p>
                <p className="text-xs text-gray-500">Miembros</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-xl p-4 border">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                <ChartBarIcon className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">
                  {totalRecords >= 1000 ? `${(totalRecords / 1000).toFixed(0)}K` : totalRecords}
                </p>
                <p className="text-xs text-gray-500">Registros totales</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-xl p-4 border">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                <DocumentTextIcon className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">{proposals.length}</p>
                <p className="text-xs text-gray-500">Propuestas</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-xl p-4 border">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <ShieldCheckIcon className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">{auditEvents.length}</p>
                <p className="text-xs text-gray-500">Eventos audit</p>
              </div>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-xl border mb-6">
          <div className="border-b">
            <div className="flex">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-6 py-4 text-sm font-medium border-b-2 transition ${
                    activeTab === tab.id
                      ? 'border-brand-600 text-brand-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <tab.icon className="w-4 h-4" />
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          <div className="p-6">
            {/* Contributions Tab */}
            {activeTab === 'contributions' && (
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-gray-900">Contribuciones de Datos</h3>
                  <span className="text-sm text-gray-500">
                    Peso de voto basado en contribucion
                  </span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {contributions.map((c) => (
                    <ContributionCard key={c.id} contribution={c} />
                  ))}
                </div>

                {/* Contribution Weight Chart */}
                <div className="mt-6 bg-gray-50 rounded-lg p-4">
                  <h4 className="font-medium text-gray-900 mb-3">Distribucion de Peso</h4>
                  <div className="h-4 bg-gray-200 rounded-full overflow-hidden flex">
                    {contributions.map((c, i) => (
                      <div
                        key={c.id}
                        className={`h-full ${
                          i === 0 ? 'bg-blue-500' : i === 1 ? 'bg-green-500' : 'bg-purple-500'
                        }`}
                        style={{ width: `${c.contribution_weight}%` }}
                        title={`${c.contributor_name}: ${c.contribution_weight.toFixed(1)}%`}
                      />
                    ))}
                  </div>
                  <div className="flex flex-wrap gap-4 mt-2">
                    {contributions.map((c, i) => (
                      <div key={c.id} className="flex items-center gap-2 text-xs">
                        <div
                          className={`w-3 h-3 rounded ${
                            i === 0 ? 'bg-blue-500' : i === 1 ? 'bg-green-500' : 'bg-purple-500'
                          }`}
                        />
                        <span>{c.contributor_name}: {c.contribution_weight.toFixed(1)}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Proposals Tab */}
            {activeTab === 'proposals' && (
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-gray-900">Propuestas de Governance</h3>
                  <button
                    onClick={() => setShowNewProposal(true)}
                    className="flex items-center gap-1 px-3 py-1.5 bg-brand-600 text-white rounded-lg text-sm font-medium hover:bg-brand-700 transition"
                  >
                    <PlusIcon className="w-4 h-4" />
                    Nueva Propuesta
                  </button>
                </div>

                {/* Active Proposals */}
                <div className="mb-6">
                  <h4 className="text-sm font-medium text-gray-700 mb-3">Votacion Activa</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {proposals
                      .filter((p) => p.status === 'active')
                      .map((p) => (
                        <ProposalCard key={p.id} proposal={p} onVote={handleVote} />
                      ))}
                    {proposals.filter((p) => p.status === 'active').length === 0 && (
                      <p className="text-gray-500 text-sm col-span-2">
                        No hay propuestas activas
                      </p>
                    )}
                  </div>
                </div>

                {/* Past Proposals */}
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-3">Historial</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {proposals
                      .filter((p) => p.status !== 'active')
                      .map((p) => (
                        <ProposalCard key={p.id} proposal={p} onVote={handleVote} />
                      ))}
                  </div>
                </div>
              </div>
            )}

            {/* Audit Tab */}
            {activeTab === 'audit' && (
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-gray-900">Audit Trail</h3>
                  <button
                    onClick={handleVerifyAudit}
                    className="flex items-center gap-1 px-3 py-1.5 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200 transition"
                  >
                    <ArrowPathIcon className="w-4 h-4" />
                    Verificar Integridad
                  </button>
                </div>

                {/* Verification Status */}
                <div
                  className={`mb-4 p-3 rounded-lg flex items-center gap-2 ${
                    auditValid ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
                  }`}
                >
                  {auditValid ? (
                    <>
                      <CheckCircleIcon className="w-5 h-5" />
                      <span className="text-sm font-medium">
                        Audit trail integro - Todos los eventos estan encadenados correctamente
                      </span>
                    </>
                  ) : (
                    <>
                      <ExclamationTriangleIcon className="w-5 h-5" />
                      <span className="text-sm font-medium">
                        Error de integridad detectado en el audit trail
                      </span>
                    </>
                  )}
                </div>

                {/* Events List */}
                <div className="bg-gray-50 rounded-lg p-4">
                  {auditEvents.map((event) => (
                    <AuditEvent key={event.id} event={event} />
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Info Box */}
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
          <h4 className="font-medium text-blue-900 mb-2">Sobre Governance</h4>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>El peso de voto se calcula automaticamente segun la cantidad de datos contribuidos</li>
            <li>Las propuestas requieren mayoria simple ponderada para ser aprobadas</li>
            <li>El audit trail es inmutable y verificable criptograficamente</li>
            <li>Todas las operaciones se pueden registrar on-chain en Arbitrum</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
