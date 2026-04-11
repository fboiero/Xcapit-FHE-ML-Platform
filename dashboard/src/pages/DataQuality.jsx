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

const SCORES = {
  completeness: { label: 'Completitud', value: 94, weight: 0.3 },
  consistency: { label: 'Consistencia', value: 87, weight: 0.25 },
  accuracy: { label: 'Precision', value: 91, weight: 0.25 },
  timeliness: { label: 'Actualidad', value: 82, weight: 0.2 },
}

const ALERTS = [
  { id: 1, message: 'Campo "diagnostico" vacio en 6.2% de los registros', severity: 'warning', dataset: 'pacientes_2026', time: 'Hace 2h' },
  { id: 2, message: 'Valores atipicos detectados en columna "costo_tratamiento"', severity: 'critical', dataset: 'costos_medicos', time: 'Hace 4h' },
  { id: 3, message: 'Formato de fecha inconsistente en 12 registros', severity: 'warning', dataset: 'admisiones', time: 'Hace 6h' },
  { id: 4, message: 'Datos de "region" actualizados correctamente', severity: 'info', dataset: 'pacientes_2026', time: 'Hace 8h' },
  { id: 5, message: 'Duplicados potenciales encontrados: 23 registros', severity: 'critical', dataset: 'historiales', time: 'Hace 12h' },
]

const RULES = [
  { id: 1, name: 'Campos obligatorios completos', type: 'Completitud', severity: 'Alta', active: true },
  { id: 2, name: 'Rango valido de edad (0-120)', type: 'Validacion', severity: 'Media', active: true },
  { id: 3, name: 'Formato de email valido', type: 'Formato', severity: 'Baja', active: true },
  { id: 4, name: 'Consistencia de codigos CIE-10', type: 'Consistencia', severity: 'Alta', active: true },
  { id: 5, name: 'Deteccion de duplicados exactos', type: 'Unicidad', severity: 'Alta', active: false },
  { id: 6, name: 'Valores fuera de rango estadistico', type: 'Precision', severity: 'Media', active: true },
  { id: 7, name: 'Antiguedad maxima de datos: 90 dias', type: 'Actualidad', severity: 'Media', active: false },
  { id: 8, name: 'Integridad referencial entre tablas', type: 'Consistencia', severity: 'Alta', active: true },
]

const ASSESSMENTS = [
  { date: '2026-03-14', score: 89, records: 45200, issues: 3, dataset: 'pacientes_2026' },
  { date: '2026-03-12', score: 85, records: 38100, issues: 5, dataset: 'costos_medicos' },
  { date: '2026-03-10', score: 92, records: 22400, issues: 1, dataset: 'admisiones' },
  { date: '2026-03-08', score: 78, records: 15800, issues: 8, dataset: 'historiales' },
  { date: '2026-03-06', score: 91, records: 44800, issues: 2, dataset: 'pacientes_2026' },
]

const SEVERITY_STYLES = {
  info: { bg: '#eff6ff', color: '#3b82f6' },
  warning: { bg: COLORS.warningLight, color: COLORS.warning },
  critical: { bg: COLORS.dangerLight, color: COLORS.danger },
}

function GaugeBar({ label, value }) {
  const color = value >= 90 ? COLORS.success : value >= 75 ? COLORS.warning : COLORS.danger
  return (
    <div style={{
      background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 20,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <span style={{ fontSize: 14, fontWeight: 600, color: COLORS.text }}>{label}</span>
        <span style={{ fontSize: 22, fontWeight: 700, color }}>{value}%</span>
      </div>
      <div style={{ width: '100%', height: 10, background: COLORS.border, borderRadius: 5, overflow: 'hidden' }}>
        <div style={{
          height: '100%', background: color, borderRadius: 5,
          width: `${value}%`, transition: 'width 0.8s ease',
        }} />
      </div>
    </div>
  )
}

export default function DataQuality() {
  const [rules, setRules] = useState(RULES)

  const overallScore = Math.round(
    Object.values(SCORES).reduce((sum, s) => sum + s.value * s.weight, 0)
  )

  const toggleRule = (id) => {
    setRules(prev => prev.map(r => r.id === id ? { ...r, active: !r.active } : r))
  }

  return (
    <div style={{ padding: 32, maxWidth: 1200, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, color: COLORS.text, margin: '0 0 8px' }}>
          Calidad de Datos
        </h1>
        <p style={{ fontSize: 16, color: COLORS.muted, margin: 0 }}>
          Monitoreo de calidad para datasets del consorcio de salud
        </p>
      </div>

      {/* Overall score + 4 gauges */}
      <div style={{ display: 'grid', gridTemplateColumns: '180px 1fr', gap: 24, marginBottom: 28 }}>
        <div style={{
          background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`,
          padding: 24, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        }}>
          <p style={{ fontSize: 13, color: COLORS.muted, margin: '0 0 8px', fontWeight: 600 }}>Calidad global</p>
          <div style={{
            width: 90, height: 90, borderRadius: '50%',
            background: `conic-gradient(${overallScore >= 85 ? COLORS.success : COLORS.warning} ${overallScore * 3.6}deg, ${COLORS.border} 0deg)`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <div style={{
              width: 70, height: 70, borderRadius: '50%', background: COLORS.card,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <span style={{ fontSize: 22, fontWeight: 700, color: overallScore >= 85 ? COLORS.success : COLORS.warning }}>
                {overallScore}%
              </span>
            </div>
          </div>
          <p style={{ fontSize: 12, color: COLORS.muted, margin: '8px 0 0' }}>Promedio ponderado</p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          {Object.values(SCORES).map((s) => (
            <GaugeBar key={s.label} label={s.label} value={s.value} />
          ))}
        </div>
      </div>

      {/* Two-column: Alerts + Rules */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 24 }}>
        {/* Alerts */}
        <div style={{
          background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 24,
        }}>
          <h2 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: '0 0 16px' }}>
            Alertas activas
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
            {ALERTS.map((alert) => {
              const sevStyle = SEVERITY_STYLES[alert.severity]
              return (
                <div key={alert.id} style={{
                  padding: '12px 0', borderBottom: `1px solid ${COLORS.border}`,
                  display: 'flex', alignItems: 'flex-start', gap: 10,
                }}>
                  <span style={{
                    padding: '2px 8px', borderRadius: 6, fontSize: 11, fontWeight: 600,
                    background: sevStyle.bg, color: sevStyle.color, whiteSpace: 'nowrap', marginTop: 2,
                  }}>
                    {alert.severity === 'critical' ? 'Critico' : alert.severity === 'warning' ? 'Alerta' : 'Info'}
                  </span>
                  <div style={{ flex: 1 }}>
                    <p style={{ fontSize: 14, color: COLORS.text, margin: '0 0 4px', lineHeight: 1.4 }}>
                      {alert.message}
                    </p>
                    <p style={{ fontSize: 12, color: COLORS.muted, margin: 0 }}>
                      {alert.dataset} - {alert.time}
                    </p>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Quality rules */}
        <div style={{
          background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 24,
        }}>
          <h2 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: '0 0 16px' }}>
            Reglas de calidad
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
            {rules.map((rule) => (
              <div key={rule.id} style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '10px 0', borderBottom: `1px solid ${COLORS.border}`,
              }}>
                <div style={{ flex: 1 }}>
                  <p style={{ fontSize: 14, color: COLORS.text, margin: '0 0 3px' }}>{rule.name}</p>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <span style={{ fontSize: 11, color: COLORS.muted }}>{rule.type}</span>
                    <span style={{
                      fontSize: 11, fontWeight: 600,
                      color: rule.severity === 'Alta' ? COLORS.danger : rule.severity === 'Media' ? COLORS.warning : COLORS.muted,
                    }}>
                      {rule.severity}
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => toggleRule(rule.id)}
                  style={{
                    width: 44, height: 24, borderRadius: 12, border: 'none', cursor: 'pointer',
                    background: rule.active ? COLORS.success : COLORS.border,
                    position: 'relative', transition: 'background 0.2s',
                  }}
                >
                  <div style={{
                    width: 18, height: 18, borderRadius: '50%', background: '#fff',
                    position: 'absolute', top: 3,
                    left: rule.active ? 23 : 3,
                    transition: 'left 0.2s',
                    boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
                  }} />
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent assessments */}
      <div style={{
        background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 24,
      }}>
        <h2 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: '0 0 16px' }}>
          Evaluaciones recientes
        </h2>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: `2px solid ${COLORS.border}` }}>
              {['Fecha', 'Dataset', 'Registros', 'Puntuacion', 'Problemas'].map((h) => (
                <th key={h} style={{
                  textAlign: 'left', padding: '10px 12px', fontSize: 13,
                  fontWeight: 600, color: COLORS.muted, textTransform: 'uppercase',
                }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {ASSESSMENTS.map((a, idx) => (
              <tr key={idx} style={{ borderBottom: `1px solid ${COLORS.border}` }}>
                <td style={{ padding: '12px', fontSize: 14, color: COLORS.text }}>
                  {new Date(a.date).toLocaleDateString('es-AR')}
                </td>
                <td style={{ padding: '12px', fontSize: 14, fontWeight: 500, color: COLORS.text }}>{a.dataset}</td>
                <td style={{ padding: '12px', fontSize: 14, color: COLORS.muted }}>{a.records.toLocaleString()}</td>
                <td style={{ padding: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{ width: 60, height: 6, background: COLORS.border, borderRadius: 3, overflow: 'hidden' }}>
                      <div style={{
                        height: '100%', borderRadius: 3,
                        background: a.score >= 90 ? COLORS.success : a.score >= 80 ? COLORS.warning : COLORS.danger,
                        width: `${a.score}%`,
                      }} />
                    </div>
                    <span style={{
                      fontSize: 14, fontWeight: 600,
                      color: a.score >= 90 ? COLORS.success : a.score >= 80 ? COLORS.warning : COLORS.danger,
                    }}>{a.score}%</span>
                  </div>
                </td>
                <td style={{ padding: '12px' }}>
                  <span style={{
                    padding: '3px 10px', borderRadius: 6, fontSize: 12, fontWeight: 600,
                    background: a.issues > 4 ? COLORS.dangerLight : a.issues > 0 ? COLORS.warningLight : COLORS.successLight,
                    color: a.issues > 4 ? COLORS.danger : a.issues > 0 ? COLORS.warning : COLORS.success,
                  }}>
                    {a.issues} {a.issues === 1 ? 'problema' : 'problemas'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
