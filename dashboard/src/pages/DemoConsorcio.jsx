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

const TAB_LABELS = ['Configurar', 'Datos', 'Entrenar', 'Resultados']

const MOCK_CSV = [
  { id: 1, edad: 45, presion: 130, colesterol: 220, glucosa: 110, riesgo: 0.72 },
  { id: 2, edad: 32, presion: 118, colesterol: 185, glucosa: 92, riesgo: 0.31 },
  { id: 3, edad: 58, presion: 145, colesterol: 260, glucosa: 138, riesgo: 0.89 },
  { id: 4, edad: 41, presion: 125, colesterol: 198, glucosa: 105, riesgo: 0.55 },
  { id: 5, edad: 67, presion: 152, colesterol: 275, glucosa: 145, riesgo: 0.93 },
]

const MODEL_TYPES = [
  { value: 'linear_regression', label: 'Regresion Lineal' },
  { value: 'logistic_regression', label: 'Regresion Logistica' },
]

export default function DemoConsorcio() {
  const [activeTab, setActiveTab] = useState(0)
  const [consortiumName, setConsortiumName] = useState('Consorcio Salud Demo')
  const [modelType, setModelType] = useState('linear_regression')
  const [fileUploaded, setFileUploaded] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const [trainingProgress, setTrainingProgress] = useState(0)
  const [trainingStarted, setTrainingStarted] = useState(false)
  const [fheStatus, setFheStatus] = useState('idle')

  useEffect(() => {
    if (!trainingStarted) return
    setFheStatus('encrypting')
    const t1 = setTimeout(() => setFheStatus('training'), 1500)
    const interval = setInterval(() => {
      setTrainingProgress(prev => {
        if (prev >= 100) { clearInterval(interval); setFheStatus('complete'); return 100 }
        return prev + 2
      })
    }, 120)
    return () => { clearTimeout(t1); clearInterval(interval) }
  }, [trainingStarted])

  const results = {
    r2: 0.94, mae: 0.042, improvement: 18.3,
    localR2: 0.79, consortiumR2: 0.94,
    localMAE: 0.087, consortiumMAE: 0.042,
  }

  return (
    <div style={{ padding: 32, maxWidth: 1200, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, color: COLORS.text, margin: '0 0 8px' }}>
          Sandbox del Consorcio
        </h1>
        <p style={{ fontSize: 16, color: COLORS.muted, margin: 0 }}>
          Simula un flujo completo de entrenamiento federado con FHE
        </p>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 0, marginBottom: 24, borderBottom: `2px solid ${COLORS.border}` }}>
        {TAB_LABELS.map((label, i) => (
          <button key={label} onClick={() => setActiveTab(i)} style={{
            padding: '12px 24px', border: 'none', background: 'none', fontSize: 14,
            fontWeight: 600, cursor: 'pointer', position: 'relative',
            color: activeTab === i ? COLORS.primary : COLORS.muted,
            borderBottom: activeTab === i ? `2px solid ${COLORS.primary}` : '2px solid transparent',
            marginBottom: -2,
          }}>
            <span style={{
              display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
              width: 22, height: 22, borderRadius: '50%', fontSize: 12, fontWeight: 700, marginRight: 8,
              background: activeTab >= i ? COLORS.primary : COLORS.border,
              color: activeTab >= i ? '#fff' : COLORS.muted,
            }}>{i + 1}</span>
            {label}
          </button>
        ))}
      </div>

      {/* Tab 1: Configurar */}
      {activeTab === 0 && (
        <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 28 }}>
          <h3 style={{ fontSize: 17, fontWeight: 600, color: COLORS.text, margin: '0 0 20px' }}>Configuracion del consorcio</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
            <div>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: COLORS.text, marginBottom: 6 }}>Nombre del consorcio</label>
              <input value={consortiumName} onChange={e => setConsortiumName(e.target.value)} style={{
                width: '100%', padding: '10px 14px', borderRadius: 8, border: `1px solid ${COLORS.border}`,
                fontSize: 14, color: COLORS.text, outline: 'none', boxSizing: 'border-box',
              }} />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: COLORS.text, marginBottom: 6 }}>Tipo de modelo</label>
              <select value={modelType} onChange={e => setModelType(e.target.value)} style={{
                width: '100%', padding: '10px 14px', borderRadius: 8, border: `1px solid ${COLORS.border}`,
                fontSize: 14, color: COLORS.text, background: '#fff', outline: 'none', boxSizing: 'border-box',
              }}>
                {MODEL_TYPES.map(mt => <option key={mt.value} value={mt.value}>{mt.label}</option>)}
              </select>
            </div>
          </div>
          <div style={{
            marginTop: 20, padding: 16, background: COLORS.primaryLight, borderRadius: 10,
            display: 'flex', alignItems: 'center', gap: 12,
          }}>
            <svg width="20" height="20" fill="none" stroke={COLORS.primary} viewBox="0 0 24 24" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
            </svg>
            <span style={{ fontSize: 13, color: COLORS.primary }}>
              Seguridad FHE: CKKS 128-bit | Privacidad Diferencial: epsilon=1.0
            </span>
          </div>
          <button onClick={() => setActiveTab(1)} style={{
            marginTop: 20, padding: '10px 24px', borderRadius: 8, border: 'none',
            background: COLORS.primary, color: '#fff', fontSize: 14, fontWeight: 600, cursor: 'pointer',
          }}>Siguiente</button>
        </div>
      )}

      {/* Tab 2: Datos */}
      {activeTab === 1 && (
        <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 28 }}>
          <h3 style={{ fontSize: 17, fontWeight: 600, color: COLORS.text, margin: '0 0 20px' }}>Datos del consorcio</h3>
          {!fileUploaded ? (
            <div
              onDragOver={e => { e.preventDefault(); setDragOver(true) }}
              onDragLeave={() => setDragOver(false)}
              onDrop={e => { e.preventDefault(); setDragOver(false); setFileUploaded(true) }}
              onClick={() => setFileUploaded(true)}
              style={{
                border: `2px dashed ${dragOver ? COLORS.primary : COLORS.border}`, borderRadius: 12,
                padding: '48px 20px', textAlign: 'center', cursor: 'pointer',
                background: dragOver ? COLORS.primaryLight : COLORS.bg, transition: 'all 0.2s',
              }}
            >
              <svg width="48" height="48" fill="none" stroke={COLORS.muted} viewBox="0 0 24 24" strokeWidth={1.5} style={{ margin: '0 auto 12px', display: 'block' }}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
              </svg>
              <p style={{ fontSize: 15, fontWeight: 600, color: COLORS.text, margin: '0 0 4px' }}>Arrastra tu archivo CSV aqui</p>
              <p style={{ fontSize: 13, color: COLORS.muted, margin: 0 }}>o haz click para seleccionar</p>
            </div>
          ) : (
            <>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16, padding: '10px 16px', background: COLORS.successLight, borderRadius: 8 }}>
                <svg width="18" height="18" fill="none" stroke={COLORS.success} viewBox="0 0 24 24" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                </svg>
                <span style={{ fontSize: 14, fontWeight: 600, color: COLORS.success }}>healthcare_data_demo.csv cargado (500 registros, 6 features)</span>
              </div>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                  <thead>
                    <tr style={{ borderBottom: `2px solid ${COLORS.border}` }}>
                      {['ID', 'Edad', 'Presion', 'Colesterol', 'Glucosa', 'Riesgo'].map(h => (
                        <th key={h} style={{ textAlign: 'left', padding: '8px 12px', fontWeight: 600, color: COLORS.muted, textTransform: 'uppercase', fontSize: 11, letterSpacing: 0.5 }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {MOCK_CSV.map(row => (
                      <tr key={row.id} style={{ borderBottom: `1px solid ${COLORS.border}` }}>
                        <td style={{ padding: '8px 12px', color: COLORS.muted }}>{row.id}</td>
                        <td style={{ padding: '8px 12px', color: COLORS.text }}>{row.edad}</td>
                        <td style={{ padding: '8px 12px', color: COLORS.text }}>{row.presion}</td>
                        <td style={{ padding: '8px 12px', color: COLORS.text }}>{row.colesterol}</td>
                        <td style={{ padding: '8px 12px', color: COLORS.text }}>{row.glucosa}</td>
                        <td style={{ padding: '8px 12px', fontWeight: 600, color: row.riesgo > 0.7 ? COLORS.danger : row.riesgo > 0.5 ? COLORS.warning : COLORS.success }}>{row.riesgo}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
          <div style={{ display: 'flex', gap: 10, marginTop: 20 }}>
            <button onClick={() => setActiveTab(0)} style={{ padding: '10px 20px', borderRadius: 8, border: `1px solid ${COLORS.border}`, background: '#fff', color: COLORS.text, fontSize: 14, fontWeight: 600, cursor: 'pointer' }}>Atras</button>
            <button onClick={() => { setFileUploaded(true); setActiveTab(2) }} style={{ padding: '10px 24px', borderRadius: 8, border: 'none', background: COLORS.primary, color: '#fff', fontSize: 14, fontWeight: 600, cursor: 'pointer' }}>Siguiente</button>
          </div>
        </div>
      )}

      {/* Tab 3: Entrenar */}
      {activeTab === 2 && (
        <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 28 }}>
          <h3 style={{ fontSize: 17, fontWeight: 600, color: COLORS.text, margin: '0 0 20px' }}>Entrenamiento FHE</h3>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
            <span style={{ fontSize: 13, fontWeight: 600, color: COLORS.text }}>Estado FHE:</span>
            <span style={{
              padding: '4px 12px', borderRadius: 6, fontSize: 12, fontWeight: 600,
              background: fheStatus === 'complete' ? COLORS.successLight : fheStatus === 'training' ? COLORS.warningLight : fheStatus === 'encrypting' ? COLORS.primaryLight : COLORS.bg,
              color: fheStatus === 'complete' ? COLORS.success : fheStatus === 'training' ? COLORS.warning : fheStatus === 'encrypting' ? COLORS.primary : COLORS.muted,
            }}>
              {fheStatus === 'idle' ? 'Esperando' : fheStatus === 'encrypting' ? 'Cifrando datos...' : fheStatus === 'training' ? 'Entrenando sobre cifrado' : 'Completado'}
            </span>
          </div>
          <div style={{ marginBottom: 20 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
              <span style={{ fontSize: 13, color: COLORS.text, fontWeight: 500 }}>Progreso del entrenamiento</span>
              <span style={{ fontSize: 13, fontWeight: 700, color: COLORS.primary }}>{trainingProgress}%</span>
            </div>
            <div style={{ width: '100%', height: 12, background: COLORS.bg, borderRadius: 6, overflow: 'hidden' }}>
              <div style={{ height: '100%', background: `linear-gradient(90deg, ${COLORS.primary}, ${COLORS.accent})`, width: `${trainingProgress}%`, borderRadius: 6, transition: 'width 0.3s' }} />
            </div>
          </div>
          {!trainingStarted ? (
            <button onClick={() => setTrainingStarted(true)} style={{ padding: '10px 24px', borderRadius: 8, border: 'none', background: COLORS.primary, color: '#fff', fontSize: 14, fontWeight: 600, cursor: 'pointer' }}>
              Iniciar entrenamiento
            </button>
          ) : trainingProgress >= 100 ? (
            <button onClick={() => setActiveTab(3)} style={{ padding: '10px 24px', borderRadius: 8, border: 'none', background: COLORS.success, color: '#fff', fontSize: 14, fontWeight: 600, cursor: 'pointer' }}>
              Ver resultados
            </button>
          ) : null}
        </div>
      )}

      {/* Tab 4: Resultados */}
      {activeTab === 3 && (
        <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 28 }}>
          <h3 style={{ fontSize: 17, fontWeight: 600, color: COLORS.text, margin: '0 0 20px' }}>Resultados del modelo</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 16, marginBottom: 24 }}>
            {[
              { label: 'R² Score', value: results.r2.toFixed(2), color: COLORS.primary },
              { label: 'MAE', value: results.mae.toFixed(3), color: COLORS.accent },
              { label: 'Mejora vs Local', value: `+${results.improvement}%`, color: COLORS.success },
            ].map(m => (
              <div key={m.label} style={{ background: COLORS.bg, borderRadius: 10, padding: 20, textAlign: 'center' }}>
                <p style={{ fontSize: 28, fontWeight: 800, color: m.color, margin: '0 0 4px' }}>{m.value}</p>
                <p style={{ fontSize: 13, color: COLORS.muted, margin: 0 }}>{m.label}</p>
              </div>
            ))}
          </div>
          <h4 style={{ fontSize: 15, fontWeight: 600, color: COLORS.text, margin: '0 0 12px' }}>Comparacion: Local vs Consorcio</h4>
          {[
            { label: 'R² Score', local: results.localR2, consortium: results.consortiumR2 },
            { label: 'MAE (menor es mejor)', local: results.localMAE, consortium: results.consortiumMAE },
          ].map(cmp => (
            <div key={cmp.label} style={{ marginBottom: 16 }}>
              <p style={{ fontSize: 13, fontWeight: 500, color: COLORS.text, margin: '0 0 8px' }}>{cmp.label}</p>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 4 }}>
                <span style={{ fontSize: 12, color: COLORS.muted, width: 80 }}>Local</span>
                <div style={{ flex: 1, height: 20, background: COLORS.bg, borderRadius: 4, overflow: 'hidden' }}>
                  <div style={{ height: '100%', background: COLORS.warning, width: `${cmp.local * 100}%`, borderRadius: 4 }} />
                </div>
                <span style={{ fontSize: 13, fontWeight: 600, color: COLORS.text, width: 50, textAlign: 'right' }}>{cmp.local}</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <span style={{ fontSize: 12, color: COLORS.muted, width: 80 }}>Consorcio</span>
                <div style={{ flex: 1, height: 20, background: COLORS.bg, borderRadius: 4, overflow: 'hidden' }}>
                  <div style={{ height: '100%', background: COLORS.primary, width: `${cmp.consortium * 100}%`, borderRadius: 4 }} />
                </div>
                <span style={{ fontSize: 13, fontWeight: 600, color: COLORS.text, width: 50, textAlign: 'right' }}>{cmp.consortium}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
