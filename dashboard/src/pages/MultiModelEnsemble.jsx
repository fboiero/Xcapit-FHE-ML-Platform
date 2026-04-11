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

const TYPE_COLORS = {
  bagging: { bg: '#eff6ff', color: '#3b82f6' },
  boosting: { bg: '#fdf4ff', color: '#a855f7' },
  stacking: { bg: '#f0fdf4', color: '#22c55e' },
  voting: { bg: '#fff7ed', color: '#f97316' },
}

const ENSEMBLES = [
  {
    id: 1,
    name: 'Predictor de Costos Hospitalarios',
    type: 'boosting',
    accuracy: 94.2,
    status: 'activo',
    models: [
      { id: 'm1', name: 'CKKS Linear Regression', weight: 0.35, accuracy: 89.1, active: true },
      { id: 'm2', name: 'FHE Gradient Boost', weight: 0.30, accuracy: 91.7, active: true },
      { id: 'm3', name: 'Encrypted Random Forest', weight: 0.20, accuracy: 87.3, active: true },
      { id: 'm4', name: 'HE Neural Net v2', weight: 0.15, accuracy: 85.9, active: false },
    ],
  },
  {
    id: 2,
    name: 'Clasificador de Riesgo Crediticio',
    type: 'stacking',
    accuracy: 91.8,
    status: 'activo',
    models: [
      { id: 'm5', name: 'Logistic Regression FHE', weight: 0.40, accuracy: 88.4, active: true },
      { id: 'm6', name: 'SVM Encriptado', weight: 0.35, accuracy: 86.2, active: true },
      { id: 'm7', name: 'Decision Tree CKKS', weight: 0.25, accuracy: 84.1, active: true },
    ],
  },
  {
    id: 3,
    name: 'Detector de Fraudes Financieros',
    type: 'voting',
    accuracy: 96.5,
    status: 'entrenando',
    models: [
      { id: 'm8', name: 'Anomaly Detector v3', weight: 0.25, accuracy: 93.8, active: true },
      { id: 'm9', name: 'Pattern Classifier FHE', weight: 0.25, accuracy: 92.1, active: true },
      { id: 'm10', name: 'Sequence Analyzer', weight: 0.20, accuracy: 90.5, active: true },
      { id: 'm11', name: 'Graph Neural Net', weight: 0.15, accuracy: 89.3, active: true },
      { id: 'm12', name: 'Rule Engine CKKS', weight: 0.15, accuracy: 88.0, active: false },
    ],
  },
]

const STATUS_STYLES = {
  activo: { bg: COLORS.successLight, color: COLORS.success, label: 'Activo' },
  entrenando: { bg: COLORS.warningLight, color: COLORS.warning, label: 'Entrenando' },
  inactivo: { bg: COLORS.dangerLight, color: COLORS.danger, label: 'Inactivo' },
}

export default function MultiModelEnsemble() {
  const [selectedId, setSelectedId] = useState(1)
  const [modelWeights, setModelWeights] = useState({})
  const [modelActive, setModelActive] = useState({})
  const [showCreate, setShowCreate] = useState(false)
  const [newName, setNewName] = useState('')
  const [newType, setNewType] = useState('boosting')

  const selected = ENSEMBLES.find(e => e.id === selectedId)
  const bestIndividual = selected
    ? Math.max(...selected.models.map(m => m.accuracy))
    : 0

  const getWeight = (modelId, defaultW) => modelWeights[modelId] ?? defaultW
  const getActive = (modelId, defaultA) => modelActive[modelId] ?? defaultA

  return (
    <div style={{ padding: 32, maxWidth: 1200, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 32, flexWrap: 'wrap', gap: 16 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 700, color: COLORS.text, margin: '0 0 8px' }}>
            Ensemble de Modelos
          </h1>
          <p style={{ fontSize: 16, color: COLORS.muted, margin: 0 }}>
            Combina multiples modelos FHE para maximizar la precision
          </p>
        </div>
        <button
          onClick={() => setShowCreate(!showCreate)}
          style={{
            padding: '10px 20px', borderRadius: 8, border: 'none',
            background: COLORS.primary, color: '#fff', fontSize: 14,
            fontWeight: 600, cursor: 'pointer',
          }}
        >
          Crear Ensemble
        </button>
      </div>

      {/* Create form */}
      {showCreate && (
        <div style={{
          background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`,
          padding: 24, marginBottom: 24,
        }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, color: COLORS.text, margin: '0 0 16px' }}>
            Nuevo Ensemble
          </h3>
          <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', alignItems: 'flex-end' }}>
            <div style={{ flex: 1, minWidth: 200 }}>
              <label style={{ fontSize: 13, color: COLORS.muted, display: 'block', marginBottom: 6 }}>Nombre</label>
              <input
                value={newName}
                onChange={e => setNewName(e.target.value)}
                placeholder="Nombre del ensemble"
                style={{
                  width: '100%', padding: '10px 14px', borderRadius: 8,
                  border: `1px solid ${COLORS.border}`, fontSize: 14, color: COLORS.text,
                  outline: 'none', boxSizing: 'border-box',
                }}
              />
            </div>
            <div style={{ minWidth: 180 }}>
              <label style={{ fontSize: 13, color: COLORS.muted, display: 'block', marginBottom: 6 }}>Tipo</label>
              <select
                value={newType}
                onChange={e => setNewType(e.target.value)}
                style={{
                  width: '100%', padding: '10px 14px', borderRadius: 8,
                  border: `1px solid ${COLORS.border}`, fontSize: 14, color: COLORS.text,
                  outline: 'none', background: COLORS.card,
                }}
              >
                <option value="bagging">Bagging</option>
                <option value="boosting">Boosting</option>
                <option value="stacking">Stacking</option>
                <option value="voting">Voting</option>
              </select>
            </div>
            <button style={{
              padding: '10px 20px', borderRadius: 8, border: 'none',
              background: COLORS.accent, color: '#fff', fontSize: 14,
              fontWeight: 600, cursor: 'pointer',
            }}>
              Guardar
            </button>
          </div>
        </div>
      )}

      {/* Stats row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16, marginBottom: 28 }}>
        {[
          { label: 'Total ensembles', value: ENSEMBLES.length, color: COLORS.primary },
          { label: 'Modelos combinados', value: ENSEMBLES.reduce((s, e) => s + e.models.length, 0), color: COLORS.accent },
          { label: 'Precision promedio', value: `${(ENSEMBLES.reduce((s, e) => s + e.accuracy, 0) / ENSEMBLES.length).toFixed(1)}%`, color: COLORS.success },
          { label: 'Entrenando', value: ENSEMBLES.filter(e => e.status === 'entrenando').length, color: COLORS.warning },
        ].map(s => (
          <div key={s.label} style={{
            background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 20,
          }}>
            <p style={{ fontSize: 13, color: COLORS.muted, margin: '0 0 4px' }}>{s.label}</p>
            <p style={{ fontSize: 28, fontWeight: 700, color: s.color, margin: 0 }}>{s.value}</p>
          </div>
        ))}
      </div>

      {/* Ensemble cards */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 28 }}>
        {ENSEMBLES.map(ensemble => {
          const typeStyle = TYPE_COLORS[ensemble.type]
          const statusStyle = STATUS_STYLES[ensemble.status]
          const isSelected = selectedId === ensemble.id

          return (
            <div
              key={ensemble.id}
              onClick={() => setSelectedId(ensemble.id)}
              style={{
                background: COLORS.card, borderRadius: 12,
                border: `2px solid ${isSelected ? COLORS.primary : COLORS.border}`,
                padding: '20px 24px', cursor: 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                flexWrap: 'wrap', gap: 12,
              }}
            >
              <div style={{ flex: 1, minWidth: 200 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8, flexWrap: 'wrap' }}>
                  <span style={{
                    padding: '3px 10px', borderRadius: 6, fontSize: 12, fontWeight: 600,
                    background: typeStyle.bg, color: typeStyle.color, textTransform: 'capitalize',
                  }}>
                    {ensemble.type}
                  </span>
                  <span style={{
                    padding: '3px 10px', borderRadius: 6, fontSize: 12, fontWeight: 600,
                    background: statusStyle.bg, color: statusStyle.color,
                  }}>
                    {statusStyle.label}
                  </span>
                </div>
                <h3 style={{ fontSize: 16, fontWeight: 600, color: COLORS.text, margin: 0 }}>
                  {ensemble.name}
                </h3>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 24, flexShrink: 0 }}>
                <div style={{ textAlign: 'center' }}>
                  <p style={{ fontSize: 20, fontWeight: 700, color: COLORS.success, margin: 0 }}>{ensemble.accuracy}%</p>
                  <p style={{ fontSize: 11, color: COLORS.muted, margin: '2px 0 0' }}>Precision</p>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <p style={{ fontSize: 20, fontWeight: 700, color: COLORS.primary, margin: 0 }}>{ensemble.models.length}</p>
                  <p style={{ fontSize: 11, color: COLORS.muted, margin: '2px 0 0' }}>Modelos</p>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Selected ensemble detail */}
      {selected && (
        <div style={{
          background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`,
          padding: 24, marginBottom: 24,
        }}>
          <h3 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: '0 0 20px' }}>
            Modelos constituyentes - {selected.name}
          </h3>

          {/* Table header */}
          <div style={{
            display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 80px',
            gap: 12, padding: '10px 16px', background: COLORS.bg, borderRadius: 8,
            fontSize: 12, fontWeight: 600, color: COLORS.muted, textTransform: 'uppercase',
            marginBottom: 8,
          }}>
            <span>Modelo</span>
            <span>Peso</span>
            <span>Precision</span>
            <span>Activo</span>
          </div>

          {/* Table rows */}
          {selected.models.map(model => (
            <div key={model.id} style={{
              display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 80px',
              gap: 12, padding: '14px 16px', alignItems: 'center',
              borderBottom: `1px solid ${COLORS.border}`,
            }}>
              <span style={{ fontSize: 14, fontWeight: 500, color: COLORS.text }}>{model.name}</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <input
                  type="range"
                  min="0" max="100"
                  value={Math.round(getWeight(model.id, model.weight) * 100)}
                  onChange={e => setModelWeights(prev => ({ ...prev, [model.id]: e.target.value / 100 }))}
                  style={{ width: 80, cursor: 'pointer' }}
                />
                <span style={{ fontSize: 13, color: COLORS.muted, minWidth: 36 }}>
                  {Math.round(getWeight(model.id, model.weight) * 100)}%
                </span>
              </div>
              <span style={{ fontSize: 14, fontWeight: 600, color: COLORS.success }}>{model.accuracy}%</span>
              <button
                onClick={() => setModelActive(prev => ({ ...prev, [model.id]: !getActive(model.id, model.active) }))}
                style={{
                  width: 44, height: 24, borderRadius: 12, border: 'none', cursor: 'pointer',
                  background: getActive(model.id, model.active) ? COLORS.success : COLORS.border,
                  position: 'relative', transition: 'background 0.2s',
                }}
              >
                <div style={{
                  width: 18, height: 18, borderRadius: '50%', background: '#fff',
                  position: 'absolute', top: 3,
                  left: getActive(model.id, model.active) ? 23 : 3,
                  transition: 'left 0.2s',
                }} />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Performance comparison */}
      {selected && (
        <div style={{
          background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`,
          padding: 24,
        }}>
          <h3 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: '0 0 20px' }}>
            Comparacion de Rendimiento
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {/* Ensemble bar */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                <span style={{ fontSize: 14, fontWeight: 500, color: COLORS.text }}>Ensemble (combinado)</span>
                <span style={{ fontSize: 14, fontWeight: 700, color: COLORS.primary }}>{selected.accuracy}%</span>
              </div>
              <div style={{ width: '100%', height: 12, background: COLORS.bg, borderRadius: 6, overflow: 'hidden' }}>
                <div style={{ height: '100%', background: COLORS.primary, borderRadius: 6, width: `${selected.accuracy}%` }} />
              </div>
            </div>
            {/* Best individual bar */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                <span style={{ fontSize: 14, fontWeight: 500, color: COLORS.text }}>Mejor modelo individual</span>
                <span style={{ fontSize: 14, fontWeight: 700, color: COLORS.accent }}>{bestIndividual}%</span>
              </div>
              <div style={{ width: '100%', height: 12, background: COLORS.bg, borderRadius: 6, overflow: 'hidden' }}>
                <div style={{ height: '100%', background: COLORS.accent, borderRadius: 6, width: `${bestIndividual}%` }} />
              </div>
            </div>
            {/* Improvement */}
            <div style={{
              background: COLORS.primaryLight, borderRadius: 8, padding: '12px 20px',
              display: 'flex', alignItems: 'center', gap: 8,
            }}>
              <span style={{ fontSize: 18, color: COLORS.success }}>&#9650;</span>
              <span style={{ fontSize: 14, fontWeight: 600, color: COLORS.primary }}>
                +{(selected.accuracy - bestIndividual).toFixed(1)} puntos porcentuales de mejora con ensemble
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
