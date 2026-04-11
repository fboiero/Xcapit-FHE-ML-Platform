import { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import {
  getConsortium,
  getConsortiumStats,
  listMembers,
  startTraining,
  getTrainingStatus,
  inviteToConsortium,
} from '../api/client'

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
  borderFocus: '#6366f1',
}

const STATUS_MAP = {
  active: { label: 'Activo', color: COLORS.success, bg: COLORS.successLight },
  training: { label: 'Entrenando', color: COLORS.warning, bg: COLORS.warningLight },
  completed: { label: 'Completado', color: COLORS.primary, bg: COLORS.primaryLight },
  pending: { label: 'Pendiente', color: COLORS.muted, bg: '#f3f4f6' },
}

const MODEL_LABELS = {
  linear_regression: 'Regresion lineal',
  logistic_regression: 'Regresion logistica',
  random_forest: 'Random Forest',
  neural_network: 'Red neuronal',
}

export default function ConsortiumDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [consortium, setConsortium] = useState(null)
  const [members, setMembers] = useState([])
  const [stats, setStats] = useState(null)
  const [trainingStatus, setTrainingStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showInvite, setShowInvite] = useState(false)
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteRole, setInviteRole] = useState('contributor')
  const [inviting, setInviting] = useState(false)
  const [inviteMsg, setInviteMsg] = useState('')
  const [trainingLoading, setTrainingLoading] = useState(false)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [cData, mData] = await Promise.allSettled([
          getConsortium(id),
          listMembers(id),
        ])
        if (cData.status === 'fulfilled') setConsortium(cData.value)
        if (mData.status === 'fulfilled') {
          const data = mData.value
          setMembers(Array.isArray(data) ? data : data.results || [])
        }

        try {
          const s = await getConsortiumStats(id)
          setStats(s)
        } catch (_) { /* stats may not exist yet */ }

        try {
          const ts = await getTrainingStatus(id)
          setTrainingStatus(ts)
        } catch (_) { /* no training yet */ }
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [id])

  const handleInvite = async (e) => {
    e.preventDefault()
    setInviting(true)
    setInviteMsg('')
    try {
      await inviteToConsortium(id, inviteEmail, inviteRole)
      setInviteMsg('Invitacion enviada correctamente.')
      setInviteEmail('')
      setShowInvite(false)
    } catch (err) {
      setInviteMsg(`Error: ${err.message}`)
    } finally {
      setInviting(false)
    }
  }

  const handleStartTraining = async () => {
    setTrainingLoading(true)
    try {
      const result = await startTraining(id)
      setTrainingStatus(result)
      setConsortium((prev) => prev ? { ...prev, status: 'training' } : prev)
    } catch (err) {
      setError(err.message)
    } finally {
      setTrainingLoading(false)
    }
  }

  if (loading) {
    return (
      <div style={{ padding: 32, textAlign: 'center' }}>
        <div style={{
          width: 40, height: 40, border: `3px solid ${COLORS.border}`, borderTopColor: COLORS.primary,
          borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '80px auto',
        }} />
        <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
        <p style={{ color: COLORS.muted }}>Cargando consorcio...</p>
      </div>
    )
  }

  if (!consortium) {
    return (
      <div style={{ padding: 32, textAlign: 'center' }}>
        <p style={{ color: COLORS.danger, fontSize: 16 }}>Consorcio no encontrado.</p>
        <Link to="/dashboard" style={{ color: COLORS.primary, textDecoration: 'none' }}>Volver al dashboard</Link>
      </div>
    )
  }

  const statusInfo = STATUS_MAP[consortium.status] || STATUS_MAP.pending
  const metrics = trainingStatus?.metrics || stats?.metrics || null

  return (
    <div style={{ padding: 32, maxWidth: 1100, margin: '0 auto' }}>
      {/* Breadcrumb */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 24 }}>
        <Link to="/dashboard" style={{ color: COLORS.muted, textDecoration: 'none', fontSize: 14 }}>Dashboard</Link>
        <span style={{ color: COLORS.muted, fontSize: 14 }}>/</span>
        <span style={{ color: COLORS.text, fontSize: 14, fontWeight: 500 }}>{consortium.name}</span>
      </div>

      {error && (
        <div style={{
          background: COLORS.dangerLight, border: '1px solid #fecaca', color: COLORS.danger,
          padding: '12px 16px', borderRadius: 10, marginBottom: 20, fontSize: 14,
        }}>
          {error}
        </div>
      )}

      {inviteMsg && (
        <div style={{
          background: inviteMsg.startsWith('Error') ? COLORS.dangerLight : COLORS.successLight,
          border: `1px solid ${inviteMsg.startsWith('Error') ? '#fecaca' : '#bbf7d0'}`,
          color: inviteMsg.startsWith('Error') ? COLORS.danger : COLORS.success,
          padding: '12px 16px', borderRadius: 10, marginBottom: 20, fontSize: 14,
        }}>
          {inviteMsg}
        </div>
      )}

      {/* Header */}
      <div style={{
        background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`,
        padding: 28, marginBottom: 24,
      }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
              <h1 style={{ fontSize: 26, fontWeight: 700, color: COLORS.text, margin: 0 }}>
                {consortium.name}
              </h1>
              <span style={{
                padding: '4px 12px', borderRadius: 6, fontSize: 13, fontWeight: 600,
                background: statusInfo.bg, color: statusInfo.color,
              }}>
                {statusInfo.label}
              </span>
            </div>
            {consortium.description && (
              <p style={{ fontSize: 15, color: COLORS.muted, margin: '0 0 12px', maxWidth: 600 }}>
                {consortium.description}
              </p>
            )}
            <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
              <div style={{ fontSize: 14 }}>
                <span style={{ color: COLORS.muted }}>Tipo de modelo: </span>
                <span style={{ fontWeight: 500, color: COLORS.text }}>
                  {MODEL_LABELS[consortium.model_type] || consortium.model_type || '-'}
                </span>
              </div>
              <div style={{ fontSize: 14 }}>
                <span style={{ color: COLORS.muted }}>Miembros: </span>
                <span style={{ fontWeight: 500, color: COLORS.text }}>{members.length}</span>
              </div>
              {consortium.created_at && (
                <div style={{ fontSize: 14 }}>
                  <span style={{ color: COLORS.muted }}>Creado: </span>
                  <span style={{ fontWeight: 500, color: COLORS.text }}>
                    {new Date(consortium.created_at).toLocaleDateString('es-AR')}
                  </span>
                </div>
              )}
            </div>
          </div>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <button
              onClick={() => setShowInvite(!showInvite)}
              style={{
                padding: '10px 18px', borderRadius: 8, border: `1px solid ${COLORS.border}`,
                background: COLORS.card, color: COLORS.text, fontSize: 14, fontWeight: 500, cursor: 'pointer',
              }}
            >
              Invitar miembro
            </button>
            <Link to={`/consortiums/${id}/upload`} style={{
              padding: '10px 18px', borderRadius: 8, border: `1px solid ${COLORS.border}`,
              background: COLORS.card, color: COLORS.text, fontSize: 14, fontWeight: 500,
              textDecoration: 'none', display: 'inline-flex', alignItems: 'center',
            }}>
              Subir datos
            </Link>
            {consortium.status === 'active' && (
              <button
                onClick={handleStartTraining}
                disabled={trainingLoading}
                style={{
                  padding: '10px 18px', borderRadius: 8, border: 'none',
                  background: trainingLoading ? '#a5b4fc' : COLORS.primary,
                  color: '#fff', fontSize: 14, fontWeight: 600,
                  cursor: trainingLoading ? 'not-allowed' : 'pointer',
                }}
              >
                {trainingLoading ? 'Iniciando...' : 'Iniciar entrenamiento'}
              </button>
            )}
          </div>
        </div>

        {/* Invite form */}
        {showInvite && (
          <form onSubmit={handleInvite} style={{
            marginTop: 20, padding: 20, background: COLORS.bg, borderRadius: 10,
            display: 'flex', gap: 12, alignItems: 'flex-end', flexWrap: 'wrap',
          }}>
            <div style={{ flex: '1 1 200px' }}>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: COLORS.muted, marginBottom: 4 }}>
                Email del miembro
              </label>
              <input
                type="email"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                placeholder="email@empresa.com"
                required
                style={{
                  width: '100%', padding: '10px 14px', borderRadius: 8, border: `1px solid ${COLORS.border}`,
                  fontSize: 14, outline: 'none', boxSizing: 'border-box',
                }}
              />
            </div>
            <div style={{ flex: '0 0 160px' }}>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: COLORS.muted, marginBottom: 4 }}>
                Rol
              </label>
              <select
                value={inviteRole}
                onChange={(e) => setInviteRole(e.target.value)}
                style={{
                  width: '100%', padding: '10px 14px', borderRadius: 8, border: `1px solid ${COLORS.border}`,
                  fontSize: 14, outline: 'none', background: '#fff', cursor: 'pointer',
                }}
              >
                <option value="contributor">Contribuidor</option>
                <option value="viewer">Observador</option>
                <option value="admin">Admin</option>
              </select>
            </div>
            <button
              type="submit"
              disabled={inviting}
              style={{
                padding: '10px 20px', borderRadius: 8, border: 'none', background: COLORS.primary,
                color: '#fff', fontSize: 14, fontWeight: 600, cursor: inviting ? 'not-allowed' : 'pointer',
              }}
            >
              {inviting ? 'Enviando...' : 'Enviar invitacion'}
            </button>
          </form>
        )}
      </div>

      {/* Content grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        {/* Members */}
        <div style={{
          background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 24,
        }}>
          <h2 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: '0 0 16px' }}>
            Miembros ({members.length})
          </h2>
          {members.length === 0 ? (
            <p style={{ color: COLORS.muted, fontSize: 14, textAlign: 'center', padding: '16px 0' }}>
              No hay miembros todavia.
            </p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
              {members.map((m, idx) => (
                <div key={m.id || idx} style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  padding: '12px 0', borderBottom: idx < members.length - 1 ? `1px solid ${COLORS.border}` : 'none',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div style={{
                      width: 34, height: 34, borderRadius: '50%', background: COLORS.primaryLight,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: 14, fontWeight: 600, color: COLORS.primary,
                    }}>
                      {(m.company_name || m.email || 'U')[0].toUpperCase()}
                    </div>
                    <div>
                      <div style={{ fontSize: 14, fontWeight: 500, color: COLORS.text }}>
                        {m.company_name || m.email || 'Miembro'}
                      </div>
                      {m.email && (
                        <div style={{ fontSize: 12, color: COLORS.muted }}>{m.email}</div>
                      )}
                    </div>
                  </div>
                  <span style={{
                    padding: '3px 10px', borderRadius: 6, fontSize: 12, fontWeight: 600,
                    background: m.role === 'owner' ? COLORS.primaryLight : m.role === 'admin' ? COLORS.warningLight : '#f3f4f6',
                    color: m.role === 'owner' ? COLORS.primary : m.role === 'admin' ? COLORS.warning : COLORS.muted,
                    textTransform: 'capitalize',
                  }}>
                    {m.role === 'owner' ? 'Propietario' : m.role === 'admin' ? 'Admin' : m.role === 'contributor' ? 'Contribuidor' : m.role || 'Miembro'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Training results / metrics */}
        <div style={{
          background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 24,
        }}>
          <h2 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: '0 0 16px' }}>
            Resultados del entrenamiento
          </h2>

          {trainingStatus?.status === 'training' && (
            <div style={{
              background: COLORS.warningLight, borderRadius: 10, padding: 16, marginBottom: 16, textAlign: 'center',
            }}>
              <div style={{
                width: '100%', height: 8, background: '#fde68a', borderRadius: 4, overflow: 'hidden', marginBottom: 8,
              }}>
                <div style={{
                  height: '100%', background: COLORS.warning, borderRadius: 4,
                  width: `${trainingStatus.progress || 50}%`, transition: 'width 0.5s',
                }} />
              </div>
              <p style={{ fontSize: 14, color: '#92400e', margin: 0, fontWeight: 500 }}>
                Entrenamiento en progreso... {trainingStatus.progress || 50}%
              </p>
            </div>
          )}

          {metrics ? (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              {metrics.r2 !== undefined && (
                <div style={{ background: COLORS.bg, borderRadius: 10, padding: 16, textAlign: 'center' }}>
                  <p style={{ fontSize: 12, color: COLORS.muted, margin: '0 0 4px', textTransform: 'uppercase', fontWeight: 600 }}>R2</p>
                  <p style={{ fontSize: 28, fontWeight: 700, color: COLORS.primary, margin: 0 }}>
                    {typeof metrics.r2 === 'number' ? metrics.r2.toFixed(4) : metrics.r2}
                  </p>
                </div>
              )}
              {metrics.mae !== undefined && (
                <div style={{ background: COLORS.bg, borderRadius: 10, padding: 16, textAlign: 'center' }}>
                  <p style={{ fontSize: 12, color: COLORS.muted, margin: '0 0 4px', textTransform: 'uppercase', fontWeight: 600 }}>MAE</p>
                  <p style={{ fontSize: 28, fontWeight: 700, color: COLORS.success, margin: 0 }}>
                    {typeof metrics.mae === 'number' ? metrics.mae.toFixed(4) : metrics.mae}
                  </p>
                </div>
              )}
              {metrics.rmse !== undefined && (
                <div style={{ background: COLORS.bg, borderRadius: 10, padding: 16, textAlign: 'center' }}>
                  <p style={{ fontSize: 12, color: COLORS.muted, margin: '0 0 4px', textTransform: 'uppercase', fontWeight: 600 }}>RMSE</p>
                  <p style={{ fontSize: 28, fontWeight: 700, color: COLORS.warning, margin: 0 }}>
                    {typeof metrics.rmse === 'number' ? metrics.rmse.toFixed(4) : metrics.rmse}
                  </p>
                </div>
              )}
              {metrics.accuracy !== undefined && (
                <div style={{ background: COLORS.bg, borderRadius: 10, padding: 16, textAlign: 'center' }}>
                  <p style={{ fontSize: 12, color: COLORS.muted, margin: '0 0 4px', textTransform: 'uppercase', fontWeight: 600 }}>Precision</p>
                  <p style={{ fontSize: 28, fontWeight: 700, color: '#8b5cf6', margin: 0 }}>
                    {typeof metrics.accuracy === 'number' ? (metrics.accuracy * 100).toFixed(2) + '%' : metrics.accuracy}
                  </p>
                </div>
              )}
            </div>
          ) : (
            <p style={{ color: COLORS.muted, fontSize: 14, textAlign: 'center', padding: '24px 0' }}>
              {consortium.status === 'active'
                ? 'Aun no se ha iniciado el entrenamiento. Sube datos y presiona "Iniciar entrenamiento".'
                : 'No hay resultados disponibles todavia.'}
            </p>
          )}

          {metrics && (
            <Link to={`/metrics/${id}`} style={{
              display: 'block', textAlign: 'center', marginTop: 16, color: COLORS.primary,
              textDecoration: 'none', fontSize: 14, fontWeight: 500,
            }}>
              Ver metricas detalladas
            </Link>
          )}
        </div>
      </div>

      {/* Contributions table */}
      <div style={{
        background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`,
        padding: 24, marginTop: 24,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
          <h2 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: 0 }}>
            Contribuciones de datos
          </h2>
          <Link to={`/consortiums/${id}/upload`} style={{
            padding: '8px 16px', borderRadius: 8, background: COLORS.primaryLight,
            color: COLORS.primary, textDecoration: 'none', fontSize: 14, fontWeight: 500,
          }}>
            Subir datos
          </Link>
        </div>

        {stats?.contributions && stats.contributions.length > 0 ? (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: `2px solid ${COLORS.border}` }}>
                {['Miembro', 'Registros', 'Tamano', 'Fecha', 'Estado'].map((h) => (
                  <th key={h} style={{
                    textAlign: 'left', padding: '10px 12px', fontSize: 13,
                    fontWeight: 600, color: COLORS.muted,
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {stats.contributions.map((c, idx) => (
                <tr key={idx} style={{ borderBottom: `1px solid ${COLORS.border}` }}>
                  <td style={{ padding: 12, fontSize: 14, color: COLORS.text }}>{c.company_name || 'Anonimo'}</td>
                  <td style={{ padding: 12, fontSize: 14, color: COLORS.muted }}>{c.records?.toLocaleString() || '-'}</td>
                  <td style={{ padding: 12, fontSize: 14, color: COLORS.muted }}>{c.size || '-'}</td>
                  <td style={{ padding: 12, fontSize: 14, color: COLORS.muted }}>
                    {c.uploaded_at ? new Date(c.uploaded_at).toLocaleDateString('es-AR') : '-'}
                  </td>
                  <td style={{ padding: 12 }}>
                    <span style={{
                      padding: '3px 10px', borderRadius: 6, fontSize: 12, fontWeight: 600,
                      background: COLORS.successLight, color: COLORS.success,
                    }}>
                      {c.status || 'Encriptado'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p style={{ color: COLORS.muted, fontSize: 14, textAlign: 'center', padding: '16px 0' }}>
            No hay contribuciones todavia. Los miembros deben subir sus datos encriptados.
          </p>
        )}
      </div>
    </div>
  )
}
