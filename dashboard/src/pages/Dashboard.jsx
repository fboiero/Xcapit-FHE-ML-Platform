import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { listConsortiums, getCurrentCompany } from '../api/client'
import { getTrialStatus, getTrialUsage } from '../api/trial'

const COLORS = {
  primary: '#6366f1',
  primaryHover: '#4f46e5',
  primaryLight: '#eef2ff',
  success: '#10b981',
  successLight: '#dcfce7',
  warning: '#f59e0b',
  warningLight: '#fef9c3',
  danger: '#ef4444',
  dangerLight: '#fef2f2',
  bg: '#f9fafb',
  card: '#ffffff',
  text: '#111827',
  muted: '#6b7280',
  border: '#e5e7eb',
}

const STAT_CARDS = [
  {
    key: 'consortiums',
    label: 'Consorcios activos',
    icon: (
      <svg width="24" height="24" fill="none" stroke={COLORS.primary} viewBox="0 0 24 24" strokeWidth={1.8}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M18 18.72a9.094 9.094 0 003.741-.479 3 3 0 00-4.682-2.72m.94 3.198l.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0112 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 016 18.719m12 0a5.971 5.971 0 00-.941-3.197m0 0A5.995 5.995 0 0012 12.75a5.995 5.995 0 00-5.058 2.772" />
      </svg>
    ),
    color: COLORS.primary,
    bg: COLORS.primaryLight,
  },
  {
    key: 'models',
    label: 'Modelos entrenados',
    icon: (
      <svg width="24" height="24" fill="none" stroke={COLORS.success} viewBox="0 0 24 24" strokeWidth={1.8}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5" />
      </svg>
    ),
    color: COLORS.success,
    bg: COLORS.successLight,
  },
  {
    key: 'uploads',
    label: 'Datos subidos',
    icon: (
      <svg width="24" height="24" fill="none" stroke={COLORS.warning} viewBox="0 0 24 24" strokeWidth={1.8}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
      </svg>
    ),
    color: COLORS.warning,
    bg: COLORS.warningLight,
  },
  {
    key: 'training_runs',
    label: 'Training runs',
    icon: (
      <svg width="24" height="24" fill="none" stroke="#8b5cf6" viewBox="0 0 24 24" strokeWidth={1.8}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.348a1.125 1.125 0 010 1.971l-11.54 6.347a1.125 1.125 0 01-1.667-.985V5.653z" />
      </svg>
    ),
    color: '#8b5cf6',
    bg: '#f5f3ff',
  },
]

const QUICK_ACTIONS = [
  { label: 'Crear consorcio', path: '/consortiums/new', icon: '+' },
  { label: 'Subir datos', path: '/data-upload', icon: '\u2191' },
  { label: 'Iniciar entrenamiento', path: '/training', icon: '\u25B6' },
  { label: 'Ver metricas', path: '/metrics', icon: '\u2630' },
]

export default function Dashboard() {
  const [company, setCompany] = useState(null)
  const [consortiums, setConsortiums] = useState([])
  const [trialStatus, setTrialStatus] = useState(null)
  const [usage, setUsage] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [companyData, consortiumData] = await Promise.allSettled([
          getCurrentCompany(),
          listConsortiums(),
        ])
        if (companyData.status === 'fulfilled') setCompany(companyData.value)
        if (consortiumData.status === 'fulfilled') {
          const data = consortiumData.value
          setConsortiums(Array.isArray(data) ? data : data.results || [])
        }

        try {
          const ts = await getTrialStatus()
          setTrialStatus(ts)
        } catch (_) { /* non-critical */ }

        try {
          const u = await getTrialUsage()
          setUsage(u)
        } catch (_) { /* non-critical */ }
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  const stats = {
    consortiums: consortiums.filter(c => c.status === 'active' || c.status === 'training').length || consortiums.length,
    models: usage?.training_runs_used || 0,
    uploads: usage?.uploads_used || 0,
    training_runs: usage?.training_runs_used || 0,
  }

  const recentActivity = consortiums.slice(0, 5).map((c, idx) => ({
    id: idx,
    text: `Consorcio "${c.name}" - ${c.status === 'active' ? 'Activo' : c.status === 'training' ? 'Entrenando' : c.status === 'completed' ? 'Completado' : 'Pendiente'}`,
    time: c.created_at ? new Date(c.created_at).toLocaleDateString('es-AR') : 'Reciente',
    type: c.status,
  }))

  if (loading) {
    return (
      <div style={{ padding: 32, textAlign: 'center' }}>
        <div style={{
          width: 40, height: 40, border: `3px solid ${COLORS.border}`, borderTopColor: COLORS.primary,
          borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '80px auto',
        }} />
        <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
        <p style={{ color: COLORS.muted }}>Cargando dashboard...</p>
      </div>
    )
  }

  return (
    <div style={{ padding: 32, maxWidth: 1200, margin: '0 auto' }}>
      {/* Trial banner */}
      {trialStatus?.is_trial && !trialStatus?.trial_expired && (
        <div style={{
          background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
          borderRadius: 12, padding: '16px 24px', marginBottom: 24,
          display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <svg width="20" height="20" fill="none" stroke="#fff" viewBox="0 0 24 24" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6l4 2m6-2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span style={{ color: '#fff', fontWeight: 600, fontSize: 15 }}>
              Periodo de prueba: {trialStatus.trial_days_remaining || 0} dias restantes
            </span>
          </div>
          <Link to="/trial" style={{
            padding: '8px 20px', borderRadius: 8, background: '#fff', color: COLORS.primary,
            fontWeight: 600, fontSize: 14, textDecoration: 'none',
          }}>
            Ver detalles
          </Link>
        </div>
      )}

      {/* Welcome */}
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, color: COLORS.text, margin: '0 0 8px' }}>
          Bienvenido{company?.name ? `, ${company.name}` : ''}
        </h1>
        <p style={{ fontSize: 16, color: COLORS.muted, margin: 0 }}>
          Resumen de tu plataforma de ML con privacidad
        </p>
      </div>

      {error && (
        <div style={{
          background: COLORS.dangerLight, border: '1px solid #fecaca', color: COLORS.danger,
          padding: '12px 16px', borderRadius: 10, marginBottom: 20, fontSize: 14,
        }}>
          {error}
        </div>
      )}

      {/* Stats cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 20, marginBottom: 32 }}>
        {STAT_CARDS.map((card) => (
          <div key={card.key} style={{
            background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`,
            padding: 24, display: 'flex', alignItems: 'flex-start', gap: 16,
          }}>
            <div style={{
              width: 48, height: 48, borderRadius: 12, background: card.bg,
              display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
            }}>
              {card.icon}
            </div>
            <div>
              <p style={{ fontSize: 13, color: COLORS.muted, margin: '0 0 4px' }}>{card.label}</p>
              <p style={{ fontSize: 28, fontWeight: 700, color: COLORS.text, margin: 0 }}>
                {stats[card.key]}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Two column layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        {/* Recent activity */}
        <div style={{
          background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 24,
        }}>
          <h2 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: '0 0 16px' }}>
            Actividad reciente
          </h2>
          {recentActivity.length === 0 ? (
            <p style={{ color: COLORS.muted, fontSize: 14, textAlign: 'center', padding: '24px 0' }}>
              No hay actividad reciente. Crea tu primer consorcio para comenzar.
            </p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
              {recentActivity.map((act) => (
                <div key={act.id} style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  padding: '12px 0', borderBottom: `1px solid ${COLORS.border}`,
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div style={{
                      width: 8, height: 8, borderRadius: '50%',
                      background: act.type === 'active' ? COLORS.success
                        : act.type === 'training' ? COLORS.warning
                        : act.type === 'completed' ? COLORS.primary
                        : COLORS.muted,
                    }} />
                    <span style={{ fontSize: 14, color: COLORS.text }}>{act.text}</span>
                  </div>
                  <span style={{ fontSize: 12, color: COLORS.muted, whiteSpace: 'nowrap', marginLeft: 12 }}>
                    {act.time}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Quick actions */}
        <div style={{
          background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 24,
        }}>
          <h2 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: '0 0 16px' }}>
            Acciones rapidas
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            {QUICK_ACTIONS.map((action) => (
              <Link
                key={action.path}
                to={action.path}
                style={{
                  display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8,
                  padding: '20px 16px', borderRadius: 10, border: `1px solid ${COLORS.border}`,
                  textDecoration: 'none', transition: 'border-color 0.2s, background 0.2s',
                  background: COLORS.card,
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.borderColor = COLORS.primary
                  e.currentTarget.style.background = COLORS.primaryLight
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.borderColor = COLORS.border
                  e.currentTarget.style.background = COLORS.card
                }}
              >
                <span style={{
                  width: 40, height: 40, borderRadius: 10, background: COLORS.primaryLight,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 20, color: COLORS.primary, fontWeight: 700,
                }}>
                  {action.icon}
                </span>
                <span style={{ fontSize: 14, fontWeight: 500, color: COLORS.text, textAlign: 'center' }}>
                  {action.label}
                </span>
              </Link>
            ))}
          </div>
        </div>
      </div>

      {/* Consortiums list */}
      <div style={{
        background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`,
        padding: 24, marginTop: 24,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
          <h2 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: 0 }}>
            Mis consorcios
          </h2>
          <Link to="/consortiums/new" style={{
            padding: '8px 16px', borderRadius: 8, background: COLORS.primary, color: '#fff',
            textDecoration: 'none', fontSize: 14, fontWeight: 500,
          }}>
            Nuevo consorcio
          </Link>
        </div>

        {consortiums.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '32px 0' }}>
            <p style={{ color: COLORS.muted, fontSize: 15, marginBottom: 16 }}>
              Aun no tienes consorcios. Crea uno para empezar a colaborar.
            </p>
            <Link to="/consortiums/new" style={{
              display: 'inline-flex', alignItems: 'center', gap: 8,
              padding: '10px 24px', borderRadius: 8, background: COLORS.primaryLight,
              color: COLORS.primary, textDecoration: 'none', fontWeight: 500, fontSize: 14,
            }}>
              Crear primer consorcio
            </Link>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: `2px solid ${COLORS.border}` }}>
                  {['Nombre', 'Tipo de modelo', 'Estado', 'Miembros', 'Acciones'].map((h) => (
                    <th key={h} style={{
                      textAlign: 'left', padding: '10px 12px', fontSize: 13,
                      fontWeight: 600, color: COLORS.muted, textTransform: 'uppercase', letterSpacing: 0.5,
                    }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {consortiums.map((c) => (
                  <tr key={c.id || c.name} style={{ borderBottom: `1px solid ${COLORS.border}` }}>
                    <td style={{ padding: '12px', fontSize: 14, fontWeight: 500, color: COLORS.text }}>
                      {c.name}
                    </td>
                    <td style={{ padding: '12px', fontSize: 14, color: COLORS.muted }}>
                      {c.model_type || '-'}
                    </td>
                    <td style={{ padding: '12px' }}>
                      <span style={{
                        display: 'inline-block', padding: '4px 10px', borderRadius: 6, fontSize: 12, fontWeight: 600,
                        background: c.status === 'active' ? COLORS.successLight
                          : c.status === 'training' ? COLORS.warningLight
                          : c.status === 'completed' ? COLORS.primaryLight
                          : '#f3f4f6',
                        color: c.status === 'active' ? COLORS.success
                          : c.status === 'training' ? COLORS.warning
                          : c.status === 'completed' ? COLORS.primary
                          : COLORS.muted,
                      }}>
                        {c.status === 'active' ? 'Activo' : c.status === 'training' ? 'Entrenando'
                          : c.status === 'completed' ? 'Completado' : c.status || 'Pendiente'}
                      </span>
                    </td>
                    <td style={{ padding: '12px', fontSize: 14, color: COLORS.muted }}>
                      {c.member_count || c.members_count || '-'}
                    </td>
                    <td style={{ padding: '12px' }}>
                      <Link to={`/consortiums/${c.id}`} style={{
                        color: COLORS.primary, textDecoration: 'none', fontSize: 14, fontWeight: 500,
                      }}>
                        Ver detalle
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
