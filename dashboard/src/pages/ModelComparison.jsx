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

const MODELS = [
  {
    id: 'local_a', name: 'Modelo Local A', type: 'Regresion Lineal',
    metrics: { r2: 0.79, mae: 0.087, rmse: 0.112, accuracy: 0.81, f1: 0.78, training_time: '4.2s', samples: 500 },
  },
  {
    id: 'local_b', name: 'Modelo Local B', type: 'Regresion Logistica',
    metrics: { r2: 0.83, mae: 0.071, rmse: 0.095, accuracy: 0.85, f1: 0.83, training_time: '6.1s', samples: 800 },
  },
  {
    id: 'consortium', name: 'Modelo Consorcio FHE', type: 'Reg. Lineal (FHE)',
    metrics: { r2: 0.94, mae: 0.042, rmse: 0.058, accuracy: 0.93, f1: 0.92, training_time: '12.4s', samples: 3000 },
  },
]

const METRIC_DEFS = [
  { key: 'r2', label: 'R² Score', higher: true, max: 1 },
  { key: 'mae', label: 'MAE', higher: false, max: 0.15 },
  { key: 'rmse', label: 'RMSE', higher: false, max: 0.2 },
  { key: 'accuracy', label: 'Accuracy', higher: true, max: 1 },
  { key: 'f1', label: 'F1 Score', higher: true, max: 1 },
  { key: 'training_time', label: 'Tiempo entrenamiento', higher: false, max: null },
  { key: 'samples', label: 'Muestras', higher: true, max: null },
]

export default function ModelComparison() {
  const [leftId, setLeftId] = useState('local_a')
  const [rightId, setRightId] = useState('consortium')

  const leftModel = MODELS.find(m => m.id === leftId)
  const rightModel = MODELS.find(m => m.id === rightId)

  const getWinner = (metric) => {
    const lv = leftModel.metrics[metric.key]
    const rv = rightModel.metrics[metric.key]
    if (typeof lv === 'string') return null
    if (metric.higher) return lv > rv ? 'left' : rv > lv ? 'right' : 'tie'
    return lv < rv ? 'left' : rv < lv ? 'right' : 'tie'
  }

  const leftWins = METRIC_DEFS.filter(m => getWinner(m) === 'left').length
  const rightWins = METRIC_DEFS.filter(m => getWinner(m) === 'right').length
  const recommended = leftWins > rightWins ? leftModel : rightModel

  return (
    <div style={{ padding: 32, maxWidth: 1200, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, color: COLORS.text, margin: '0 0 8px' }}>
          Comparacion de Modelos
        </h1>
        <p style={{ fontSize: 16, color: COLORS.muted, margin: 0 }}>
          Compara metricas entre modelos locales y del consorcio
        </p>
      </div>

      {/* Model selectors */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr', gap: 16, marginBottom: 24, alignItems: 'center' }}>
        <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 20 }}>
          <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: COLORS.muted, marginBottom: 6, textTransform: 'uppercase', letterSpacing: 0.5 }}>Modelo A</label>
          <select value={leftId} onChange={e => setLeftId(e.target.value)} style={{
            width: '100%', padding: '10px 14px', borderRadius: 8, border: `1px solid ${COLORS.border}`,
            fontSize: 14, color: COLORS.text, background: '#fff', outline: 'none', boxSizing: 'border-box',
          }}>
            {MODELS.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
          </select>
          <p style={{ fontSize: 12, color: COLORS.muted, marginTop: 6, marginBottom: 0 }}>{leftModel.type}</p>
        </div>

        <div style={{ fontSize: 18, fontWeight: 700, color: COLORS.muted, textAlign: 'center' }}>VS</div>

        <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 20 }}>
          <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: COLORS.muted, marginBottom: 6, textTransform: 'uppercase', letterSpacing: 0.5 }}>Modelo B</label>
          <select value={rightId} onChange={e => setRightId(e.target.value)} style={{
            width: '100%', padding: '10px 14px', borderRadius: 8, border: `1px solid ${COLORS.border}`,
            fontSize: 14, color: COLORS.text, background: '#fff', outline: 'none', boxSizing: 'border-box',
          }}>
            {MODELS.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
          </select>
          <p style={{ fontSize: 12, color: COLORS.muted, marginTop: 6, marginBottom: 0 }}>{rightModel.type}</p>
        </div>
      </div>

      {/* Comparison table */}
      <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 24, marginBottom: 24 }}>
        <h2 style={{ fontSize: 17, fontWeight: 600, color: COLORS.text, margin: '0 0 20px' }}>Metricas</h2>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: `2px solid ${COLORS.border}` }}>
                {['Metrica', leftModel.name, 'Comparacion', rightModel.name, ''].map((h, i) => (
                  <th key={i} style={{
                    textAlign: i === 2 ? 'center' : 'left', padding: '10px 12px', fontSize: 12,
                    fontWeight: 600, color: COLORS.muted, textTransform: 'uppercase', letterSpacing: 0.5,
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {METRIC_DEFS.map(metric => {
                const lv = leftModel.metrics[metric.key]
                const rv = rightModel.metrics[metric.key]
                const winner = getWinner(metric)
                const isNumeric = typeof lv === 'number'
                const lvPct = isNumeric && metric.max ? (lv / metric.max) * 100 : 0
                const rvPct = isNumeric && metric.max ? (rv / metric.max) * 100 : 0

                return (
                  <tr key={metric.key} style={{ borderBottom: `1px solid ${COLORS.border}` }}>
                    <td style={{ padding: '12px', fontSize: 14, fontWeight: 500, color: COLORS.text }}>{metric.label}</td>
                    <td style={{
                      padding: '12px', fontSize: 14, fontWeight: 600,
                      color: winner === 'left' ? COLORS.success : COLORS.text,
                    }}>
                      {lv}
                    </td>
                    <td style={{ padding: '12px', width: 200 }}>
                      {isNumeric && metric.max && (
                        <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
                          <div style={{ flex: 1, height: 8, background: COLORS.bg, borderRadius: 4, overflow: 'hidden', direction: 'rtl' }}>
                            <div style={{ height: '100%', background: winner === 'left' ? COLORS.success : COLORS.warning, width: `${lvPct}%`, borderRadius: 4 }} />
                          </div>
                          <div style={{ flex: 1, height: 8, background: COLORS.bg, borderRadius: 4, overflow: 'hidden' }}>
                            <div style={{ height: '100%', background: winner === 'right' ? COLORS.success : COLORS.warning, width: `${rvPct}%`, borderRadius: 4 }} />
                          </div>
                        </div>
                      )}
                    </td>
                    <td style={{
                      padding: '12px', fontSize: 14, fontWeight: 600,
                      color: winner === 'right' ? COLORS.success : COLORS.text,
                    }}>
                      {rv}
                    </td>
                    <td style={{ padding: '12px', width: 40, textAlign: 'center' }}>
                      {winner === 'left' && (
                        <span style={{ padding: '2px 8px', borderRadius: 4, background: COLORS.successLight, color: COLORS.success, fontSize: 11, fontWeight: 700 }}>A</span>
                      )}
                      {winner === 'right' && (
                        <span style={{ padding: '2px 8px', borderRadius: 4, background: COLORS.primaryLight, color: COLORS.primary, fontSize: 11, fontWeight: 700 }}>B</span>
                      )}
                      {winner === 'tie' && (
                        <span style={{ padding: '2px 8px', borderRadius: 4, background: COLORS.bg, color: COLORS.muted, fontSize: 11, fontWeight: 700 }}>=</span>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recommendation */}
      <div style={{
        background: `linear-gradient(135deg, ${COLORS.primaryLight}, #f5f3ff)`,
        borderRadius: 12, border: `1px solid ${COLORS.primary}33`, padding: 24,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16,
      }}>
        <div>
          <p style={{ fontSize: 12, fontWeight: 600, color: COLORS.primary, margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: 0.5 }}>Recomendacion</p>
          <h3 style={{ fontSize: 20, fontWeight: 700, color: COLORS.text, margin: '0 0 6px' }}>{recommended.name}</h3>
          <p style={{ fontSize: 14, color: COLORS.muted, margin: 0 }}>
            Gana en {Math.max(leftWins, rightWins)} de {METRIC_DEFS.length} metricas evaluadas.
            {recommended.id === 'consortium' && ' El modelo del consorcio aprovecha datos agregados de multiples participantes para mayor precision.'}
          </p>
        </div>
        <div style={{
          padding: '8px 16px', borderRadius: 8, background: COLORS.primary, color: '#fff',
          fontSize: 13, fontWeight: 600,
        }}>
          Mejor rendimiento general
        </div>
      </div>
    </div>
  )
}
