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
  purple: '#8b5cf6',
  purpleLight: '#f5f3ff',
}

const CURRENT_ROUND = {
  number: 6,
  phase: 'collecting',
  phaseLabel: 'Recolectando',
  participantsCurrent: 3,
  participantsTotal: 5,
  progress: 60,
  startedAt: '2026-03-14T10:30:00',
  estimatedEnd: '2026-03-14T18:00:00',
}

const ROUNDS_HISTORY = [
  { round: 5, participants: 5, method: 'FedAvg', accuracy: 93.2, epsilonUsed: 0.3, status: 'completed' },
  { round: 4, participants: 5, method: 'FedAvg', accuracy: 91.8, epsilonUsed: 0.3, status: 'completed' },
  { round: 3, participants: 4, method: 'FedAvg', accuracy: 89.5, epsilonUsed: 0.4, status: 'completed' },
  { round: 2, participants: 5, method: 'FedProx', accuracy: 86.1, epsilonUsed: 0.5, status: 'completed' },
  { round: 1, participants: 3, method: 'FedProx', accuracy: 82.3, epsilonUsed: 0.5, status: 'completed' },
]

const PRIVACY_BUDGET = {
  epsilonUsed: 2.0,
  epsilonTotal: 5.0,
}

const PARTICIPANTS = [
  { name: 'MedCorp S.A.', records: 12400, contribution: 'Completada', zkpVerified: true, lastActive: '2026-03-14T11:45:00' },
  { name: 'HealthData Inc.', records: 8900, contribution: 'Completada', zkpVerified: true, lastActive: '2026-03-14T12:10:00' },
  { name: 'BioAnalytics', records: 15200, contribution: 'Completada', zkpVerified: true, lastActive: '2026-03-14T12:30:00' },
  { name: 'ClinicalAI', records: 6700, contribution: 'Pendiente', zkpVerified: false, lastActive: '2026-03-14T09:15:00' },
  { name: 'PharmaML', records: 9800, contribution: 'Pendiente', zkpVerified: false, lastActive: '2026-03-13T22:00:00' },
]

const PHASE_STYLES = {
  collecting: { bg: COLORS.warningLight, color: COLORS.warning },
  aggregating: { bg: COLORS.primaryLight, color: COLORS.primary },
  completed: { bg: COLORS.successLight, color: COLORS.success },
}

export default function FederatedInference() {
  const [selectedRound, setSelectedRound] = useState(null)

  const phaseStyle = PHASE_STYLES[CURRENT_ROUND.phase]
  const privacyPct = Math.round((PRIVACY_BUDGET.epsilonUsed / PRIVACY_BUDGET.epsilonTotal) * 100)
  const privacyColor = privacyPct >= 80 ? COLORS.danger : privacyPct >= 50 ? COLORS.warning : COLORS.success
  const bestAccuracy = Math.max(...ROUNDS_HISTORY.map(r => r.accuracy))

  return (
    <div style={{ padding: 32, maxWidth: 1200, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, color: COLORS.text, margin: '0 0 8px' }}>
          Aprendizaje Federado
        </h1>
        <p style={{ fontSize: 16, color: COLORS.muted, margin: 0 }}>
          Estado de las rondas de entrenamiento federado y presupuesto de privacidad
        </p>
      </div>

      {/* Top row: Current round + Privacy budget */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 24, marginBottom: 28 }}>
        {/* Current round */}
        <div style={{
          background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 24,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
            <h2 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: 0 }}>
              Ronda actual
            </h2>
            <span style={{
              padding: '4px 12px', borderRadius: 6, fontSize: 12, fontWeight: 600,
              background: phaseStyle.bg, color: phaseStyle.color,
            }}>
              {CURRENT_ROUND.phaseLabel}
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 20 }}>
            <div style={{ background: COLORS.bg, borderRadius: 10, padding: 16, textAlign: 'center' }}>
              <p style={{ fontSize: 12, color: COLORS.muted, margin: '0 0 4px', fontWeight: 600 }}>Ronda</p>
              <p style={{ fontSize: 28, fontWeight: 700, color: COLORS.primary, margin: 0 }}>#{CURRENT_ROUND.number}</p>
            </div>
            <div style={{ background: COLORS.bg, borderRadius: 10, padding: 16, textAlign: 'center' }}>
              <p style={{ fontSize: 12, color: COLORS.muted, margin: '0 0 4px', fontWeight: 600 }}>Participantes</p>
              <p style={{ fontSize: 28, fontWeight: 700, color: COLORS.text, margin: 0 }}>
                {CURRENT_ROUND.participantsCurrent}/{CURRENT_ROUND.participantsTotal}
              </p>
            </div>
            <div style={{ background: COLORS.bg, borderRadius: 10, padding: 16, textAlign: 'center' }}>
              <p style={{ fontSize: 12, color: COLORS.muted, margin: '0 0 4px', fontWeight: 600 }}>Mejor precision</p>
              <p style={{ fontSize: 28, fontWeight: 700, color: COLORS.success, margin: 0 }}>{bestAccuracy}%</p>
            </div>
          </div>

          {/* Progress bar */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
              <span style={{ fontSize: 13, color: COLORS.muted }}>Progreso de la ronda</span>
              <span style={{ fontSize: 13, fontWeight: 600, color: COLORS.warning }}>{CURRENT_ROUND.progress}%</span>
            </div>
            <div style={{ width: '100%', height: 10, background: COLORS.border, borderRadius: 5, overflow: 'hidden' }}>
              <div style={{
                height: '100%', background: COLORS.warning, borderRadius: 5,
                width: `${CURRENT_ROUND.progress}%`, transition: 'width 0.5s',
              }} />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 6 }}>
              <span style={{ fontSize: 12, color: COLORS.muted }}>
                Inicio: {new Date(CURRENT_ROUND.startedAt).toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' })}
              </span>
              <span style={{ fontSize: 12, color: COLORS.muted }}>
                Est. fin: {new Date(CURRENT_ROUND.estimatedEnd).toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
          </div>
        </div>

        {/* Privacy budget */}
        <div style={{
          background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 24,
          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        }}>
          <h2 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: '0 0 20px' }}>
            Presupuesto de privacidad
          </h2>
          <div style={{
            width: 120, height: 120, borderRadius: '50%',
            background: `conic-gradient(${privacyColor} ${privacyPct * 3.6}deg, ${COLORS.border} 0deg)`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <div style={{
              width: 96, height: 96, borderRadius: '50%', background: COLORS.card,
              display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
            }}>
              <span style={{ fontSize: 22, fontWeight: 700, color: privacyColor }}>
                {PRIVACY_BUDGET.epsilonUsed}
              </span>
              <span style={{ fontSize: 12, color: COLORS.muted }}>de {PRIVACY_BUDGET.epsilonTotal}</span>
            </div>
          </div>
          <p style={{ fontSize: 13, color: COLORS.muted, margin: '12px 0 0', textAlign: 'center' }}>
            Epsilon consumido ({privacyPct}%)
          </p>
          <p style={{ fontSize: 12, color: privacyColor, fontWeight: 600, margin: '4px 0 0' }}>
            {PRIVACY_BUDGET.epsilonTotal - PRIVACY_BUDGET.epsilonUsed} epsilon restante
          </p>
        </div>
      </div>

      {/* Two-column: Rounds history + Participants */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: 24 }}>
        {/* Rounds history */}
        <div style={{
          background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 24,
        }}>
          <h2 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: '0 0 16px' }}>
            Historial de rondas
          </h2>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: `2px solid ${COLORS.border}` }}>
                {['Ronda', 'Participantes', 'Metodo', 'Precision', 'Epsilon', 'Estado'].map((h) => (
                  <th key={h} style={{
                    textAlign: 'left', padding: '10px 8px', fontSize: 12,
                    fontWeight: 600, color: COLORS.muted, textTransform: 'uppercase',
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {ROUNDS_HISTORY.map((round) => (
                <tr
                  key={round.round}
                  onClick={() => setSelectedRound(selectedRound === round.round ? null : round.round)}
                  style={{
                    borderBottom: `1px solid ${COLORS.border}`, cursor: 'pointer',
                    background: selectedRound === round.round ? COLORS.primaryLight : 'transparent',
                  }}
                >
                  <td style={{ padding: '10px 8px', fontSize: 14, fontWeight: 600, color: COLORS.primary }}>
                    #{round.round}
                  </td>
                  <td style={{ padding: '10px 8px', fontSize: 14, color: COLORS.text }}>{round.participants}/5</td>
                  <td style={{ padding: '10px 8px', fontSize: 13 }}>
                    <span style={{
                      padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 600,
                      background: COLORS.purpleLight, color: COLORS.purple,
                    }}>
                      {round.method}
                    </span>
                  </td>
                  <td style={{ padding: '10px 8px', fontSize: 14, fontWeight: 600, color: COLORS.success }}>
                    {round.accuracy}%
                  </td>
                  <td style={{ padding: '10px 8px', fontSize: 14, color: COLORS.muted }}>{round.epsilonUsed}</td>
                  <td style={{ padding: '10px 8px' }}>
                    <span style={{
                      padding: '3px 8px', borderRadius: 6, fontSize: 11, fontWeight: 600,
                      background: COLORS.successLight, color: COLORS.success,
                    }}>
                      Completada
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Participants */}
        <div style={{
          background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 24,
        }}>
          <h2 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: '0 0 16px' }}>
            Participantes (Ronda #{CURRENT_ROUND.number})
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
            {PARTICIPANTS.map((p, idx) => (
              <div key={idx} style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '12px 0', borderBottom: `1px solid ${COLORS.border}`,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <div style={{
                    width: 34, height: 34, borderRadius: '50%', background: COLORS.primaryLight,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 14, fontWeight: 600, color: COLORS.primary,
                  }}>
                    {p.name[0]}
                  </div>
                  <div>
                    <p style={{ fontSize: 14, fontWeight: 500, color: COLORS.text, margin: '0 0 2px' }}>{p.name}</p>
                    <p style={{ fontSize: 12, color: COLORS.muted, margin: 0 }}>
                      {p.records.toLocaleString()} registros
                    </p>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  {/* ZKP badge */}
                  <span style={{
                    padding: '2px 8px', borderRadius: 6, fontSize: 11, fontWeight: 600,
                    background: p.zkpVerified ? COLORS.successLight : COLORS.bg,
                    color: p.zkpVerified ? COLORS.success : COLORS.muted,
                  }}>
                    ZKP {p.zkpVerified ? '\u2713' : '-'}
                  </span>
                  {/* Contribution status */}
                  <span style={{
                    padding: '3px 8px', borderRadius: 6, fontSize: 11, fontWeight: 600,
                    background: p.contribution === 'Completada' ? COLORS.successLight : COLORS.warningLight,
                    color: p.contribution === 'Completada' ? COLORS.success : COLORS.warning,
                  }}>
                    {p.contribution}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
