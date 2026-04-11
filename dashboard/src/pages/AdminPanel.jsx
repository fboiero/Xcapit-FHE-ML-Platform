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

const TIER_COLORS = {
  enterprise: { bg: '#fdf4ff', color: '#a855f7', label: 'Enterprise' },
  professional: { bg: '#eff6ff', color: '#3b82f6', label: 'Professional' },
  starter: { bg: '#f0fdf4', color: '#22c55e', label: 'Starter' },
  trial: { bg: COLORS.warningLight, color: COLORS.warning, label: 'Trial' },
}

const COMPANIES = [
  { id: 1, name: 'MedCorp S.A.', tier: 'enterprise', members: 45, consortiums: 3, trial: false, lastActive: '2026-03-14' },
  { id: 2, name: 'FinTech Solutions', tier: 'professional', members: 22, consortiums: 2, trial: false, lastActive: '2026-03-14' },
  { id: 3, name: 'SecureLab', tier: 'enterprise', members: 38, consortiums: 4, trial: false, lastActive: '2026-03-13' },
  { id: 4, name: 'DataInsights AR', tier: 'professional', members: 15, consortiums: 1, trial: false, lastActive: '2026-03-12' },
  { id: 5, name: 'CryptoHealth', tier: 'starter', members: 8, consortiums: 1, trial: false, lastActive: '2026-03-11' },
  { id: 6, name: 'BioAnalytics', tier: 'trial', members: 4, consortiums: 0, trial: true, lastActive: '2026-03-10' },
  { id: 7, name: 'NeuralMed', tier: 'trial', members: 3, consortiums: 0, trial: true, lastActive: '2026-03-09' },
  { id: 8, name: 'PrivacyFirst Tech', tier: 'starter', members: 10, consortiums: 1, trial: false, lastActive: '2026-03-08' },
]

const SYSTEM_HEALTH = [
  { name: 'API Gateway', status: 'green', latency: '12ms', uptime: '99.98%' },
  { name: 'Base de Datos', status: 'green', latency: '3ms', uptime: '99.99%' },
  { name: 'Redis Cache', status: 'green', latency: '1ms', uptime: '99.97%' },
  { name: 'FHE Engine', status: 'yellow', latency: '245ms', uptime: '99.85%' },
  { name: 'Blockchain Node', status: 'green', latency: '89ms', uptime: '99.92%' },
]

const STATUS_COLORS = {
  green: COLORS.success,
  yellow: COLORS.warning,
  red: COLORS.danger,
}

const ACTIVITY_LOG = [
  { id: 1, action: 'Aprobacion de trial', user: 'admin@xcapit.com', target: 'BioAnalytics', time: 'Hace 2 horas' },
  { id: 2, action: 'Cambio de tier', user: 'admin@xcapit.com', target: 'CryptoHealth (Trial -> Starter)', time: 'Hace 4 horas' },
  { id: 3, action: 'Reseteo de password', user: 'admin@xcapit.com', target: 'usuario@datainsights.com', time: 'Hace 6 horas' },
  { id: 4, action: 'Creacion de consorcio', user: 'admin@xcapit.com', target: 'Consorcio Seguros Unidos', time: 'Hace 1 dia' },
  { id: 5, action: 'Suspension de cuenta', user: 'admin@xcapit.com', target: 'cuenta_spam_01', time: 'Hace 1 dia' },
  { id: 6, action: 'Actualizacion FHE Engine', user: 'devops@xcapit.com', target: 'v2.4.1 -> v2.5.0', time: 'Hace 2 dias' },
  { id: 7, action: 'Backup de base de datos', user: 'devops@xcapit.com', target: 'snapshot_20260312', time: 'Hace 2 dias' },
  { id: 8, action: 'Aprobacion de trial', user: 'admin@xcapit.com', target: 'NeuralMed', time: 'Hace 3 dias' },
  { id: 9, action: 'Configuracion de seguridad', user: 'admin@xcapit.com', target: 'CKKS 256-bit habilitado', time: 'Hace 4 dias' },
  { id: 10, action: 'Cambio de tier', user: 'admin@xcapit.com', target: 'FinTech Solutions (Starter -> Professional)', time: 'Hace 5 dias' },
]

export default function AdminPanel() {
  const [isAdmin] = useState(true)
  const [actionModal, setActionModal] = useState(null)

  if (!isAdmin) {
    return (
      <div style={{ padding: 32, maxWidth: 1200, margin: '0 auto', textAlign: 'center', paddingTop: 120 }}>
        <p style={{ fontSize: 18, color: COLORS.danger, fontWeight: 600 }}>Acceso denegado</p>
        <p style={{ fontSize: 14, color: COLORS.muted }}>Solo administradores pueden acceder a este panel.</p>
      </div>
    )
  }

  const totalEmpresas = COMPANIES.length
  const totalUsuarios = COMPANIES.reduce((s, c) => s + c.members, 0)
  const totalConsorcios = new Set(COMPANIES.flatMap(c => Array(c.consortiums).fill(0))).size || COMPANIES.reduce((s, c) => s + c.consortiums, 0)
  const storageUsed = '847 GB'

  return (
    <div style={{ padding: 32, maxWidth: 1200, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 32, flexWrap: 'wrap', gap: 16 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 700, color: COLORS.text, margin: '0 0 8px' }}>
            Panel de Administracion
          </h1>
          <p style={{ fontSize: 16, color: COLORS.muted, margin: 0 }}>
            Gestion de empresas, usuarios y salud del sistema
          </p>
        </div>
        <span style={{
          padding: '6px 14px', borderRadius: 6, fontSize: 12, fontWeight: 600,
          background: COLORS.dangerLight, color: COLORS.danger,
        }}>
          Solo administradores
        </span>
      </div>

      {/* Stats row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16, marginBottom: 28 }}>
        {[
          { label: 'Total empresas', value: totalEmpresas, color: COLORS.primary },
          { label: 'Usuarios activos', value: totalUsuarios, color: COLORS.accent },
          { label: 'Consorcios', value: 11, color: COLORS.success },
          { label: 'Storage usado', value: storageUsed, color: COLORS.warning },
        ].map(s => (
          <div key={s.label} style={{
            background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 20,
          }}>
            <p style={{ fontSize: 13, color: COLORS.muted, margin: '0 0 4px' }}>{s.label}</p>
            <p style={{ fontSize: 28, fontWeight: 700, color: s.color, margin: 0 }}>{s.value}</p>
          </div>
        ))}
      </div>

      {/* Companies table */}
      <div style={{
        background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`,
        padding: 24, marginBottom: 24,
      }}>
        <h3 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: '0 0 20px' }}>
          Empresas Registradas
        </h3>

        {/* Table header */}
        <div style={{
          display: 'grid', gridTemplateColumns: '2fr 100px 80px 100px 80px 100px',
          gap: 12, padding: '10px 16px', background: COLORS.bg, borderRadius: 8,
          fontSize: 12, fontWeight: 600, color: COLORS.muted, textTransform: 'uppercase',
          marginBottom: 4,
        }}>
          <span>Empresa</span>
          <span>Tier</span>
          <span>Miembros</span>
          <span>Consorcios</span>
          <span>Trial</span>
          <span>Ultima act.</span>
        </div>

        {COMPANIES.map(company => {
          const tierStyle = TIER_COLORS[company.tier]
          return (
            <div key={company.id} style={{
              display: 'grid', gridTemplateColumns: '2fr 100px 80px 100px 80px 100px',
              gap: 12, padding: '14px 16px', alignItems: 'center',
              borderBottom: `1px solid ${COLORS.border}`,
            }}>
              <span style={{ fontSize: 14, fontWeight: 500, color: COLORS.text }}>{company.name}</span>
              <span style={{
                padding: '3px 10px', borderRadius: 6, fontSize: 12, fontWeight: 600,
                background: tierStyle.bg, color: tierStyle.color,
                display: 'inline-block', width: 'fit-content',
              }}>
                {tierStyle.label}
              </span>
              <span style={{ fontSize: 14, color: COLORS.muted }}>{company.members}</span>
              <span style={{ fontSize: 14, color: COLORS.muted }}>{company.consortiums}</span>
              <span style={{
                fontSize: 12, fontWeight: 600,
                color: company.trial ? COLORS.warning : COLORS.success,
              }}>
                {company.trial ? 'Si' : 'No'}
              </span>
              <span style={{ fontSize: 13, color: COLORS.muted }}>{company.lastActive}</span>
            </div>
          )
        })}
      </div>

      {/* System health + Activity log */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: 20 }}>
        {/* System health */}
        <div style={{
          background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 24,
        }}>
          <h3 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: '0 0 20px' }}>
            Salud del Sistema
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {SYSTEM_HEALTH.map(service => (
              <div key={service.name} style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '12px 16px', background: COLORS.bg, borderRadius: 8,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <div style={{
                    width: 10, height: 10, borderRadius: '50%',
                    background: STATUS_COLORS[service.status],
                  }} />
                  <span style={{ fontSize: 14, fontWeight: 500, color: COLORS.text }}>{service.name}</span>
                </div>
                <div style={{ display: 'flex', gap: 16 }}>
                  <span style={{ fontSize: 12, color: COLORS.muted }}>Latencia: {service.latency}</span>
                  <span style={{ fontSize: 12, color: COLORS.muted }}>Uptime: {service.uptime}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Activity log */}
        <div style={{
          background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 24,
        }}>
          <h3 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: '0 0 20px' }}>
            Actividad Reciente
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
            {ACTIVITY_LOG.map((entry, idx) => (
              <div key={entry.id} style={{
                padding: '10px 0',
                borderBottom: idx < ACTIVITY_LOG.length - 1 ? `1px solid ${COLORS.border}` : 'none',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span style={{ fontSize: 14, fontWeight: 500, color: COLORS.text }}>{entry.action}</span>
                  <span style={{ fontSize: 12, color: COLORS.muted, flexShrink: 0 }}>{entry.time}</span>
                </div>
                <div style={{ display: 'flex', gap: 8, fontSize: 12, color: COLORS.muted }}>
                  <span>{entry.user}</span>
                  <span>-</span>
                  <span>{entry.target}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Quick actions */}
      <div style={{
        background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`,
        padding: 24, marginTop: 20,
      }}>
        <h3 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: '0 0 20px' }}>
          Acciones Rapidas
        </h3>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          {[
            { label: 'Aprobar Trial', action: 'approve_trial', bg: COLORS.success, desc: 'Aprobar una cuenta de prueba pendiente' },
            { label: 'Cambiar Tier', action: 'change_tier', bg: COLORS.primary, desc: 'Modificar el nivel de suscripcion de una empresa' },
            { label: 'Resetear Password', action: 'reset_password', bg: COLORS.warning, desc: 'Enviar enlace de reseteo a un usuario' },
          ].map(btn => (
            <div key={btn.action} style={{ flex: 1, minWidth: 200 }}>
              <button
                onClick={() => setActionModal(actionModal === btn.action ? null : btn.action)}
                style={{
                  width: '100%', padding: '14px 20px', borderRadius: 8, border: 'none',
                  background: actionModal === btn.action ? btn.bg : COLORS.bg,
                  color: actionModal === btn.action ? '#fff' : COLORS.text,
                  fontSize: 14, fontWeight: 600, cursor: 'pointer',
                  transition: 'background 0.2s, color 0.2s',
                }}
              >
                {btn.label}
              </button>
              {actionModal === btn.action && (
                <div style={{
                  marginTop: 8, padding: 16, background: COLORS.bg, borderRadius: 8,
                  border: `1px solid ${COLORS.border}`,
                }}>
                  <p style={{ fontSize: 13, color: COLORS.muted, margin: '0 0 12px' }}>{btn.desc}</p>
                  <input
                    placeholder={btn.action === 'reset_password' ? 'Email del usuario' : 'Nombre de la empresa'}
                    style={{
                      width: '100%', padding: '10px 12px', borderRadius: 8,
                      border: `1px solid ${COLORS.border}`, fontSize: 14, color: COLORS.text,
                      outline: 'none', boxSizing: 'border-box', marginBottom: 8,
                    }}
                  />
                  <button style={{
                    padding: '8px 16px', borderRadius: 6, border: 'none',
                    background: btn.bg, color: '#fff', fontSize: 13,
                    fontWeight: 600, cursor: 'pointer',
                  }}>
                    Confirmar
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
