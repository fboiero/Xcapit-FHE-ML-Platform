import { useState, useEffect } from 'react'

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

const MODEL_TYPES = [
  { value: 'linear_regression', label: 'Regresion Lineal' },
  { value: 'logistic_regression', label: 'Regresion Logistica' },
  { value: 'neural_network', label: 'Red Neuronal (MLP)' },
  { value: 'random_forest', label: 'Random Forest' },
]

const SECURITY_LEVELS = [
  { value: 128, label: '128-bit', desc: 'Estandar — rapido' },
  { value: 192, label: '192-bit', desc: 'Alto — balanceado' },
  { value: 256, label: '256-bit', desc: 'Maximo — lento' },
]

const ALL_FEATURES = ['edad', 'presion_arterial', 'colesterol', 'glucosa', 'imc', 'frecuencia_cardiaca', 'tabaquismo', 'actividad_fisica', 'historial_familiar', 'genero']

export default function ModelBuilder() {
  const [modelName, setModelName] = useState('modelo_salud_v1')
  const [modelType, setModelType] = useState('linear_regression')
  const [securityLevel, setSecurityLevel] = useState(128)
  const [selectedFeatures, setSelectedFeatures] = useState(['edad', 'presion_arterial', 'colesterol', 'glucosa', 'imc'])
  const [epochs, setEpochs] = useState(50)
  const [learningRate, setLearningRate] = useState(0.01)
  const [batchSize, setBatchSize] = useState(32)
  const [training, setTraining] = useState(false)
  const [progress, setProgress] = useState(0)
  const [done, setDone] = useState(false)

  const toggleFeature = (f) => {
    setSelectedFeatures(prev => prev.includes(f) ? prev.filter(x => x !== f) : [...prev, f])
  }

  useEffect(() => {
    if (!training) return
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) { clearInterval(interval); setTraining(false); setDone(true); return 100 }
        return prev + 3
      })
    }, 150)
    return () => clearInterval(interval)
  }, [training])

  const handleTrain = () => { setTraining(true); setProgress(0); setDone(false) }

  return (
    <div style={{ padding: 32, maxWidth: 1200, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, color: COLORS.text, margin: '0 0 8px' }}>
          Constructor de Modelos
        </h1>
        <p style={{ fontSize: 16, color: COLORS.muted, margin: 0 }}>
          Configura y entrena modelos de ML con encriptacion homomorfica
        </p>
      </div>

      {/* Two-column layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 24 }}>
        {/* Left: Config form */}
        <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 24 }}>
          <h2 style={{ fontSize: 17, fontWeight: 600, color: COLORS.text, margin: '0 0 20px' }}>Configuracion</h2>

          <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: COLORS.text, marginBottom: 6 }}>Nombre del modelo</label>
          <input value={modelName} onChange={e => setModelName(e.target.value)} style={{
            width: '100%', padding: '10px 14px', borderRadius: 8, border: `1px solid ${COLORS.border}`,
            fontSize: 14, color: COLORS.text, outline: 'none', marginBottom: 16, boxSizing: 'border-box',
          }} />

          <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: COLORS.text, marginBottom: 6 }}>Tipo de modelo</label>
          <select value={modelType} onChange={e => setModelType(e.target.value)} style={{
            width: '100%', padding: '10px 14px', borderRadius: 8, border: `1px solid ${COLORS.border}`,
            fontSize: 14, color: COLORS.text, background: '#fff', outline: 'none', marginBottom: 16, boxSizing: 'border-box',
          }}>
            {MODEL_TYPES.map(mt => <option key={mt.value} value={mt.value}>{mt.label}</option>)}
          </select>

          <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: COLORS.text, marginBottom: 6 }}>Nivel de seguridad FHE</label>
          <div style={{ display: 'flex', gap: 10, marginBottom: 16 }}>
            {SECURITY_LEVELS.map(sl => (
              <button key={sl.value} onClick={() => setSecurityLevel(sl.value)} style={{
                flex: 1, padding: '10px 8px', borderRadius: 8, border: `2px solid ${securityLevel === sl.value ? COLORS.primary : COLORS.border}`,
                background: securityLevel === sl.value ? COLORS.primaryLight : '#fff',
                color: securityLevel === sl.value ? COLORS.primary : COLORS.text,
                fontSize: 13, fontWeight: 600, cursor: 'pointer', textAlign: 'center',
              }}>
                {sl.label}
                <div style={{ fontSize: 11, fontWeight: 400, color: COLORS.muted, marginTop: 2 }}>{sl.desc}</div>
              </button>
            ))}
          </div>

          <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: COLORS.text, marginBottom: 6 }}>Features ({selectedFeatures.length} seleccionadas)</label>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {ALL_FEATURES.map(f => (
              <button key={f} onClick={() => toggleFeature(f)} style={{
                padding: '6px 12px', borderRadius: 6, border: `1px solid ${selectedFeatures.includes(f) ? COLORS.primary : COLORS.border}`,
                background: selectedFeatures.includes(f) ? COLORS.primaryLight : '#fff',
                color: selectedFeatures.includes(f) ? COLORS.primary : COLORS.muted,
                fontSize: 12, fontWeight: 500, cursor: 'pointer',
              }}>
                {f}
              </button>
            ))}
          </div>
        </div>

        {/* Right: Architecture preview */}
        <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 24 }}>
          <h2 style={{ fontSize: 17, fontWeight: 600, color: COLORS.text, margin: '0 0 20px' }}>Vista previa de arquitectura</h2>
          <div style={{ background: COLORS.bg, borderRadius: 10, padding: 20, marginBottom: 16 }}>
            {[
              { label: 'Modelo', value: MODEL_TYPES.find(m => m.value === modelType)?.label },
              { label: 'Nombre', value: modelName },
              { label: 'Seguridad FHE', value: `CKKS ${securityLevel}-bit` },
              { label: 'Features', value: `${selectedFeatures.length} de ${ALL_FEATURES.length}` },
              { label: 'Epochs', value: epochs },
              { label: 'Learning Rate', value: learningRate },
              { label: 'Batch Size', value: batchSize },
            ].map(row => (
              <div key={row.label} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: `1px solid ${COLORS.border}` }}>
                <span style={{ fontSize: 13, color: COLORS.muted }}>{row.label}</span>
                <span style={{ fontSize: 13, fontWeight: 600, color: COLORS.text }}>{row.value}</span>
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {['Input Layer', modelType === 'neural_network' ? 'Hidden Layer (64)' : null, modelType === 'neural_network' ? 'Hidden Layer (32)' : null, 'FHE Encryption Layer', 'Output Layer'].filter(Boolean).map((layer, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{
                  flex: 1, padding: '10px 16px', borderRadius: 8,
                  background: layer.includes('FHE') ? COLORS.primaryLight : COLORS.bg,
                  border: `1px solid ${layer.includes('FHE') ? COLORS.primary : COLORS.border}`,
                  fontSize: 13, fontWeight: layer.includes('FHE') ? 600 : 500,
                  color: layer.includes('FHE') ? COLORS.primary : COLORS.text, textAlign: 'center',
                }}>
                  {layer}{layer === 'Input Layer' ? ` (${selectedFeatures.length})` : layer === 'Output Layer' ? ' (1)' : ''}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Training config */}
      <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 24, marginBottom: 24 }}>
        <h2 style={{ fontSize: 17, fontWeight: 600, color: COLORS.text, margin: '0 0 20px' }}>Configuracion de entrenamiento</h2>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 24 }}>
          {[
            { label: 'Epochs', value: epochs, set: setEpochs, min: 10, max: 200, step: 10 },
            { label: 'Learning Rate', value: learningRate, set: setLearningRate, min: 0.001, max: 0.1, step: 0.001 },
            { label: 'Batch Size', value: batchSize, set: setBatchSize, min: 8, max: 128, step: 8 },
          ].map(s => (
            <div key={s.label}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                <span style={{ fontSize: 13, fontWeight: 600, color: COLORS.text }}>{s.label}</span>
                <span style={{ fontSize: 13, fontWeight: 700, color: COLORS.primary }}>{s.value}</span>
              </div>
              <input type="range" min={s.min} max={s.max} step={s.step} value={s.value}
                onChange={e => s.set(Number(e.target.value))}
                style={{ width: '100%', accentColor: COLORS.primary }} />
            </div>
          ))}
        </div>
        <div style={{ marginTop: 20, display: 'flex', alignItems: 'center', gap: 16 }}>
          <button onClick={handleTrain} disabled={training || selectedFeatures.length === 0} style={{
            padding: '12px 28px', borderRadius: 8, border: 'none',
            background: training ? COLORS.muted : COLORS.primary, color: '#fff',
            fontSize: 15, fontWeight: 600, cursor: training ? 'default' : 'pointer',
          }}>
            {training ? 'Entrenando...' : 'Entrenar Modelo'}
          </button>
          {training && (
            <div style={{ flex: 1 }}>
              <div style={{ width: '100%', height: 8, background: COLORS.bg, borderRadius: 4, overflow: 'hidden' }}>
                <div style={{ height: '100%', background: COLORS.primary, width: `${progress}%`, transition: 'width 0.2s', borderRadius: 4 }} />
              </div>
              <span style={{ fontSize: 12, color: COLORS.muted, marginTop: 4, display: 'block' }}>{progress}% completado</span>
            </div>
          )}
        </div>
      </div>

      {/* Results */}
      {done && (
        <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
            <svg width="20" height="20" fill="none" stroke={COLORS.success} viewBox="0 0 24 24" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h2 style={{ fontSize: 17, fontWeight: 600, color: COLORS.text, margin: 0 }}>Resultados del entrenamiento</h2>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16 }}>
            {[
              { label: 'R² Score', value: '0.94', color: COLORS.primary },
              { label: 'MAE', value: '0.042', color: COLORS.accent },
              { label: 'RMSE', value: '0.058', color: COLORS.warning },
              { label: 'Tiempo', value: '12.4s', color: '#8b5cf6' },
              { label: 'Tamanio modelo', value: '2.8 MB', color: COLORS.muted },
            ].map(m => (
              <div key={m.label} style={{ background: COLORS.bg, borderRadius: 10, padding: 20, textAlign: 'center' }}>
                <p style={{ fontSize: 24, fontWeight: 800, color: m.color, margin: '0 0 4px' }}>{m.value}</p>
                <p style={{ fontSize: 12, color: COLORS.muted, margin: 0 }}>{m.label}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
