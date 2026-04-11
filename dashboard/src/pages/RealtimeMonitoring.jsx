import { useState, useEffect, useRef } from 'react'

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

const ENDPOINTS = [
  '/api/v2/consortiums/', '/api/v2/training/start/', '/api/v2/data/upload/',
  '/api/v2/models/predict/', '/api/v2/auth/login/', '/api/v2/governance/proposals/',
  '/api/v2/compliance/status/', '/api/v2/keys/generate/',
]

const STATUS_CODES = [200, 200, 200, 200, 200, 201, 200, 401, 500, 200, 200, 200, 200, 200, 204]

function generateApiCall(id) {
  const endpoint = ENDPOINTS[Math.floor(Math.random() * ENDPOINTS.length)]
  const status = STATUS_CODES[Math.floor(Math.random() * STATUS_CODES.length)]
  const latency = Math.floor(Math.random() * 350) + 20
  const now = new Date()
  return {
    id,
    timestamp: now.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    endpoint,
    status,
    latency,
  }
}

function generateBlockchainTx(id) {
  const types = ['Registro de modelo', 'Verificacion ZKP', 'Actualizacion de pesos', 'Registro de contribucion']
  const statuses = ['confirmada', 'confirmada', 'confirmada', 'pendiente']
  return {
    id,
    hash: `0x${Array.from({ length: 8 }, () => Math.floor(Math.random() * 16).toString(16)).join('')}...`,
    type: types[Math.floor(Math.random() * types.length)],
    status: statuses[Math.floor(Math.random() * statuses.length)],
    time: new Date().toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' }),
    gas: (Math.random() * 0.008 + 0.001).toFixed(4),
  }
}

const INITIAL_CALLS = Array.from({ length: 10 }, (_, i) => generateApiCall(i))
const INITIAL_TXS = Array.from({ length: 5 }, (_, i) => generateBlockchainTx(i))

export default function RealtimeMonitoring() {
  const [systemStatus, setSystemStatus] = useState('green')
  const [uptime, setUptime] = useState('99.97%')
  const [metrics, setMetrics] = useState({
    latency: { value: 142, trend: 'down', change: '-8ms' },
    throughput: { value: 1247, trend: 'up', change: '+52/s' },
    errorRate: { value: 0.12, trend: 'down', change: '-0.03%' },
    activeUsers: { value: 84, trend: 'up', change: '+12' },
  })
  const [apiCalls, setApiCalls] = useState(INITIAL_CALLS)
  const [fheOps, setFheOps] = useState({ encryptions: 342, decryptions: 198, trainings: 12 })
  const [blockchainTxs, setBlockchainTxs] = useState(INITIAL_TXS)
  const callIdRef = useRef(10)
  const txIdRef = useRef(5)

  useEffect(() => {
    const interval = setInterval(() => {
      // Update metrics with small random variations
      setMetrics(prev => ({
        latency: {
          value: Math.max(50, prev.latency.value + Math.floor(Math.random() * 20 - 10)),
          trend: Math.random() > 0.5 ? 'up' : 'down',
          change: `${Math.random() > 0.5 ? '+' : '-'}${Math.floor(Math.random() * 15)}ms`,
        },
        throughput: {
          value: Math.max(800, prev.throughput.value + Math.floor(Math.random() * 100 - 50)),
          trend: Math.random() > 0.4 ? 'up' : 'down',
          change: `${Math.random() > 0.5 ? '+' : '-'}${Math.floor(Math.random() * 80)}/s`,
        },
        errorRate: {
          value: Math.max(0, +(prev.errorRate.value + (Math.random() * 0.06 - 0.03)).toFixed(2)),
          trend: Math.random() > 0.5 ? 'up' : 'down',
          change: `${Math.random() > 0.5 ? '+' : '-'}${(Math.random() * 0.05).toFixed(2)}%`,
        },
        activeUsers: {
          value: Math.max(20, prev.activeUsers.value + Math.floor(Math.random() * 10 - 5)),
          trend: Math.random() > 0.4 ? 'up' : 'down',
          change: `${Math.random() > 0.5 ? '+' : '-'}${Math.floor(Math.random() * 8)}`,
        },
      }))

      // Add new API call
      callIdRef.current += 1
      setApiCalls(prev => [generateApiCall(callIdRef.current), ...prev.slice(0, 9)])

      // Occasionally add blockchain tx
      if (Math.random() > 0.6) {
        txIdRef.current += 1
        setBlockchainTxs(prev => [generateBlockchainTx(txIdRef.current), ...prev.slice(0, 4)])
      }

      // Update FHE ops
      setFheOps(prev => ({
        encryptions: prev.encryptions + Math.floor(Math.random() * 5),
        decryptions: prev.decryptions + Math.floor(Math.random() * 3),
        trainings: prev.trainings + (Math.random() > 0.85 ? 1 : 0),
      }))

      // Random system status (mostly green)
      const r = Math.random()
      setSystemStatus(r > 0.95 ? 'yellow' : 'green')
    }, 3000)

    return () => clearInterval(interval)
  }, [])

  const statusColors = { green: COLORS.success, yellow: COLORS.warning, red: COLORS.danger }
  const statusLabels = { green: 'Operativo', yellow: 'Degradado', red: 'Caido' }

  const METRIC_CARDS = [
    { key: 'latency', label: 'Latencia API', value: `${metrics.latency.value}ms`, ...metrics.latency },
    { key: 'throughput', label: 'Throughput', value: `${metrics.throughput.value}/s`, ...metrics.throughput },
    { key: 'errorRate', label: 'Tasa de Error', value: `${metrics.errorRate.value}%`, ...metrics.errorRate },
    { key: 'activeUsers', label: 'Usuarios Activos', value: metrics.activeUsers.value, ...metrics.activeUsers },
  ]

  return (
    <div style={{ padding: 32, maxWidth: 1200, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 32, flexWrap: 'wrap', gap: 16 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 700, color: COLORS.text, margin: '0 0 8px' }}>
            Monitoreo en Tiempo Real
          </h1>
          <p style={{ fontSize: 16, color: COLORS.muted, margin: 0 }}>
            Metricas de rendimiento y operaciones del sistema
          </p>
        </div>
        {/* System status badge */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 10, padding: '10px 20px',
          borderRadius: 10, background: COLORS.card, border: `1px solid ${COLORS.border}`,
        }}>
          <div style={{
            width: 12, height: 12, borderRadius: '50%',
            background: statusColors[systemStatus],
            boxShadow: `0 0 8px ${statusColors[systemStatus]}88`,
            animation: 'pulse 2s ease-in-out infinite',
          }} />
          <span style={{ fontSize: 14, fontWeight: 600, color: statusColors[systemStatus] }}>
            {statusLabels[systemStatus]}
          </span>
          <span style={{ fontSize: 13, color: COLORS.muted }}>|</span>
          <span style={{ fontSize: 13, color: COLORS.muted }}>Uptime: {uptime}</span>
        </div>
      </div>
      <style>{`@keyframes pulse { 0%, 100% { opacity: 1 } 50% { opacity: 0.5 } }`}</style>

      {/* Metric cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, marginBottom: 24 }}>
        {METRIC_CARDS.map((m) => (
          <div key={m.key} style={{
            background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 20,
          }}>
            <p style={{ fontSize: 13, color: COLORS.muted, margin: '0 0 8px' }}>{m.label}</p>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
              <span style={{ fontSize: 28, fontWeight: 700, color: COLORS.text }}>{m.value}</span>
              <span style={{
                fontSize: 13, fontWeight: 600,
                color: m.trend === 'up'
                  ? (m.key === 'errorRate' || m.key === 'latency' ? COLORS.danger : COLORS.success)
                  : (m.key === 'errorRate' || m.key === 'latency' ? COLORS.success : COLORS.danger),
              }}>
                {m.trend === 'up' ? '\u2191' : '\u2193'} {m.change}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* FHE operations */}
      <div style={{
        background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`,
        padding: 20, marginBottom: 24, display: 'flex', justifyContent: 'space-around', flexWrap: 'wrap', gap: 16,
      }}>
        <div style={{ textAlign: 'center' }}>
          <p style={{ fontSize: 12, color: COLORS.muted, margin: '0 0 4px', fontWeight: 600, textTransform: 'uppercase' }}>Encriptaciones hoy</p>
          <p style={{ fontSize: 24, fontWeight: 700, color: COLORS.primary, margin: 0 }}>{fheOps.encryptions}</p>
        </div>
        <div style={{ width: 1, background: COLORS.border }} />
        <div style={{ textAlign: 'center' }}>
          <p style={{ fontSize: 12, color: COLORS.muted, margin: '0 0 4px', fontWeight: 600, textTransform: 'uppercase' }}>Desencriptaciones hoy</p>
          <p style={{ fontSize: 24, fontWeight: 700, color: COLORS.success, margin: 0 }}>{fheOps.decryptions}</p>
        </div>
        <div style={{ width: 1, background: COLORS.border }} />
        <div style={{ textAlign: 'center' }}>
          <p style={{ fontSize: 12, color: COLORS.muted, margin: '0 0 4px', fontWeight: 600, textTransform: 'uppercase' }}>Entrenamientos hoy</p>
          <p style={{ fontSize: 24, fontWeight: 700, color: COLORS.warning, margin: 0 }}>{fheOps.trainings}</p>
        </div>
      </div>

      {/* Two-column: API calls + Blockchain txs */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 24 }}>
        {/* API calls log */}
        <div style={{
          background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 24,
        }}>
          <h2 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: '0 0 16px' }}>
            Llamadas API recientes
          </h2>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: `2px solid ${COLORS.border}` }}>
                {['Hora', 'Endpoint', 'Estado', 'Latencia'].map((h) => (
                  <th key={h} style={{
                    textAlign: 'left', padding: '8px 6px', fontSize: 12,
                    fontWeight: 600, color: COLORS.muted, textTransform: 'uppercase',
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {apiCalls.map((call) => (
                <tr key={call.id} style={{ borderBottom: `1px solid ${COLORS.border}` }}>
                  <td style={{ padding: '8px 6px', fontSize: 13, color: COLORS.muted, fontFamily: 'monospace' }}>
                    {call.timestamp}
                  </td>
                  <td style={{ padding: '8px 6px', fontSize: 13, color: COLORS.text, fontFamily: 'monospace' }}>
                    {call.endpoint}
                  </td>
                  <td style={{ padding: '8px 6px' }}>
                    <span style={{
                      padding: '2px 8px', borderRadius: 4, fontSize: 12, fontWeight: 600, fontFamily: 'monospace',
                      background: call.status < 300 ? COLORS.successLight : call.status < 500 ? COLORS.warningLight : COLORS.dangerLight,
                      color: call.status < 300 ? COLORS.success : call.status < 500 ? COLORS.warning : COLORS.danger,
                    }}>
                      {call.status}
                    </span>
                  </td>
                  <td style={{
                    padding: '8px 6px', fontSize: 13, fontFamily: 'monospace',
                    color: call.latency > 250 ? COLORS.danger : call.latency > 150 ? COLORS.warning : COLORS.muted,
                  }}>
                    {call.latency}ms
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Blockchain transactions */}
        <div style={{
          background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 24,
        }}>
          <h2 style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, margin: '0 0 16px' }}>
            Transacciones blockchain
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
            {blockchainTxs.map((tx) => (
              <div key={tx.id} style={{
                padding: '12px 0', borderBottom: `1px solid ${COLORS.border}`,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                  <span style={{ fontSize: 13, fontWeight: 500, color: COLORS.text }}>{tx.type}</span>
                  <span style={{
                    padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 600,
                    background: tx.status === 'confirmada' ? COLORS.successLight : COLORS.warningLight,
                    color: tx.status === 'confirmada' ? COLORS.success : COLORS.warning,
                  }}>
                    {tx.status}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: 12, color: COLORS.muted, fontFamily: 'monospace' }}>{tx.hash}</span>
                  <span style={{ fontSize: 12, color: COLORS.muted }}>{tx.gas} ETH | {tx.time}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
