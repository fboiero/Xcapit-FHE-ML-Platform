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
  { id: 'cost_predictor', name: 'Predictor de Costos Hospitalarios' },
  { id: 'risk_classifier', name: 'Clasificador de Riesgo Pacientes' },
  { id: 'readmission', name: 'Modelo de Readmision' },
]

const MODEL_RESULTS = {
  cost_predictor: {
    metrics: {
      r2: { value: 0.934, trend: 'up', prev: 0.921 },
      mae: { value: 1247, trend: 'down', prev: 1389 },
      rmse: { value: 1891, trend: 'down', prev: 2034 },
      f1: { value: 0.912, trend: 'up', prev: 0.898 },
      accuracy: { value: 94.2, trend: 'up', prev: 92.8 },
    },
    history: [
      { id: 'r1', date: '2026-03-12', duration: '42 min', samples: 125000, r2: 0.934, accuracy: 94.2, status: 'completado' },
      { id: 'r2', date: '2026-03-08', duration: '38 min', samples: 118000, r2: 0.921, accuracy: 92.8, status: 'completado' },
      { id: 'r3', date: '2026-03-01', duration: '51 min', samples: 110000, r2: 0.908, accuracy: 91.5, status: 'completado' },
      { id: 'r4', date: '2026-02-22', duration: '45 min', samples: 105000, r2: 0.895, accuracy: 90.1, status: 'completado' },
      { id: 'r5', date: '2026-02-15', duration: '47 min', samples: 98000, r2: 0.882, accuracy: 88.7, status: 'fallido' },
    ],
    features: [
      { name: 'Dias de estancia', importance: 0.23 },
      { name: 'Tipo de cirugia', importance: 0.19 },
      { name: 'Edad del paciente', importance: 0.15 },
      { name: 'Comorbilidades', importance: 0.13 },
      { name: 'Medicamentos', importance: 0.10 },
      { name: 'Especialidad', importance: 0.08 },
      { name: 'Region geografica', importance: 0.07 },
      { name: 'Tipo de seguro', importance: 0.05 },
    ],
    predictions: [
      { id: 'p1', actual: 15200, predicted: 14890, diff: -2.04 },
      { id: 'p2', actual: 8750, predicted: 9120, diff: 4.23 },
      { id: 'p3', actual: 32400, predicted: 31850, diff: -1.70 },
      { id: 'p4', actual: 5600, predicted: 5890, diff: 5.18 },
      { id: 'p5', actual: 21300, predicted: 20750, diff: -2.58 },
      { id: 'p6', actual: 12800, predicted: 13100, diff: 2.34 },
      { id: 'p7', actual: 45600, predicted: 44200, diff: -3.07 },
      { id: 'p8', actual: 9200, predicted: 9450, diff: 2.72 },
    ],
  },
  risk_classifier: {
    metrics: {
      r2: { value: 0.891, trend: 'up', prev: 0.878 },
      mae: { value: 0.087, trend: 'down', prev: 0.095 },
      rmse: { value: 0.112, trend: 'down', prev: 0.125 },
      f1: { value: 0.895, trend: 'up', prev: 0.881 },
      accuracy: { value: 91.3, trend: 'up', prev: 89.9 },
    },
    history: [
      { id: 'r6', date: '2026-03-10', duration: '35 min', samples: 95000, r2: 0.891, accuracy: 91.3, status: 'completado' },
      { id: 'r7', date: '2026-03-03', duration: '32 min', samples: 90000, r2: 0.878, accuracy: 89.9, status: 'completado' },
    ],
    features: [
      { name: 'Historial clinico', importance: 0.28 },
      { name: 'Edad', importance: 0.18 },
      { name: 'Presion arterial', importance: 0.14 },
      { name: 'IMC', importance: 0.11 },
      { name: 'Glucosa', importance: 0.10 },
      { name: 'Colesterol', importance: 0.08 },
      { name: 'Actividad fisica', importance: 0.06 },
      { name: 'Tabaquismo', importance: 0.05 },
    ],
    predictions: [
      { id: 'p9', actual: 0.82, predicted: 0.79, diff: -3.66 },
      { id: 'p10', actual: 0.35, predicted: 0.38, diff: 8.57 },
      { id: 'p11', actual: 0.91, predicted: 0.88, diff: -3.30 },
      { id: 'p12', actual: 0.15, predicted: 0.17, diff: 13.33 },
    ],
  },
  readmission: {
    metrics: {
      r2: { value: 0.856, trend: 'stable', prev: 0.854 },
      mae: { value: 0.102, trend: 'stable', prev: 0.104 },
      rmse: { value: 0.138, trend: 'down', prev: 0.142 },
      f1: { value: 0.871, trend: 'up', prev: 0.862 },
      accuracy: { value: 88.9, trend: 'up', prev: 87.5 },
    },
    history: [
      { id: 'r8', date: '2026-03-11', duration: '28 min', samples: 72000, r2: 0.856, accuracy: 88.9, status: 'completado' },
    ],
    features: [
      { name: 'Diagnostico previo', importance: 0.25 },
      { name: 'Dias internacion', importance: 0.20 },
      { name: 'Seguimiento post-alta', importance: 0.16 },
      { name: 'Edad', importance: 0.12 },
      { name: 'Comorbilidades', importance: 0.10 },
      { name: 'Medicacion', importance: 0.08 },
      { name: 'Soporte social', importance: 0.05 },
      { name: 'Distancia al hospital', importance: 0.04 },
    ],
    predictions: [
      { id: 'p13', actual: 0.72, predicted: 0.69, diff: -4.17 },
      { id: 'p14', actual: 0.28, predicted: 0.31, diff: 10.71 },
      { id: 'p15', actual: 0.55, predicted: 0.53, diff: -3.64 },
    ],
  },
}

const METRIC_LABELS = {
  r2: { label: 'R\u00B2', format: v => v.toFixed(3) },
  mae: { label: 'MAE', format: v => typeof v === 'number' && v > 1 ? v.toLocaleString() : v.toFixed(3) },
  rmse: { label: 'RMSE', format: v => typeof v === 'number' && v > 1 ? v.toLocaleString() : v.toFixed(3) },
  f1: { label: 'F1 Score', format: v => v.toFixed(3) },
  accuracy: { label: 'Accuracy', format: v => `${v}%` },
}

const TREND_DISPLAY = {
  up: { symbol: '\u25B2', color: COLORS.success },
  down: { symbol: '\u25BC', color: COLORS.success },
  stable: { symbol: '\u25CF', color: COLORS.warning },
}

export default function ResultsVisualization() {
  const [selectedModel, setSelectedModel] = useState('cost_predictor')

  const data = MODEL_RESULTS[selectedModel]

  return (
    <div style={{ padding: 32, maxWidth: 1200, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 32, flexWrap: 'wrap', gap: 16 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 700, color: COLORS.text, margin: '0 0 8px' }}>
            Visualizacion de Resultados
          </h1>
          <p style={{ fontSize: 16, color: COLORS.muted, margin: 0 }}>
            Resultados de entrenamiento FHE - prediccion de costos en salud
          </p>
        </div>
        <select
          value={selectedModel}
          onChange={e => setSelectedModel(e.target.value)}
          style={{
            padding: '10px 16px', borderRadius: 8, border: `1px solid ${COLORS.border}`,
            fontSize: 14, color: COLORS.text, outline: 'none', background: COLORS.card,
            minWidth: 260,
          }}
        >
          {MODELS.map(m => (
            <option key={m.id} value={m.id}>{m.name}</option>
          ))}
        </select>
      </div>

      {/* Metrics cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16, marginBottom: 28 }}>
        {Object.entries(data.metrics).map(([key, m]) => {
          const meta = METRIC_LABELS[key]
          const trendInfo = TREND_DISPLAY[m.trend]
          return (
            <div key={key} style={{
              background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 20,
            }}>
              <p style={{ fontSize: 13, color: COLORS.muted, margin: '0 0 4px' }}>{meta.label}</p>
              <p style={{ fontSize: 28, fontWeight: 700, color: COLORS.primary, margin: '0 0 8px' }}>
                {meta.format(m.value)}
              </p>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ fontSize: 12, color: trendInfo.color }}>{trendInfo.symbol}</span>
                <span style={{ fontSize: 12, color: COLORS.muted }}>
                  prev: {meta.format(m.prev)}
                </span>
              </div>
            </div>
          )
        })}
      </div>

      {/* Training history */}
      <div style={{
        background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`,
        padding: 24, marginBottom: 24,
      }}>
        <h3 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: '0 0 20px' }}>
          Historial de Entrenamiento
        </h3>
        {/* Table header */}
        <div style={{
          display: 'grid', gridTemplateColumns: '120px 80px 100px 80px 80px 100px',
          gap: 12, padding: '10px 16px', background: COLORS.bg, borderRadius: 8,
          fontSize: 12, fontWeight: 600, color: COLORS.muted, textTransform: 'uppercase',
          marginBottom: 4,
        }}>
          <span>Fecha</span>
          <span>Duracion</span>
          <span>Muestras</span>
          <span>R{'\u00B2'}</span>
          <span>Accuracy</span>
          <span>Estado</span>
        </div>
        {data.history.map(run => (
          <div key={run.id} style={{
            display: 'grid', gridTemplateColumns: '120px 80px 100px 80px 80px 100px',
            gap: 12, padding: '14px 16px', alignItems: 'center',
            borderBottom: `1px solid ${COLORS.border}`,
          }}>
            <span style={{ fontSize: 14, color: COLORS.text }}>{run.date}</span>
            <span style={{ fontSize: 14, color: COLORS.muted }}>{run.duration}</span>
            <span style={{ fontSize: 14, color: COLORS.muted }}>{run.samples.toLocaleString()}</span>
            <span style={{ fontSize: 14, fontWeight: 600, color: COLORS.primary }}>{run.r2.toFixed(3)}</span>
            <span style={{ fontSize: 14, fontWeight: 600, color: COLORS.success }}>{run.accuracy}%</span>
            <span style={{
              padding: '3px 10px', borderRadius: 6, fontSize: 12, fontWeight: 600,
              background: run.status === 'completado' ? COLORS.successLight : COLORS.dangerLight,
              color: run.status === 'completado' ? COLORS.success : COLORS.danger,
              display: 'inline-block',
            }}>
              {run.status === 'completado' ? 'Completado' : 'Fallido'}
            </span>
          </div>
        ))}
      </div>

      {/* Feature importance + Predictions side by side */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: 16 }}>
        {/* Feature importance */}
        <div style={{
          background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 24,
        }}>
          <h3 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: '0 0 20px' }}>
            Importancia de Features
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {data.features.map((f, idx) => (
              <div key={f.name}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span style={{ fontSize: 13, color: COLORS.text }}>{f.name}</span>
                  <span style={{ fontSize: 13, fontWeight: 600, color: COLORS.primary }}>
                    {(f.importance * 100).toFixed(0)}%
                  </span>
                </div>
                <div style={{ width: '100%', height: 8, background: COLORS.bg, borderRadius: 4, overflow: 'hidden' }}>
                  <div style={{
                    height: '100%', borderRadius: 4,
                    width: `${f.importance * 100 / data.features[0].importance * 100}%`,
                    background: idx < 3 ? COLORS.primary : COLORS.accent,
                    transition: 'width 0.3s',
                  }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Predictions vs Actuals */}
        <div style={{
          background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 24,
        }}>
          <h3 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: '0 0 20px' }}>
            Predicciones vs Valores Reales
          </h3>
          {/* Table header */}
          <div style={{
            display: 'grid', gridTemplateColumns: '1fr 1fr 1fr',
            gap: 8, padding: '10px 12px', background: COLORS.bg, borderRadius: 8,
            fontSize: 12, fontWeight: 600, color: COLORS.muted, textTransform: 'uppercase',
            marginBottom: 4,
          }}>
            <span>Real</span>
            <span>Predicho</span>
            <span>Diferencia</span>
          </div>
          {data.predictions.map(p => (
            <div key={p.id} style={{
              display: 'grid', gridTemplateColumns: '1fr 1fr 1fr',
              gap: 8, padding: '10px 12px', alignItems: 'center',
              borderBottom: `1px solid ${COLORS.border}`,
            }}>
              <span style={{ fontSize: 14, color: COLORS.text, fontWeight: 500 }}>
                {typeof p.actual === 'number' && p.actual > 1 ? `$${p.actual.toLocaleString()}` : p.actual}
              </span>
              <span style={{ fontSize: 14, color: COLORS.primary, fontWeight: 500 }}>
                {typeof p.predicted === 'number' && p.predicted > 1 ? `$${p.predicted.toLocaleString()}` : p.predicted}
              </span>
              <span style={{
                fontSize: 14, fontWeight: 600,
                color: Math.abs(p.diff) < 3 ? COLORS.success : Math.abs(p.diff) < 6 ? COLORS.warning : COLORS.danger,
              }}>
                {p.diff > 0 ? '+' : ''}{p.diff.toFixed(2)}%
              </span>
            </div>
          ))}
          <div style={{
            marginTop: 12, padding: '10px 16px', background: COLORS.primaryLight, borderRadius: 8,
          }}>
            <span style={{ fontSize: 13, color: COLORS.primary, fontWeight: 500 }}>
              Error promedio: {(data.predictions.reduce((s, p) => s + Math.abs(p.diff), 0) / data.predictions.length).toFixed(2)}%
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
