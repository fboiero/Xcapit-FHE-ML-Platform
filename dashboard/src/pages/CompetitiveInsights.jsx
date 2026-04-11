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

const BENCHMARKS = [
  { metric: 'Precision del modelo', company: 94.2, p25: 72, p50: 81, p75: 89, p90: 95, unit: '%' },
  { metric: 'Tiempo de entrenamiento', company: 45, p25: 120, p50: 85, p75: 55, p90: 30, unit: 'min', inverted: true },
  { metric: 'Volumen de datos procesados', company: 2.4, p25: 0.5, p50: 1.2, p75: 2.0, p90: 3.5, unit: 'M registros' },
  { metric: 'Nivel de encriptacion', company: 256, p25: 128, p50: 128, p75: 192, p90: 256, unit: 'bits' },
  { metric: 'Adopcion de FHE', company: 87, p25: 30, p50: 52, p75: 71, p90: 90, unit: '%' },
]

const STRENGTHS = [
  { text: 'Precision de modelo superior al percentil 90', trend: 'improving' },
  { text: 'Nivel de encriptacion CKKS 256-bit (maximo)', trend: 'stable' },
  { text: 'Alta adopcion de FHE entre equipos', trend: 'improving' },
]

const WEAKNESSES = [
  { text: 'Tiempo de entrenamiento por encima del p50', trend: 'improving' },
  { text: 'Variedad de modelos limitada vs competidores', trend: 'stable' },
]

const OPPORTUNITIES = [
  { text: 'Implementar ensemble models para superar p90 en precision', trend: 'improving' },
  { text: 'Optimizar pipeline FHE para reducir latencia 40%', trend: 'improving' },
  { text: 'Expandir a verticales: finanzas y seguros', trend: 'stable' },
]

const TREND_ICONS = {
  improving: { symbol: '\u25B2', color: COLORS.success, label: 'Mejorando' },
  stable: { symbol: '\u25CF', color: COLORS.warning, label: 'Estable' },
  declining: { symbol: '\u25BC', color: COLORS.danger, label: 'Declinando' },
}

const HISTORY = [
  { month: 'Ene 2026', percentile: 78 },
  { month: 'Feb 2026', percentile: 82 },
  { month: 'Mar 2026', percentile: 85 },
]

export default function CompetitiveInsights() {
  const [selectedMetric, setSelectedMetric] = useState(null)

  const overallPercentile = 85

  return (
    <div style={{ padding: 32, maxWidth: 1200, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, color: COLORS.text, margin: '0 0 8px' }}>
          Inteligencia Competitiva
        </h1>
        <p style={{ fontSize: 16, color: COLORS.muted, margin: 0 }}>
          Posicionamiento en la industria de salud - benchmarks FHE-ML
        </p>
      </div>

      {/* Overall rank + trend */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 16, marginBottom: 28 }}>
        <div style={{
          background: COLORS.primary, borderRadius: 12, padding: 28, color: '#fff',
        }}>
          <p style={{ fontSize: 14, opacity: 0.85, margin: '0 0 8px' }}>Posicion general</p>
          <p style={{ fontSize: 40, fontWeight: 700, margin: '0 0 4px' }}>Top 15%</p>
          <p style={{ fontSize: 14, opacity: 0.85, margin: 0 }}>en tu industria (salud)</p>
        </div>
        <div style={{
          background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 28,
        }}>
          <p style={{ fontSize: 14, color: COLORS.muted, margin: '0 0 8px' }}>Percentil actual</p>
          <p style={{ fontSize: 40, fontWeight: 700, color: COLORS.accent, margin: '0 0 4px' }}>{overallPercentile}</p>
          <p style={{ fontSize: 14, color: COLORS.success, margin: 0 }}>
            {'\u25B2'} +3 puntos vs mes anterior
          </p>
        </div>
        <div style={{
          background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 28,
        }}>
          <p style={{ fontSize: 14, color: COLORS.muted, margin: '0 0 8px' }}>Evolucion trimestral</p>
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: 12, marginTop: 12 }}>
            {HISTORY.map(h => (
              <div key={h.month} style={{ textAlign: 'center', flex: 1 }}>
                <div style={{
                  height: h.percentile * 0.6, background: COLORS.primary, borderRadius: '4px 4px 0 0',
                  minHeight: 20, transition: 'height 0.3s',
                }} />
                <p style={{ fontSize: 11, color: COLORS.muted, margin: '6px 0 0' }}>{h.month.split(' ')[0]}</p>
                <p style={{ fontSize: 12, fontWeight: 600, color: COLORS.text, margin: 0 }}>p{h.percentile}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Benchmark comparison */}
      <div style={{
        background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`,
        padding: 24, marginBottom: 24,
      }}>
        <h3 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: '0 0 24px' }}>
          Comparacion con la Industria
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {BENCHMARKS.map((b, idx) => {
            const maxVal = Math.max(b.company, b.p90) * 1.1
            const companyPct = (b.company / maxVal) * 100
            const p25Pct = (b.p25 / maxVal) * 100
            const p50Pct = (b.p50 / maxVal) * 100
            const p75Pct = (b.p75 / maxVal) * 100
            const p90Pct = (b.p90 / maxVal) * 100
            const isSelected = selectedMetric === idx

            return (
              <div
                key={b.metric}
                onClick={() => setSelectedMetric(isSelected ? null : idx)}
                style={{ cursor: 'pointer' }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span style={{ fontSize: 14, fontWeight: 500, color: COLORS.text }}>{b.metric}</span>
                  <span style={{ fontSize: 14, fontWeight: 700, color: COLORS.primary }}>
                    {b.company} {b.unit}
                  </span>
                </div>
                {/* Bar background with percentile markers */}
                <div style={{ position: 'relative', width: '100%', height: 16, background: COLORS.bg, borderRadius: 8 }}>
                  {/* Percentile range band (p25 to p75) */}
                  <div style={{
                    position: 'absolute', top: 2, height: 12, borderRadius: 6,
                    left: `${p25Pct}%`, width: `${p75Pct - p25Pct}%`,
                    background: '#e2e8f0',
                  }} />
                  {/* P50 marker */}
                  <div style={{
                    position: 'absolute', top: 0, height: 16, width: 2,
                    background: COLORS.muted, left: `${p50Pct}%`,
                  }} />
                  {/* P90 marker */}
                  <div style={{
                    position: 'absolute', top: 0, height: 16, width: 2,
                    background: COLORS.success, left: `${p90Pct}%`,
                  }} />
                  {/* Company marker */}
                  <div style={{
                    position: 'absolute', top: -2, height: 20, width: 20,
                    borderRadius: '50%', background: COLORS.primary, border: '3px solid #fff',
                    left: `${companyPct}%`, transform: 'translateX(-10px)',
                    boxShadow: '0 2px 4px rgba(0,0,0,0.15)',
                  }} />
                </div>
                {/* Legend (shown when selected) */}
                {isSelected && (
                  <div style={{ display: 'flex', gap: 16, marginTop: 8, flexWrap: 'wrap' }}>
                    {[
                      { label: 'P25', value: b.p25, color: COLORS.border },
                      { label: 'P50', value: b.p50, color: COLORS.muted },
                      { label: 'P75', value: b.p75, color: '#94a3b8' },
                      { label: 'P90', value: b.p90, color: COLORS.success },
                      { label: 'Tu empresa', value: b.company, color: COLORS.primary },
                    ].map(l => (
                      <span key={l.label} style={{ fontSize: 12, color: l.color, fontWeight: 500 }}>
                        {l.label}: {l.value} {b.unit}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Strengths / Weaknesses / Opportunities */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 16 }}>
        {/* Strengths */}
        <div style={{
          background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 24,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: COLORS.success }} />
            <h3 style={{ fontSize: 16, fontWeight: 600, color: COLORS.text, margin: 0 }}>Fortalezas</h3>
          </div>
          {STRENGTHS.map((item, i) => {
            const trend = TREND_ICONS[item.trend]
            return (
              <div key={i} style={{
                padding: '12px 0', borderBottom: i < STRENGTHS.length - 1 ? `1px solid ${COLORS.border}` : 'none',
                display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8,
              }}>
                <span style={{ fontSize: 14, color: COLORS.text }}>{item.text}</span>
                <span style={{ fontSize: 14, color: trend.color, flexShrink: 0 }} title={trend.label}>
                  {trend.symbol}
                </span>
              </div>
            )
          })}
        </div>

        {/* Weaknesses */}
        <div style={{
          background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 24,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: COLORS.danger }} />
            <h3 style={{ fontSize: 16, fontWeight: 600, color: COLORS.text, margin: 0 }}>Debilidades</h3>
          </div>
          {WEAKNESSES.map((item, i) => {
            const trend = TREND_ICONS[item.trend]
            return (
              <div key={i} style={{
                padding: '12px 0', borderBottom: i < WEAKNESSES.length - 1 ? `1px solid ${COLORS.border}` : 'none',
                display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8,
              }}>
                <span style={{ fontSize: 14, color: COLORS.text }}>{item.text}</span>
                <span style={{ fontSize: 14, color: trend.color, flexShrink: 0 }} title={trend.label}>
                  {trend.symbol}
                </span>
              </div>
            )
          })}
        </div>

        {/* Opportunities */}
        <div style={{
          background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 24,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: COLORS.primary }} />
            <h3 style={{ fontSize: 16, fontWeight: 600, color: COLORS.text, margin: 0 }}>Oportunidades</h3>
          </div>
          {OPPORTUNITIES.map((item, i) => {
            const trend = TREND_ICONS[item.trend]
            return (
              <div key={i} style={{
                padding: '12px 0', borderBottom: i < OPPORTUNITIES.length - 1 ? `1px solid ${COLORS.border}` : 'none',
                display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8,
              }}>
                <span style={{ fontSize: 14, color: COLORS.text }}>{item.text}</span>
                <span style={{ fontSize: 14, color: trend.color, flexShrink: 0 }} title={trend.label}>
                  {trend.symbol}
                </span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
