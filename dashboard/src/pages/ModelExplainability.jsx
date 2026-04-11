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

const EXPLANATION_TYPES = ['SHAP', 'LIME', 'Permutation Importance']

const FEATURES = {
  SHAP: [
    { name: 'Severidad del diagnostico', importance: 0.342, ciLow: 0.318, ciHigh: 0.366, direction: 'positive' },
    { name: 'Edad del paciente', importance: 0.268, ciLow: 0.245, ciHigh: 0.291, direction: 'positive' },
    { name: 'BMI', importance: 0.187, ciLow: 0.165, ciHigh: 0.209, direction: 'positive' },
    { name: 'Historial de internaciones', importance: 0.124, ciLow: 0.105, ciHigh: 0.143, direction: 'positive' },
    { name: 'Region geografica', importance: 0.079, ciLow: 0.062, ciHigh: 0.096, direction: 'negative' },
    { name: 'Tipo de cobertura', importance: 0.058, ciLow: 0.043, ciHigh: 0.073, direction: 'negative' },
    { name: 'Genero', importance: 0.031, ciLow: 0.019, ciHigh: 0.043, direction: 'neutral' },
    { name: 'Cantidad de dependientes', importance: 0.024, ciLow: 0.015, ciHigh: 0.033, direction: 'neutral' },
  ],
  LIME: [
    { name: 'Severidad del diagnostico', importance: 0.356, ciLow: 0.330, ciHigh: 0.382, direction: 'positive' },
    { name: 'Edad del paciente', importance: 0.251, ciLow: 0.228, ciHigh: 0.274, direction: 'positive' },
    { name: 'BMI', importance: 0.198, ciLow: 0.175, ciHigh: 0.221, direction: 'positive' },
    { name: 'Historial de internaciones', importance: 0.115, ciLow: 0.098, ciHigh: 0.132, direction: 'positive' },
    { name: 'Region geografica', importance: 0.068, ciLow: 0.052, ciHigh: 0.084, direction: 'negative' },
    { name: 'Tipo de cobertura', importance: 0.051, ciLow: 0.037, ciHigh: 0.065, direction: 'negative' },
    { name: 'Genero', importance: 0.028, ciLow: 0.016, ciHigh: 0.040, direction: 'neutral' },
    { name: 'Cantidad de dependientes', importance: 0.019, ciLow: 0.010, ciHigh: 0.028, direction: 'neutral' },
  ],
  'Permutation Importance': [
    { name: 'Severidad del diagnostico', importance: 0.329, ciLow: 0.305, ciHigh: 0.353, direction: 'positive' },
    { name: 'Edad del paciente', importance: 0.275, ciLow: 0.252, ciHigh: 0.298, direction: 'positive' },
    { name: 'BMI', importance: 0.175, ciLow: 0.153, ciHigh: 0.197, direction: 'positive' },
    { name: 'Historial de internaciones', importance: 0.132, ciLow: 0.113, ciHigh: 0.151, direction: 'positive' },
    { name: 'Region geografica', importance: 0.085, ciLow: 0.068, ciHigh: 0.102, direction: 'negative' },
    { name: 'Tipo de cobertura', importance: 0.062, ciLow: 0.047, ciHigh: 0.077, direction: 'negative' },
    { name: 'Genero', importance: 0.035, ciLow: 0.023, ciHigh: 0.047, direction: 'neutral' },
    { name: 'Cantidad de dependientes', importance: 0.021, ciLow: 0.012, ciHigh: 0.030, direction: 'neutral' },
  ],
}

const INSIGHTS = [
  {
    id: 1,
    type: 'drift',
    title: 'Drift detectado en feature "BMI"',
    description: 'La distribucion de BMI en los datos recientes muestra un desplazamiento de +0.8 desviaciones estandar respecto al conjunto de entrenamiento original. Considerar re-entrenamiento.',
    severity: 'warning',
  },
  {
    id: 2,
    type: 'feature_change',
    title: 'Importancia de "Region" en aumento',
    description: 'La importancia de la feature "Region geografica" aumento un 23% en las ultimas 3 evaluaciones. Posible sesgo geografico emergente.',
    severity: 'warning',
  },
  {
    id: 3,
    type: 'stability',
    title: 'Modelo estable para top-3 features',
    description: 'Las 3 features mas importantes (Severidad, Edad, BMI) mantienen rankings consistentes en SHAP, LIME y Permutation Importance con varianza < 5%.',
    severity: 'info',
  },
  {
    id: 4,
    type: 'fairness',
    title: 'Feature "Genero" con baja importancia',
    description: 'La feature "Genero" tiene una importancia < 3.5% en todos los metodos, lo que sugiere baja influencia en las predicciones. Resultado favorable para equidad.',
    severity: 'success',
  },
]

const INSIGHT_STYLES = {
  warning: { bg: COLORS.warningLight, color: COLORS.warning },
  info: { bg: COLORS.primaryLight, color: COLORS.primary },
  success: { bg: COLORS.successLight, color: COLORS.success },
}

const DIRECTION_COLORS = {
  positive: COLORS.success,
  negative: COLORS.danger,
  neutral: COLORS.muted,
}

export default function ModelExplainability() {
  const [selectedMethod, setSelectedMethod] = useState('SHAP')

  const features = FEATURES[selectedMethod]
  const maxImportance = Math.max(...features.map(f => f.importance))

  return (
    <div style={{ padding: 32, maxWidth: 1200, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, color: COLORS.text, margin: '0 0 8px' }}>
          Interpretabilidad del Modelo
        </h1>
        <p style={{ fontSize: 16, color: COLORS.muted, margin: 0 }}>
          Prediccion de costos medicos - Importancia de features y explicaciones
        </p>
      </div>

      {/* Method selector */}
      <div style={{
        display: 'flex', gap: 8, marginBottom: 24, background: COLORS.bg,
        padding: 4, borderRadius: 10, width: 'fit-content',
      }}>
        {EXPLANATION_TYPES.map((method) => (
          <button
            key={method}
            onClick={() => setSelectedMethod(method)}
            style={{
              padding: '8px 20px', borderRadius: 8, border: 'none',
              background: selectedMethod === method ? COLORS.primary : 'transparent',
              color: selectedMethod === method ? '#fff' : COLORS.muted,
              fontSize: 14, fontWeight: 600, cursor: 'pointer',
              transition: 'background 0.2s, color 0.2s',
            }}
          >
            {method}
          </button>
        ))}
      </div>

      {/* Two-column: Feature importance chart + Top features */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: 24, marginBottom: 24 }}>
        {/* Feature importance bars */}
        <div style={{
          background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 24,
        }}>
          <h2 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: '0 0 20px' }}>
            Importancia de Features ({selectedMethod})
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {features.map((f, idx) => {
              const barWidth = Math.round((f.importance / maxImportance) * 100)
              const dirColor = DIRECTION_COLORS[f.direction]
              return (
                <div key={idx}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span style={{ fontSize: 13, fontWeight: 500, color: COLORS.text }}>{f.name}</span>
                    <span style={{ fontSize: 13, fontWeight: 600, color: dirColor }}>
                      {(f.importance * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div style={{ position: 'relative' }}>
                    <div style={{
                      width: '100%', height: 24, background: COLORS.bg, borderRadius: 6, overflow: 'hidden',
                    }}>
                      <div style={{
                        height: '100%', borderRadius: 6,
                        width: `${barWidth}%`,
                        background: `linear-gradient(90deg, ${dirColor}33, ${dirColor}88)`,
                        transition: 'width 0.5s ease',
                      }} />
                    </div>
                    {/* Confidence interval markers */}
                    <div style={{
                      position: 'absolute', top: 8, height: 8,
                      left: `${(f.ciLow / maxImportance) * 100}%`,
                      width: `${((f.ciHigh - f.ciLow) / maxImportance) * 100}%`,
                      background: `${dirColor}44`, borderRadius: 2,
                      borderLeft: `2px solid ${dirColor}`,
                      borderRight: `2px solid ${dirColor}`,
                    }} />
                  </div>
                </div>
              )
            })}
          </div>
          <p style={{ fontSize: 11, color: COLORS.muted, margin: '16px 0 0' }}>
            Las barras sombreadas muestran los intervalos de confianza al 95%
          </p>
        </div>

        {/* Top 5 features detail */}
        <div style={{
          background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 24,
        }}>
          <h2 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: '0 0 16px' }}>
            Top 5 Features
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
            {features.slice(0, 5).map((f, idx) => {
              const dirColor = DIRECTION_COLORS[f.direction]
              return (
                <div key={idx} style={{
                  padding: '14px 0', borderBottom: `1px solid ${COLORS.border}`,
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{
                        width: 24, height: 24, borderRadius: 6, background: COLORS.primaryLight,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: 12, fontWeight: 700, color: COLORS.primary,
                      }}>
                        {idx + 1}
                      </span>
                      <span style={{ fontSize: 14, fontWeight: 600, color: COLORS.text }}>{f.name}</span>
                    </div>
                    <span style={{
                      padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 600,
                      background: f.direction === 'positive' ? COLORS.successLight : f.direction === 'negative' ? COLORS.dangerLight : COLORS.bg,
                      color: dirColor,
                    }}>
                      {f.direction === 'positive' ? 'Positiva' : f.direction === 'negative' ? 'Negativa' : 'Neutral'}
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: 16, paddingLeft: 32 }}>
                    <div>
                      <span style={{ fontSize: 11, color: COLORS.muted }}>Score: </span>
                      <span style={{ fontSize: 13, fontWeight: 600, color: COLORS.text }}>{f.importance.toFixed(3)}</span>
                    </div>
                    <div>
                      <span style={{ fontSize: 11, color: COLORS.muted }}>IC 95%: </span>
                      <span style={{ fontSize: 13, color: COLORS.muted }}>
                        [{f.ciLow.toFixed(3)}, {f.ciHigh.toFixed(3)}]
                      </span>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* Insights */}
      <div style={{
        background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 24,
      }}>
        <h2 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: '0 0 16px' }}>
          Observaciones automaticas
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          {INSIGHTS.map((insight) => {
            const style = INSIGHT_STYLES[insight.severity]
            return (
              <div key={insight.id} style={{
                background: style.bg, borderRadius: 10, padding: 16,
                borderLeft: `4px solid ${style.color}`,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                  <span style={{
                    width: 8, height: 8, borderRadius: '50%', background: style.color,
                  }} />
                  <h3 style={{ fontSize: 14, fontWeight: 600, color: COLORS.text, margin: 0 }}>
                    {insight.title}
                  </h3>
                </div>
                <p style={{ fontSize: 13, color: COLORS.text, margin: 0, lineHeight: 1.6 }}>
                  {insight.description}
                </p>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
