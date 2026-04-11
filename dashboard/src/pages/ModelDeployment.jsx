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

const DEPLOYMENTS = [
  { id: 1, name: 'Modelo Riesgo Salud v2', version: 'v2.1.0', endpoint: 'https://api.xcapit.io/v2/predict/health-risk', status: 'running', latency: '45ms', rpm: 1240, uptime: '99.97%' },
  { id: 2, name: 'Modelo Fraude Financiero', version: 'v1.3.2', endpoint: 'https://api.xcapit.io/v2/predict/fraud-detect', status: 'running', latency: '62ms', rpm: 890, uptime: '99.95%' },
  { id: 3, name: 'Modelo Churn Prediccion', version: 'v1.0.0', endpoint: 'https://api.xcapit.io/v2/predict/churn', status: 'scaling', latency: '128ms', rpm: 2100, uptime: '99.89%' },
  { id: 4, name: 'Modelo Segmentacion Beta', version: 'v0.9.1', endpoint: 'https://api.xcapit.io/v2/predict/segment-beta', status: 'stopped', latency: '-', rpm: 0, uptime: '-' },
]

const STATUS_MAP = {
  running: { label: 'Activo', bg: COLORS.successLight, color: COLORS.success },
  scaling: { label: 'Escalando', bg: COLORS.warningLight, color: COLORS.warning },
  stopped: { label: 'Detenido', bg: COLORS.dangerLight, color: COLORS.danger },
}

const MOCK_LOGS = [
  { time: '14:32:01', level: 'INFO', msg: 'health-risk: 200 OK - 42ms' },
  { time: '14:32:03', level: 'INFO', msg: 'fraud-detect: 200 OK - 58ms' },
  { time: '14:32:05', level: 'WARN', msg: 'churn: latencia elevada 145ms (umbral: 100ms)' },
  { time: '14:32:06', level: 'INFO', msg: 'churn: auto-scaling activado (replicas: 2 -> 3)' },
  { time: '14:32:08', level: 'INFO', msg: 'health-risk: 200 OK - 39ms' },
  { time: '14:32:10', level: 'INFO', msg: 'fraud-detect: 200 OK - 61ms' },
  { time: '14:32:12', level: 'INFO', msg: 'churn: nueva replica lista (total: 3)' },
  { time: '14:32:14', level: 'INFO', msg: 'churn: 200 OK - 78ms (normalizado)' },
  { time: '14:32:16', level: 'ERROR', msg: 'segment-beta: servicio detenido por inactividad' },
  { time: '14:32:18', level: 'INFO', msg: 'health-risk: 200 OK - 44ms' },
]

const AVAILABLE_MODELS = [
  'Modelo Riesgo Salud v2',
  'Modelo Fraude Financiero',
  'Modelo Churn Prediccion',
  'Modelo Segmentacion Beta',
  'Modelo Consorcio FHE v1',
]

export default function ModelDeployment() {
  const [showModal, setShowModal] = useState(false)
  const [selectedModel, setSelectedModel] = useState(AVAILABLE_MODELS[0])
  const [replicas, setReplicas] = useState(2)
  const [cpuLimit, setCpuLimit] = useState('500m')

  return (
    <div style={{ padding: 32, maxWidth: 1200, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 28, flexWrap: 'wrap', gap: 16 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 700, color: COLORS.text, margin: '0 0 8px' }}>
            Despliegue de Modelos
          </h1>
          <p style={{ fontSize: 16, color: COLORS.muted, margin: 0 }}>
            Gestiona endpoints de inferencia en produccion
          </p>
        </div>
        <button onClick={() => setShowModal(true)} style={{
          padding: '10px 20px', borderRadius: 8, border: 'none',
          background: COLORS.primary, color: '#fff', fontSize: 14,
          fontWeight: 600, cursor: 'pointer',
        }}>
          Nuevo Despliegue
        </button>
      </div>

      {/* Stats row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16, marginBottom: 28 }}>
        {[
          { label: 'Activos', value: DEPLOYMENTS.filter(d => d.status === 'running').length, color: COLORS.success },
          { label: 'Escalando', value: DEPLOYMENTS.filter(d => d.status === 'scaling').length, color: COLORS.warning },
          { label: 'Detenidos', value: DEPLOYMENTS.filter(d => d.status === 'stopped').length, color: COLORS.danger },
          { label: 'Requests/min total', value: DEPLOYMENTS.reduce((s, d) => s + d.rpm, 0).toLocaleString(), color: COLORS.primary },
        ].map(s => (
          <div key={s.label} style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 20 }}>
            <p style={{ fontSize: 13, color: COLORS.muted, margin: '0 0 4px' }}>{s.label}</p>
            <p style={{ fontSize: 28, fontWeight: 700, color: s.color, margin: 0 }}>{s.value}</p>
          </div>
        ))}
      </div>

      {/* Deployment cards */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginBottom: 28 }}>
        {DEPLOYMENTS.map(dep => {
          const st = STATUS_MAP[dep.status]
          return (
            <div key={dep.id} style={{
              background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`,
              padding: 20, display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              flexWrap: 'wrap', gap: 16,
            }}>
              <div style={{ minWidth: 200 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                  <div style={{ width: 10, height: 10, borderRadius: '50%', background: st.color }} />
                  <h3 style={{ fontSize: 15, fontWeight: 600, color: COLORS.text, margin: 0 }}>{dep.name}</h3>
                  <span style={{
                    padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 600,
                    background: st.bg, color: st.color,
                  }}>{st.label}</span>
                </div>
                <p style={{ fontSize: 12, color: COLORS.muted, margin: '0 0 2px' }}>Version: {dep.version}</p>
                <p style={{ fontSize: 11, fontFamily: 'monospace', color: COLORS.muted, margin: 0, wordBreak: 'break-all' }}>{dep.endpoint}</p>
              </div>
              <div style={{ display: 'flex', gap: 20 }}>
                {[
                  { label: 'Latencia', value: dep.latency },
                  { label: 'Req/min', value: dep.rpm.toLocaleString() },
                  { label: 'Uptime', value: dep.uptime },
                ].map(m => (
                  <div key={m.label} style={{ textAlign: 'center', minWidth: 70 }}>
                    <p style={{ fontSize: 16, fontWeight: 700, color: COLORS.text, margin: '0 0 2px' }}>{m.value}</p>
                    <p style={{ fontSize: 11, color: COLORS.muted, margin: 0 }}>{m.label}</p>
                  </div>
                ))}
              </div>
            </div>
          )
        })}
      </div>

      {/* Logs */}
      <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 24 }}>
        <h2 style={{ fontSize: 17, fontWeight: 600, color: COLORS.text, margin: '0 0 16px' }}>Logs de despliegue</h2>
        <div style={{
          background: '#0f172a', borderRadius: 10, padding: 16, fontFamily: 'monospace',
          fontSize: 12, maxHeight: 260, overflowY: 'auto', lineHeight: 1.8,
        }}>
          {MOCK_LOGS.map((log, i) => (
            <div key={i} style={{
              color: log.level === 'ERROR' ? '#f87171'
                : log.level === 'WARN' ? '#fbbf24'
                : '#a5f3fc',
            }}>
              <span style={{ color: '#64748b' }}>[{log.time}]</span>{' '}
              <span style={{ fontWeight: 600 }}>{log.level}</span>{' '}
              {log.msg}
            </div>
          ))}
        </div>
      </div>

      {/* New deployment modal */}
      {showModal && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', display: 'flex',
          alignItems: 'center', justifyContent: 'center', zIndex: 1000,
        }} onClick={() => setShowModal(false)}>
          <div onClick={e => e.stopPropagation()} style={{
            background: COLORS.card, borderRadius: 16, padding: 28, width: 440,
            maxWidth: '90vw', boxShadow: '0 20px 60px rgba(0,0,0,0.15)',
          }}>
            <h2 style={{ fontSize: 20, fontWeight: 700, color: COLORS.text, margin: '0 0 20px' }}>Nuevo Despliegue</h2>

            <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: COLORS.text, marginBottom: 6 }}>Modelo</label>
            <select value={selectedModel} onChange={e => setSelectedModel(e.target.value)} style={{
              width: '100%', padding: '10px 14px', borderRadius: 8, border: `1px solid ${COLORS.border}`,
              fontSize: 14, color: COLORS.text, background: '#fff', outline: 'none', marginBottom: 16, boxSizing: 'border-box',
            }}>
              {AVAILABLE_MODELS.map(m => <option key={m} value={m}>{m}</option>)}
            </select>

            <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: COLORS.text, marginBottom: 6 }}>Replicas</label>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
              <input type="range" min={1} max={5} value={replicas} onChange={e => setReplicas(Number(e.target.value))}
                style={{ flex: 1, accentColor: COLORS.primary }} />
              <span style={{ fontSize: 14, fontWeight: 700, color: COLORS.primary, width: 24, textAlign: 'center' }}>{replicas}</span>
            </div>

            <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: COLORS.text, marginBottom: 6 }}>CPU Limit</label>
            <select value={cpuLimit} onChange={e => setCpuLimit(e.target.value)} style={{
              width: '100%', padding: '10px 14px', borderRadius: 8, border: `1px solid ${COLORS.border}`,
              fontSize: 14, color: COLORS.text, background: '#fff', outline: 'none', marginBottom: 20, boxSizing: 'border-box',
            }}>
              {['250m', '500m', '1000m', '2000m'].map(v => <option key={v} value={v}>{v}</option>)}
            </select>

            <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
              <button onClick={() => setShowModal(false)} style={{
                padding: '10px 20px', borderRadius: 8, border: `1px solid ${COLORS.border}`,
                background: '#fff', color: COLORS.text, fontSize: 14, fontWeight: 600, cursor: 'pointer',
              }}>Cancelar</button>
              <button onClick={() => setShowModal(false)} style={{
                padding: '10px 20px', borderRadius: 8, border: 'none',
                background: COLORS.primary, color: '#fff', fontSize: 14, fontWeight: 600, cursor: 'pointer',
              }}>Desplegar</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
