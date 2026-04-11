import { useState, useEffect } from 'react'
import { Link, useParams } from 'react-router-dom'
import { listConsortiums, startTraining, getTrainingStatus } from '../api/client'

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

const STATUS_STYLES = {
  completed: { label: 'Completado', color: COLORS.success, bg: COLORS.successLight },
  training: { label: 'Entrenando', color: COLORS.warning, bg: COLORS.warningLight },
  queued: { label: 'En cola', color: COLORS.primary, bg: COLORS.primaryLight },
  failed: { label: 'Fallido', color: COLORS.danger, bg: COLORS.dangerLight },
  pending: { label: 'Pendiente', color: COLORS.muted, bg: '#f3f4f6' },
}

const MODEL_LABELS = {
  linear_regression: 'Regresion lineal',
  logistic_regression: 'Regresion logistica',
  random_forest: 'Random Forest',
  neural_network: 'Red neuronal',
}

export default function TrainingDashboard() {
  const { consortiumId } = useParams()
  const [consortiums, setConsortiums] = useState([])
  const [trainingRuns, setTrainingRuns] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [startingId, setStartingId] = useState(null)
  const [selectedRun, setSelectedRun] = useState(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await listConsortiums()
        const list = Array.isArray(data) ? data : data.results || []
        setConsortiums(list)

        // Fetch training status for each consortium
        const runs = []
        const targets = consortiumId ? list.filter(c => c.id === consortiumId) : list.slice(0, 20)
        for (const c of targets) {
          try {
            const ts = await getTrainingStatus(c.id)
            runs.push({
              consortium_id: c.id,
              consortium_name: c.name,
              model_type: c.model_type,
              status: ts.status || c.status,
              progress: ts.progress || 0,
              started_at: ts.started_at || ts.created_at,
              completed_at: ts.completed_at,
              metrics: ts.metrics || null,
              duration: ts.duration || null,
              epochs: ts.epochs || null,
            })
          } catch (_) {
            runs.push({
              consortium_id: c.id,
              consortium_name: c.name,
              model_type: c.model_type,
              status: c.status === 'completed' ? 'completed' : 'pending',
              progress: c.status === 'completed' ? 100 : 0,
              started_at: null,
              completed_at: null,
              metrics: null,
            })
          }
        }
        setTrainingRuns(runs)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [consortiumId])

  const handleStartTraining = async (cId) => {
    setStartingId(cId)
    setError('')
    try {
      const result = await startTraining(cId)
      setTrainingRuns((prev) =>
        prev.map((r) =>
          r.consortium_id === cId
            ? { ...r, status: 'training', progress: 0, started_at: new Date().toISOString(), metrics: null }
            : r
        )
      )
    } catch (err) {
      setError(`Error iniciando entrenamiento: ${err.message}`)
    } finally {
      setStartingId(null)
    }
  }

  const activeRuns = trainingRuns.filter(r => r.status === 'training' || r.status === 'queued')
  const completedRuns = trainingRuns.filter(r => r.status === 'completed')
  const pendingRuns = trainingRuns.filter(r => r.status === 'pending' || r.status === 'failed')

  if (loading) {
    return (
      <div style={{ padding: 32, textAlign: 'center' }}>
        <div style={{
          width: 40, height: 40, border: `3px solid ${COLORS.border}`, borderTopColor: COLORS.primary,
          borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '80px auto',
        }} />
        <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
        <p style={{ color: COLORS.muted }}>Cargando entrenamientos...</p>
      </div>
    )
  }

  return (
    <div style={{ padding: 32, maxWidth: 1100, margin: '0 auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 700, color: COLORS.text, margin: '0 0 8px' }}>
            Entrenamiento
          </h1>
          <p style={{ fontSize: 16, color: COLORS.muted, margin: 0 }}>
            Gestiona y monitorea tus entrenamientos de ML federado
          </p>
        </div>
      </div>

      {error && (
        <div style={{
          background: COLORS.dangerLight, border: '1px solid #fecaca', color: COLORS.danger,
          padding: '12px 16px', borderRadius: 10, marginBottom: 20, fontSize: 14,
        }}>
          {error}
        </div>
      )}

      {/* Summary */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16, marginBottom: 24 }}>
        <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 20 }}>
          <p style={{ fontSize: 13, color: COLORS.muted, margin: '0 0 4px' }}>En progreso</p>
          <p style={{ fontSize: 28, fontWeight: 700, color: COLORS.warning, margin: 0 }}>{activeRuns.length}</p>
        </div>
        <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 20 }}>
          <p style={{ fontSize: 13, color: COLORS.muted, margin: '0 0 4px' }}>Completados</p>
          <p style={{ fontSize: 28, fontWeight: 700, color: COLORS.success, margin: 0 }}>{completedRuns.length}</p>
        </div>
        <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 20 }}>
          <p style={{ fontSize: 13, color: COLORS.muted, margin: '0 0 4px' }}>Pendientes</p>
          <p style={{ fontSize: 28, fontWeight: 700, color: COLORS.muted, margin: 0 }}>{pendingRuns.length}</p>
        </div>
        <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 20 }}>
          <p style={{ fontSize: 13, color: COLORS.muted, margin: '0 0 4px' }}>Total</p>
          <p style={{ fontSize: 28, fontWeight: 700, color: COLORS.text, margin: 0 }}>{trainingRuns.length}</p>
        </div>
      </div>

      {/* Active training runs */}
      {activeRuns.length > 0 && (
        <div style={{
          background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`,
          padding: 24, marginBottom: 24,
        }}>
          <h2 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: '0 0 16px' }}>
            Entrenamientos activos
          </h2>
          {activeRuns.map((run) => (
            <div key={run.consortium_id} style={{
              border: `1px solid ${COLORS.border}`, borderRadius: 10, padding: 16, marginBottom: 12,
              background: COLORS.warningLight + '33',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
                <div>
                  <span style={{ fontSize: 15, fontWeight: 600, color: COLORS.text }}>{run.consortium_name}</span>
                  <span style={{ fontSize: 13, color: COLORS.muted, marginLeft: 12 }}>
                    {MODEL_LABELS[run.model_type] || run.model_type}
                  </span>
                </div>
                <span style={{
                  padding: '4px 10px', borderRadius: 6, fontSize: 12, fontWeight: 600,
                  background: COLORS.warningLight, color: COLORS.warning,
                }}>
                  Entrenando
                </span>
              </div>
              <div style={{
                width: '100%', height: 8, background: '#fde68a', borderRadius: 4, overflow: 'hidden',
              }}>
                <div style={{
                  height: '100%', background: COLORS.warning, borderRadius: 4,
                  width: `${run.progress || 45}%`, transition: 'width 0.5s',
                }} />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 6 }}>
                <span style={{ fontSize: 13, color: COLORS.muted }}>
                  {run.started_at ? `Iniciado: ${new Date(run.started_at).toLocaleString('es-AR')}` : ''}
                </span>
                <span style={{ fontSize: 13, fontWeight: 600, color: COLORS.warning }}>
                  {run.progress || 45}%
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* All training runs table */}
      <div style={{
        background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, overflow: 'hidden',
      }}>
        <div style={{ padding: '20px 24px', borderBottom: `1px solid ${COLORS.border}` }}>
          <h2 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: 0 }}>
            Todos los entrenamientos
          </h2>
        </div>

        {trainingRuns.length === 0 ? (
          <div style={{ padding: 48, textAlign: 'center' }}>
            <p style={{ color: COLORS.muted, fontSize: 16, marginBottom: 16 }}>
              No hay entrenamientos todavia. Crea un consorcio y sube datos para comenzar.
            </p>
            <Link to="/consortiums/new" style={{
              padding: '10px 20px', borderRadius: 8, background: COLORS.primary, color: '#fff',
              textDecoration: 'none', fontSize: 14, fontWeight: 600,
            }}>
              Crear consorcio
            </Link>
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: '#f8fafc', borderBottom: `2px solid ${COLORS.border}` }}>
                {['Consorcio', 'Modelo', 'Estado', 'Progreso', 'Metricas', 'Acciones'].map((h) => (
                  <th key={h} style={{
                    textAlign: 'left', padding: '12px 16px', fontSize: 13,
                    fontWeight: 600, color: COLORS.muted, textTransform: 'uppercase',
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {trainingRuns.map((run) => {
                const statusStyle = STATUS_STYLES[run.status] || STATUS_STYLES.pending
                return (
                  <tr key={run.consortium_id} style={{
                    borderBottom: `1px solid ${COLORS.border}`,
                    background: selectedRun === run.consortium_id ? COLORS.primaryLight : 'transparent',
                    cursor: 'pointer',
                  }}
                    onClick={() => setSelectedRun(selectedRun === run.consortium_id ? null : run.consortium_id)}
                  >
                    <td style={{ padding: '12px 16px', fontSize: 14, fontWeight: 500, color: COLORS.text }}>
                      {run.consortium_name}
                    </td>
                    <td style={{ padding: '12px 16px', fontSize: 14, color: COLORS.muted }}>
                      {MODEL_LABELS[run.model_type] || run.model_type || '-'}
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      <span style={{
                        display: 'inline-block', padding: '4px 10px', borderRadius: 6, fontSize: 12, fontWeight: 600,
                        background: statusStyle.bg, color: statusStyle.color,
                      }}>
                        {statusStyle.label}
                      </span>
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <div style={{
                          flex: 1, height: 6, background: COLORS.border, borderRadius: 3, overflow: 'hidden', maxWidth: 100,
                        }}>
                          <div style={{
                            height: '100%', borderRadius: 3,
                            background: run.status === 'completed' ? COLORS.success : run.status === 'training' ? COLORS.warning : COLORS.muted,
                            width: `${run.progress || (run.status === 'completed' ? 100 : 0)}%`,
                          }} />
                        </div>
                        <span style={{ fontSize: 13, color: COLORS.muted }}>
                          {run.progress || (run.status === 'completed' ? 100 : 0)}%
                        </span>
                      </div>
                    </td>
                    <td style={{ padding: '12px 16px', fontSize: 14, color: COLORS.muted }}>
                      {run.metrics ? (
                        <span>
                          R2: {typeof run.metrics.r2 === 'number' ? run.metrics.r2.toFixed(3) : '-'}
                        </span>
                      ) : '-'}
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      {(run.status === 'pending' || run.status === 'failed') && (
                        <button
                          onClick={(e) => { e.stopPropagation(); handleStartTraining(run.consortium_id) }}
                          disabled={startingId === run.consortium_id}
                          style={{
                            padding: '6px 14px', borderRadius: 6, border: 'none',
                            background: startingId === run.consortium_id ? '#a5b4fc' : COLORS.primary,
                            color: '#fff', fontSize: 13, fontWeight: 600,
                            cursor: startingId === run.consortium_id ? 'not-allowed' : 'pointer',
                          }}
                        >
                          {startingId === run.consortium_id ? 'Iniciando...' : 'Iniciar'}
                        </button>
                      )}
                      {run.status === 'completed' && (
                        <Link
                          to={`/metrics/${run.consortium_id}`}
                          onClick={(e) => e.stopPropagation()}
                          style={{
                            padding: '6px 14px', borderRadius: 6, background: COLORS.primaryLight,
                            color: COLORS.primary, textDecoration: 'none', fontSize: 13, fontWeight: 600,
                          }}
                        >
                          Ver metricas
                        </Link>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Selected run details */}
      {selectedRun && (() => {
        const run = trainingRuns.find(r => r.consortium_id === selectedRun)
        if (!run || !run.metrics) return null
        return (
          <div style={{
            background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`,
            padding: 24, marginTop: 20,
          }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: COLORS.text, margin: '0 0 16px' }}>
              Metricas: {run.consortium_name}
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 12 }}>
              {Object.entries(run.metrics).map(([key, value]) => (
                <div key={key} style={{ background: COLORS.bg, borderRadius: 10, padding: 16, textAlign: 'center' }}>
                  <p style={{ fontSize: 12, color: COLORS.muted, margin: '0 0 4px', textTransform: 'uppercase', fontWeight: 600 }}>{key}</p>
                  <p style={{ fontSize: 24, fontWeight: 700, color: COLORS.primary, margin: 0 }}>
                    {typeof value === 'number' ? value.toFixed(4) : value}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )
      })()}
    </div>
  )
}
