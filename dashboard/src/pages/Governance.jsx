import { useState } from 'react'

const COLORS = {
  primary: '#4f46e5',
  primaryLight: '#eef2ff',
  success: '#10b981',
  successLight: '#dcfce7',
  warning: '#f59e0b',
  warningLight: '#fef9c3',
  danger: '#ef4444',
  dangerLight: '#fef2f2',
  bg: '#f8fafc',
  card: '#ffffff',
  text: '#1e293b',
  muted: '#64748b',
  border: '#e5e7eb',
  accent: '#06d6a0',
}

const PROPOSALS = [
  {
    id: 1,
    title: 'Aumentar presupuesto de privacidad epsilon a 3.0',
    type: 'Privacidad',
    status: 'activa',
    description: 'Propuesta para incrementar el presupuesto de privacidad diferencial de epsilon=1.0 a epsilon=3.0, permitiendo mayor precision en los modelos a cambio de una ligera reduccion en las garantias de privacidad.',
    votesFor: 12,
    votesAgainst: 3,
    abstentions: 2,
    totalVoters: 25,
    timeRemaining: '2 dias 14h',
    author: 'MedCorp S.A.',
    createdAt: '2026-03-10',
  },
  {
    id: 2,
    title: 'Incorporar nuevo miembro: FinTech Solutions',
    type: 'Membresia',
    status: 'activa',
    description: 'FinTech Solutions solicita unirse al consorcio como contribuidor de datos. La empresa cumple con todos los requisitos de seguridad y ha completado la auditoria de cumplimiento.',
    votesFor: 18,
    votesAgainst: 1,
    abstentions: 0,
    totalVoters: 25,
    timeRemaining: '5 dias 8h',
    author: 'Admin Consorcio',
    createdAt: '2026-03-08',
  },
  {
    id: 3,
    title: 'Migrar esquema de encriptacion a CKKS 256-bit',
    type: 'Tecnica',
    status: 'aprobada',
    description: 'Propuesta aprobada para migrar de CKKS 128-bit a 256-bit, incrementando la seguridad criptografica del consorcio. La migracion se ejecutara en la proxima ventana de mantenimiento.',
    votesFor: 22,
    votesAgainst: 2,
    abstentions: 1,
    totalVoters: 25,
    timeRemaining: null,
    author: 'CryptoLab',
    createdAt: '2026-03-01',
  },
  {
    id: 4,
    title: 'Reducir quorum minimo de votacion a 60%',
    type: 'Gobernanza',
    status: 'rechazada',
    description: 'Se propuso reducir el quorum minimo necesario para aprobar propuestas del 75% al 60%. Fue rechazada por considerar que debilitaria la representatividad en las decisiones.',
    votesFor: 5,
    votesAgainst: 16,
    abstentions: 4,
    totalVoters: 25,
    timeRemaining: null,
    author: 'DataInsights',
    createdAt: '2026-02-25',
  },
  {
    id: 5,
    title: 'Implementar verificacion ZKP para contribuciones',
    type: 'Tecnica',
    status: 'activa',
    description: 'Propuesta para requerir pruebas de conocimiento cero (ZKP) en todas las contribuciones de datos, garantizando la integridad sin revelar el contenido.',
    votesFor: 8,
    votesAgainst: 4,
    abstentions: 1,
    totalVoters: 25,
    timeRemaining: '6 dias 2h',
    author: 'SecureLab',
    createdAt: '2026-03-12',
  },
]

const TYPE_COLORS = {
  Privacidad: { bg: '#fdf4ff', color: '#a855f7' },
  Membresia: { bg: '#eff6ff', color: '#3b82f6' },
  Tecnica: { bg: '#f0fdf4', color: '#22c55e' },
  Gobernanza: { bg: '#fff7ed', color: '#f97316' },
}

const STATUS_COLORS = {
  activa: { bg: COLORS.warningLight, color: COLORS.warning, label: 'Activa' },
  aprobada: { bg: COLORS.successLight, color: COLORS.success, label: 'Aprobada' },
  rechazada: { bg: COLORS.dangerLight, color: COLORS.danger, label: 'Rechazada' },
}

export default function Governance() {
  const [expandedId, setExpandedId] = useState(null)
  const [votes, setVotes] = useState({})

  const activeCount = PROPOSALS.filter(p => p.status === 'activa').length
  const approvedCount = PROPOSALS.filter(p => p.status === 'aprobada').length
  const rejectedCount = PROPOSALS.filter(p => p.status === 'rechazada').length
  const avgQuorum = Math.round(
    PROPOSALS.reduce((sum, p) => sum + ((p.votesFor + p.votesAgainst + p.abstentions) / p.totalVoters) * 100, 0) / PROPOSALS.length
  )

  const handleVote = (proposalId, voteType) => {
    setVotes(prev => ({ ...prev, [proposalId]: voteType }))
  }

  return (
    <div style={{ padding: 32, maxWidth: 1200, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 32, flexWrap: 'wrap', gap: 16 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 700, color: COLORS.text, margin: '0 0 8px' }}>
            Gobernanza
          </h1>
          <p style={{ fontSize: 16, color: COLORS.muted, margin: 0 }}>
            Gestiona propuestas y votaciones del consorcio
          </p>
        </div>
        <button style={{
          padding: '10px 20px', borderRadius: 8, border: 'none',
          background: COLORS.primary, color: '#fff', fontSize: 14,
          fontWeight: 600, cursor: 'pointer',
        }}>
          Nueva Propuesta
        </button>
      </div>

      {/* Stats row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16, marginBottom: 28 }}>
        {[
          { label: 'Propuestas activas', value: activeCount, color: COLORS.warning },
          { label: 'Aprobadas', value: approvedCount, color: COLORS.success },
          { label: 'Rechazadas', value: rejectedCount, color: COLORS.danger },
          { label: 'Quorum promedio', value: `${avgQuorum}%`, color: COLORS.primary },
        ].map((s) => (
          <div key={s.label} style={{
            background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 20,
          }}>
            <p style={{ fontSize: 13, color: COLORS.muted, margin: '0 0 4px' }}>{s.label}</p>
            <p style={{ fontSize: 28, fontWeight: 700, color: s.color, margin: 0 }}>{s.value}</p>
          </div>
        ))}
      </div>

      {/* Proposals list */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {PROPOSALS.map((proposal) => {
          const statusStyle = STATUS_COLORS[proposal.status]
          const typeStyle = TYPE_COLORS[proposal.type] || TYPE_COLORS.Tecnica
          const totalVoted = proposal.votesFor + proposal.votesAgainst + proposal.abstentions
          const forPct = Math.round((proposal.votesFor / totalVoted) * 100)
          const againstPct = Math.round((proposal.votesAgainst / totalVoted) * 100)
          const isExpanded = expandedId === proposal.id
          const userVote = votes[proposal.id]

          return (
            <div key={proposal.id} style={{
              background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`,
              overflow: 'hidden',
            }}>
              {/* Proposal header row */}
              <div
                onClick={() => setExpandedId(isExpanded ? null : proposal.id)}
                style={{
                  padding: '20px 24px', cursor: 'pointer',
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  flexWrap: 'wrap', gap: 12,
                }}
              >
                <div style={{ flex: 1, minWidth: 200 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8, flexWrap: 'wrap' }}>
                    <span style={{
                      padding: '3px 10px', borderRadius: 6, fontSize: 12, fontWeight: 600,
                      background: typeStyle.bg, color: typeStyle.color,
                    }}>
                      {proposal.type}
                    </span>
                    <span style={{
                      padding: '3px 10px', borderRadius: 6, fontSize: 12, fontWeight: 600,
                      background: statusStyle.bg, color: statusStyle.color,
                    }}>
                      {statusStyle.label}
                    </span>
                  </div>
                  <h3 style={{ fontSize: 16, fontWeight: 600, color: COLORS.text, margin: '0 0 6px' }}>
                    {proposal.title}
                  </h3>
                  <p style={{ fontSize: 13, color: COLORS.muted, margin: 0 }}>
                    Por {proposal.author} - {new Date(proposal.createdAt).toLocaleDateString('es-AR')}
                  </p>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 20, flexShrink: 0 }}>
                  {/* Vote bar */}
                  <div style={{ width: 160 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span style={{ fontSize: 12, color: COLORS.success, fontWeight: 600 }}>{forPct}% a favor</span>
                      <span style={{ fontSize: 12, color: COLORS.danger, fontWeight: 600 }}>{againstPct}% en contra</span>
                    </div>
                    <div style={{
                      width: '100%', height: 8, background: COLORS.border, borderRadius: 4, overflow: 'hidden',
                      display: 'flex',
                    }}>
                      <div style={{ height: '100%', background: COLORS.success, width: `${forPct}%` }} />
                      <div style={{ height: '100%', background: COLORS.danger, width: `${againstPct}%` }} />
                    </div>
                    <p style={{ fontSize: 11, color: COLORS.muted, margin: '4px 0 0', textAlign: 'center' }}>
                      {totalVoted}/{proposal.totalVoters} votos emitidos
                    </p>
                  </div>

                  {/* Time remaining */}
                  {proposal.timeRemaining && (
                    <div style={{ textAlign: 'center' }}>
                      <p style={{ fontSize: 13, fontWeight: 600, color: COLORS.warning, margin: 0 }}>
                        {proposal.timeRemaining}
                      </p>
                      <p style={{ fontSize: 11, color: COLORS.muted, margin: '2px 0 0' }}>restante</p>
                    </div>
                  )}

                  {/* Expand arrow */}
                  <span style={{
                    fontSize: 18, color: COLORS.muted, transition: 'transform 0.2s',
                    transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
                  }}>
                    &#9662;
                  </span>
                </div>
              </div>

              {/* Expanded details */}
              {isExpanded && (
                <div style={{
                  padding: '0 24px 24px', borderTop: `1px solid ${COLORS.border}`,
                  paddingTop: 20,
                }}>
                  <p style={{ fontSize: 14, color: COLORS.text, lineHeight: 1.7, margin: '0 0 20px' }}>
                    {proposal.description}
                  </p>

                  <div style={{ display: 'flex', gap: 16, marginBottom: 16, flexWrap: 'wrap' }}>
                    <div style={{ background: COLORS.bg, borderRadius: 8, padding: '12px 20px', textAlign: 'center' }}>
                      <p style={{ fontSize: 20, fontWeight: 700, color: COLORS.success, margin: 0 }}>{proposal.votesFor}</p>
                      <p style={{ fontSize: 12, color: COLORS.muted, margin: '2px 0 0' }}>A favor</p>
                    </div>
                    <div style={{ background: COLORS.bg, borderRadius: 8, padding: '12px 20px', textAlign: 'center' }}>
                      <p style={{ fontSize: 20, fontWeight: 700, color: COLORS.danger, margin: 0 }}>{proposal.votesAgainst}</p>
                      <p style={{ fontSize: 12, color: COLORS.muted, margin: '2px 0 0' }}>En contra</p>
                    </div>
                    <div style={{ background: COLORS.bg, borderRadius: 8, padding: '12px 20px', textAlign: 'center' }}>
                      <p style={{ fontSize: 20, fontWeight: 700, color: COLORS.muted, margin: 0 }}>{proposal.abstentions}</p>
                      <p style={{ fontSize: 12, color: COLORS.muted, margin: '2px 0 0' }}>Abstenciones</p>
                    </div>
                  </div>

                  {proposal.status === 'activa' && (
                    <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                      {[
                        { label: 'A Favor', type: 'for', bg: userVote === 'for' ? COLORS.success : COLORS.successLight, color: userVote === 'for' ? '#fff' : COLORS.success },
                        { label: 'En Contra', type: 'against', bg: userVote === 'against' ? COLORS.danger : COLORS.dangerLight, color: userVote === 'against' ? '#fff' : COLORS.danger },
                        { label: 'Abstencion', type: 'abstain', bg: userVote === 'abstain' ? COLORS.muted : COLORS.bg, color: userVote === 'abstain' ? '#fff' : COLORS.muted },
                      ].map((btn) => (
                        <button
                          key={btn.type}
                          onClick={() => handleVote(proposal.id, btn.type)}
                          style={{
                            padding: '8px 20px', borderRadius: 8, border: 'none',
                            background: btn.bg, color: btn.color, fontSize: 14,
                            fontWeight: 600, cursor: 'pointer',
                          }}
                        >
                          {btn.label}
                        </button>
                      ))}
                      {userVote && (
                        <span style={{ fontSize: 13, color: COLORS.success, alignSelf: 'center', fontWeight: 500 }}>
                          Voto registrado
                        </span>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
