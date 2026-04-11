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

const WORKFLOWS = [
  {
    id: 1, name: 'Reentrenar modelo semanal', trigger: 'cron', schedule: 'Lunes 03:00 UTC',
    lastRun: '2026-03-10 03:00', nextRun: '2026-03-17 03:00', status: 'active',
    steps: ['Descargar datos nuevos', 'Validar calidad', 'Cifrar con FHE', 'Entrenar modelo', 'Evaluar metricas', 'Desplegar si mejora'],
  },
  {
    id: 2, name: 'Alerta calidad de datos', trigger: 'event', schedule: 'Al subir datos',
    lastRun: '2026-03-13 14:22', nextRun: 'Proximo upload', status: 'active',
    steps: ['Detectar nuevo upload', 'Ejecutar checks de calidad', 'Enviar alerta si falla'],
  },
  {
    id: 3, name: 'Backup automatico', trigger: 'cron', schedule: 'Diario 02:00 UTC',
    lastRun: '2026-03-14 02:00', nextRun: '2026-03-15 02:00', status: 'active',
    steps: ['Snapshot base de datos', 'Comprimir backup', 'Subir a S3', 'Verificar integridad'],
  },
  {
    id: 4, name: 'Reporte mensual', trigger: 'cron', schedule: '1er dia del mes 08:00',
    lastRun: '2026-03-01 08:00', nextRun: '2026-04-01 08:00', status: 'active',
    steps: ['Recopilar metricas', 'Generar graficos', 'Compilar PDF', 'Enviar por email'],
  },
  {
    id: 5, name: 'Limpieza de cache', trigger: 'manual', schedule: 'Manual',
    lastRun: '2026-03-08 11:30', nextRun: '-', status: 'inactive',
    steps: ['Limpiar cache de Redis', 'Purgar archivos temporales', 'Notificar admin'],
  },
]

const TRIGGER_MAP = {
  cron: { label: 'Programado', bg: COLORS.primaryLight, color: COLORS.primary },
  event: { label: 'Evento', bg: COLORS.warningLight, color: COLORS.warning },
  manual: { label: 'Manual', bg: COLORS.bg, color: COLORS.muted },
}

const EXECUTIONS = [
  { id: 1, workflow: 'Backup automatico', trigger: 'cron', duration: '1m 23s', status: 'success', time: '2026-03-14 02:01' },
  { id: 2, workflow: 'Alerta calidad de datos', trigger: 'event', duration: '8s', status: 'success', time: '2026-03-13 14:22' },
  { id: 3, workflow: 'Reentrenar modelo semanal', trigger: 'cron', duration: '14m 52s', status: 'success', time: '2026-03-10 03:14' },
  { id: 4, workflow: 'Limpieza de cache', trigger: 'manual', duration: '32s', status: 'success', time: '2026-03-08 11:30' },
  { id: 5, workflow: 'Alerta calidad de datos', trigger: 'event', duration: '6s', status: 'failed', time: '2026-03-07 09:15' },
  { id: 6, workflow: 'Reporte mensual', trigger: 'cron', duration: '2m 41s', status: 'success', time: '2026-03-01 08:02' },
  { id: 7, workflow: 'Backup automatico', trigger: 'cron', duration: '1m 18s', status: 'success', time: '2026-03-13 02:01' },
]

const EXEC_STATUS = {
  success: { label: 'Exitoso', bg: COLORS.successLight, color: COLORS.success },
  failed: { label: 'Fallido', bg: COLORS.dangerLight, color: COLORS.danger },
}

export default function WorkflowAutomation() {
  const [expandedId, setExpandedId] = useState(null)

  const activeCount = WORKFLOWS.filter(w => w.status === 'active').length

  return (
    <div style={{ padding: 32, maxWidth: 1200, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 28, flexWrap: 'wrap', gap: 16 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 700, color: COLORS.text, margin: '0 0 8px' }}>
            Automatizacion de Flujos
          </h1>
          <p style={{ fontSize: 16, color: COLORS.muted, margin: 0 }}>
            Configura y gestiona pipelines automatizados
          </p>
        </div>
        <button style={{
          padding: '10px 20px', borderRadius: 8, border: 'none',
          background: COLORS.primary, color: '#fff', fontSize: 14,
          fontWeight: 600, cursor: 'pointer',
        }}>
          Nuevo Flujo
        </button>
      </div>

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16, marginBottom: 28 }}>
        {[
          { label: 'Flujos activos', value: activeCount, color: COLORS.success },
          { label: 'Ejecuciones hoy', value: 3, color: COLORS.primary },
          { label: 'Tasa de exito', value: '95%', color: COLORS.accent },
          { label: 'Ultima ejecucion', value: '02:01', color: COLORS.muted },
        ].map(s => (
          <div key={s.label} style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 20 }}>
            <p style={{ fontSize: 13, color: COLORS.muted, margin: '0 0 4px' }}>{s.label}</p>
            <p style={{ fontSize: 28, fontWeight: 700, color: s.color, margin: 0 }}>{s.value}</p>
          </div>
        ))}
      </div>

      {/* Workflows list */}
      <div style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: '0 0 16px' }}>Flujos configurados</h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {WORKFLOWS.map(wf => {
            const triggerInfo = TRIGGER_MAP[wf.trigger]
            const isExpanded = expandedId === wf.id
            return (
              <div key={wf.id} style={{
                background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, overflow: 'hidden',
              }}>
                <div onClick={() => setExpandedId(isExpanded ? null : wf.id)} style={{
                  padding: '18px 24px', cursor: 'pointer',
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  flexWrap: 'wrap', gap: 12,
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, minWidth: 200 }}>
                    <div style={{
                      width: 10, height: 10, borderRadius: '50%',
                      background: wf.status === 'active' ? COLORS.success : COLORS.muted,
                    }} />
                    <div>
                      <h3 style={{ fontSize: 15, fontWeight: 600, color: COLORS.text, margin: '0 0 4px' }}>{wf.name}</h3>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{
                          padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 600,
                          background: triggerInfo.bg, color: triggerInfo.color,
                        }}>{triggerInfo.label}</span>
                        <span style={{ fontSize: 12, color: COLORS.muted }}>{wf.schedule}</span>
                      </div>
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 24, flexShrink: 0 }}>
                    <div style={{ textAlign: 'center' }}>
                      <p style={{ fontSize: 12, color: COLORS.muted, margin: '0 0 2px' }}>Ultima ejecucion</p>
                      <p style={{ fontSize: 13, fontWeight: 600, color: COLORS.text, margin: 0 }}>{wf.lastRun}</p>
                    </div>
                    <div style={{ textAlign: 'center' }}>
                      <p style={{ fontSize: 12, color: COLORS.muted, margin: '0 0 2px' }}>Proxima</p>
                      <p style={{ fontSize: 13, fontWeight: 600, color: COLORS.text, margin: 0 }}>{wf.nextRun}</p>
                    </div>
                    <span style={{
                      fontSize: 18, color: COLORS.muted, transition: 'transform 0.2s',
                      transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
                    }}>&#9662;</span>
                  </div>
                </div>

                {/* Expanded: workflow steps preview */}
                {isExpanded && (
                  <div style={{ padding: '0 24px 24px', borderTop: `1px solid ${COLORS.border}`, paddingTop: 20 }}>
                    <p style={{ fontSize: 13, fontWeight: 600, color: COLORS.muted, margin: '0 0 12px', textTransform: 'uppercase', letterSpacing: 0.5 }}>Pasos del flujo</p>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
                      {wf.steps.map((step, i) => (
                        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 24 }}>
                            <div style={{
                              width: 24, height: 24, borderRadius: '50%', background: COLORS.primaryLight,
                              border: `2px solid ${COLORS.primary}`, display: 'flex', alignItems: 'center',
                              justifyContent: 'center', fontSize: 11, fontWeight: 700, color: COLORS.primary,
                              zIndex: 1,
                            }}>
                              {i + 1}
                            </div>
                            {i < wf.steps.length - 1 && (
                              <div style={{ width: 2, height: 20, background: COLORS.border }} />
                            )}
                          </div>
                          <div style={{
                            flex: 1, padding: '8px 14px', background: COLORS.bg, borderRadius: 6,
                            fontSize: 13, color: COLORS.text, marginBottom: i < wf.steps.length - 1 ? 0 : 0,
                          }}>
                            {step}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Recent executions */}
      <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 24 }}>
        <h2 style={{ fontSize: 17, fontWeight: 600, color: COLORS.text, margin: '0 0 16px' }}>Ejecuciones recientes</h2>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: `2px solid ${COLORS.border}` }}>
                {['Flujo', 'Trigger', 'Duracion', 'Estado', 'Fecha'].map(h => (
                  <th key={h} style={{
                    textAlign: 'left', padding: '10px 12px', fontSize: 12,
                    fontWeight: 600, color: COLORS.muted, textTransform: 'uppercase', letterSpacing: 0.5,
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {EXECUTIONS.map(exec => {
                const execStatus = EXEC_STATUS[exec.status]
                const triggerInfo = TRIGGER_MAP[exec.trigger]
                return (
                  <tr key={exec.id} style={{ borderBottom: `1px solid ${COLORS.border}` }}>
                    <td style={{ padding: '10px 12px', fontSize: 14, fontWeight: 500, color: COLORS.text }}>{exec.workflow}</td>
                    <td style={{ padding: '10px 12px' }}>
                      <span style={{
                        padding: '3px 8px', borderRadius: 4, fontSize: 11, fontWeight: 600,
                        background: triggerInfo.bg, color: triggerInfo.color,
                      }}>{triggerInfo.label}</span>
                    </td>
                    <td style={{ padding: '10px 12px', fontSize: 13, color: COLORS.muted, fontFamily: 'monospace' }}>{exec.duration}</td>
                    <td style={{ padding: '10px 12px' }}>
                      <span style={{
                        padding: '3px 10px', borderRadius: 6, fontSize: 12, fontWeight: 600,
                        background: execStatus.bg, color: execStatus.color,
                      }}>{execStatus.label}</span>
                    </td>
                    <td style={{ padding: '10px 12px', fontSize: 13, color: COLORS.muted }}>{exec.time}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
