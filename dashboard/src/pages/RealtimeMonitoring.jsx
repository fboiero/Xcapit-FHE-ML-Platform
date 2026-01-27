import { useState, useEffect, useRef, useCallback } from 'react'
import { useTranslation } from 'react-i18next'

export default function RealtimeMonitoring() {
  const { t } = useTranslation()
  const [connected, setConnected] = useState(false)
  const [metrics, setMetrics] = useState({
    requestsPerSecond: 0,
    avgLatency: 0,
    activeModels: 0,
    queueSize: 0,
    cpuUsage: 0,
    memoryUsage: 0,
    gpuUsage: 0,
  })
  const [history, setHistory] = useState([])
  const [alerts, setAlerts] = useState([])
  const [logs, setLogs] = useState([])
  const [selectedTimeRange, setSelectedTimeRange] = useState('5m')
  const intervalRef = useRef(null)

  // Simulate WebSocket connection
  useEffect(() => {
    const connect = () => {
      setConnected(true)

      intervalRef.current = setInterval(() => {
        // Simulate real-time data
        const newMetrics = {
          requestsPerSecond: Math.floor(Math.random() * 100) + 50,
          avgLatency: Math.floor(Math.random() * 50) + 10,
          activeModels: Math.floor(Math.random() * 5) + 3,
          queueSize: Math.floor(Math.random() * 20),
          cpuUsage: Math.random() * 40 + 30,
          memoryUsage: Math.random() * 30 + 50,
          gpuUsage: Math.random() * 50 + 20,
        }

        setMetrics(newMetrics)
        setHistory(prev => [...prev.slice(-60), { ...newMetrics, timestamp: Date.now() }])

        // Random log entry
        if (Math.random() > 0.7) {
          const logTypes = ['info', 'warning', 'error']
          const logType = logTypes[Math.floor(Math.random() * logTypes.length)]
          const messages = {
            info: ['Model inference completed', 'New training job started', 'Batch prediction processed'],
            warning: ['High latency detected', 'Queue size increasing', 'Memory usage above 80%'],
            error: ['Model failed to load', 'Connection timeout', 'Invalid input data'],
          }

          setLogs(prev => [{
            id: Date.now(),
            type: logType,
            message: messages[logType][Math.floor(Math.random() * messages[logType].length)],
            timestamp: new Date().toISOString(),
          }, ...prev.slice(0, 49)])
        }
      }, 1000)
    }

    connect()

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [])

  // Generate alerts based on metrics
  useEffect(() => {
    const newAlerts = []
    if (metrics.cpuUsage > 80) {
      newAlerts.push({ type: 'warning', message: t('monitoring.highCpuUsage') })
    }
    if (metrics.memoryUsage > 85) {
      newAlerts.push({ type: 'error', message: t('monitoring.highMemoryUsage') })
    }
    if (metrics.avgLatency > 40) {
      newAlerts.push({ type: 'warning', message: t('monitoring.highLatency') })
    }
    if (metrics.queueSize > 15) {
      newAlerts.push({ type: 'info', message: t('monitoring.queueBacklog') })
    }
    setAlerts(newAlerts)
  }, [metrics, t])

  const MetricCard = ({ title, value, unit, trend, icon, color }) => (
    <div className="bg-white rounded-xl border border-slate-200 p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-slate-500">{title}</span>
        <span className={`text-xl ${color}`}>{icon}</span>
      </div>
      <div className="flex items-baseline gap-1">
        <span className="text-2xl font-bold text-slate-900">{value}</span>
        <span className="text-sm text-slate-500">{unit}</span>
      </div>
      {trend !== undefined && (
        <div className={`text-sm mt-1 ${trend >= 0 ? 'text-green-600' : 'text-red-600'}`}>
          {trend >= 0 ? '↑' : '↓'} {Math.abs(trend).toFixed(1)}%
        </div>
      )}
    </div>
  )

  const renderSparkline = (data, color) => {
    if (data.length < 2) return null

    const values = data.map(d => d.value)
    const min = Math.min(...values)
    const max = Math.max(...values)
    const range = max - min || 1

    const points = data.map((d, i) => {
      const x = (i / (data.length - 1)) * 100
      const y = 100 - ((d.value - min) / range) * 100
      return `${x},${y}`
    }).join(' ')

    return (
      <svg className="w-full h-12" viewBox="0 0 100 100" preserveAspectRatio="none">
        <polyline
          points={points}
          fill="none"
          stroke={color}
          strokeWidth="2"
          vectorEffect="non-scaling-stroke"
        />
      </svg>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{t('monitoring.title')}</h1>
          <p className="text-slate-600 mt-1">{t('monitoring.subtitle')}</p>
        </div>
        <div className="flex items-center gap-4">
          <div className={`flex items-center gap-2 px-3 py-1 rounded-full ${
            connected ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
          }`}>
            <span className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
            {connected ? t('monitoring.connected') : t('monitoring.disconnected')}
          </div>
          <select
            value={selectedTimeRange}
            onChange={(e) => setSelectedTimeRange(e.target.value)}
            className="px-4 py-2 border border-slate-200 rounded-lg text-sm"
          >
            <option value="1m">1 {t('monitoring.minute')}</option>
            <option value="5m">5 {t('monitoring.minutes')}</option>
            <option value="15m">15 {t('monitoring.minutes')}</option>
            <option value="1h">1 {t('monitoring.hour')}</option>
          </select>
        </div>
      </div>

      {/* Alerts */}
      {alerts.length > 0 && (
        <div className="space-y-2">
          {alerts.map((alert, idx) => (
            <div
              key={idx}
              className={`px-4 py-3 rounded-lg flex items-center gap-3 ${
                alert.type === 'error' ? 'bg-red-50 text-red-700 border border-red-200' :
                alert.type === 'warning' ? 'bg-yellow-50 text-yellow-700 border border-yellow-200' :
                'bg-blue-50 text-blue-700 border border-blue-200'
              }`}
            >
              {alert.type === 'error' ? '⚠️' : alert.type === 'warning' ? '⚡' : 'ℹ️'}
              <span className="font-medium">{alert.message}</span>
            </div>
          ))}
        </div>
      )}

      {/* Main Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          title={t('monitoring.requestsPerSecond')}
          value={metrics.requestsPerSecond}
          unit="req/s"
          icon="📊"
          color="text-blue-500"
        />
        <MetricCard
          title={t('monitoring.avgLatency')}
          value={metrics.avgLatency}
          unit="ms"
          icon="⚡"
          color="text-yellow-500"
        />
        <MetricCard
          title={t('monitoring.activeModels')}
          value={metrics.activeModels}
          unit=""
          icon="🤖"
          color="text-purple-500"
        />
        <MetricCard
          title={t('monitoring.queueSize')}
          value={metrics.queueSize}
          unit={t('monitoring.jobs')}
          icon="📋"
          color="text-green-500"
        />
      </div>

      {/* Resource Usage */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h3 className="font-medium text-slate-900 mb-4">{t('monitoring.cpuUsage')}</h3>
          <div className="relative pt-1">
            <div className="flex items-center justify-between mb-2">
              <span className="text-2xl font-bold text-slate-900">{metrics.cpuUsage.toFixed(1)}%</span>
              <span className={`text-sm ${metrics.cpuUsage > 80 ? 'text-red-600' : 'text-green-600'}`}>
                {metrics.cpuUsage > 80 ? t('monitoring.high') : t('monitoring.normal')}
              </span>
            </div>
            <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-300 ${
                  metrics.cpuUsage > 80 ? 'bg-red-500' : metrics.cpuUsage > 60 ? 'bg-yellow-500' : 'bg-green-500'
                }`}
                style={{ width: `${metrics.cpuUsage}%` }}
              />
            </div>
          </div>
          <div className="mt-4">
            {renderSparkline(
              history.slice(-30).map(h => ({ value: h.cpuUsage })),
              metrics.cpuUsage > 80 ? '#ef4444' : '#22c55e'
            )}
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h3 className="font-medium text-slate-900 mb-4">{t('monitoring.memoryUsage')}</h3>
          <div className="relative pt-1">
            <div className="flex items-center justify-between mb-2">
              <span className="text-2xl font-bold text-slate-900">{metrics.memoryUsage.toFixed(1)}%</span>
              <span className={`text-sm ${metrics.memoryUsage > 85 ? 'text-red-600' : 'text-green-600'}`}>
                {metrics.memoryUsage > 85 ? t('monitoring.high') : t('monitoring.normal')}
              </span>
            </div>
            <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-300 ${
                  metrics.memoryUsage > 85 ? 'bg-red-500' : metrics.memoryUsage > 70 ? 'bg-yellow-500' : 'bg-blue-500'
                }`}
                style={{ width: `${metrics.memoryUsage}%` }}
              />
            </div>
          </div>
          <div className="mt-4">
            {renderSparkline(
              history.slice(-30).map(h => ({ value: h.memoryUsage })),
              metrics.memoryUsage > 85 ? '#ef4444' : '#3b82f6'
            )}
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h3 className="font-medium text-slate-900 mb-4">{t('monitoring.gpuUsage')}</h3>
          <div className="relative pt-1">
            <div className="flex items-center justify-between mb-2">
              <span className="text-2xl font-bold text-slate-900">{metrics.gpuUsage.toFixed(1)}%</span>
              <span className="text-sm text-green-600">{t('monitoring.normal')}</span>
            </div>
            <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-purple-500 rounded-full transition-all duration-300"
                style={{ width: `${metrics.gpuUsage}%` }}
              />
            </div>
          </div>
          <div className="mt-4">
            {renderSparkline(
              history.slice(-30).map(h => ({ value: h.gpuUsage })),
              '#a855f7'
            )}
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Request Rate Chart */}
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h3 className="font-medium text-slate-900 mb-4">{t('monitoring.requestRate')}</h3>
          <div className="h-48 relative">
            <svg className="w-full h-full" viewBox="0 0 100 50" preserveAspectRatio="none">
              {history.length > 1 && (
                <>
                  <defs>
                    <linearGradient id="requestGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#6366f1" stopOpacity="0.3" />
                      <stop offset="100%" stopColor="#6366f1" stopOpacity="0" />
                    </linearGradient>
                  </defs>
                  <path
                    d={`M 0 50 ${history.slice(-60).map((h, i) => {
                      const x = (i / 59) * 100
                      const y = 50 - (h.requestsPerSecond / 150) * 50
                      return `L ${x} ${y}`
                    }).join(' ')} L 100 50 Z`}
                    fill="url(#requestGradient)"
                  />
                  <polyline
                    points={history.slice(-60).map((h, i) => {
                      const x = (i / 59) * 100
                      const y = 50 - (h.requestsPerSecond / 150) * 50
                      return `${x},${y}`
                    }).join(' ')}
                    fill="none"
                    stroke="#6366f1"
                    strokeWidth="1.5"
                    vectorEffect="non-scaling-stroke"
                  />
                </>
              )}
            </svg>
          </div>
        </div>

        {/* Latency Chart */}
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h3 className="font-medium text-slate-900 mb-4">{t('monitoring.latencyDistribution')}</h3>
          <div className="h-48 relative">
            <svg className="w-full h-full" viewBox="0 0 100 50" preserveAspectRatio="none">
              {history.length > 1 && (
                <>
                  <defs>
                    <linearGradient id="latencyGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.3" />
                      <stop offset="100%" stopColor="#f59e0b" stopOpacity="0" />
                    </linearGradient>
                  </defs>
                  <path
                    d={`M 0 50 ${history.slice(-60).map((h, i) => {
                      const x = (i / 59) * 100
                      const y = 50 - (h.avgLatency / 80) * 50
                      return `L ${x} ${y}`
                    }).join(' ')} L 100 50 Z`}
                    fill="url(#latencyGradient)"
                  />
                  <polyline
                    points={history.slice(-60).map((h, i) => {
                      const x = (i / 59) * 100
                      const y = 50 - (h.avgLatency / 80) * 50
                      return `${x},${y}`
                    }).join(' ')}
                    fill="none"
                    stroke="#f59e0b"
                    strokeWidth="1.5"
                    vectorEffect="non-scaling-stroke"
                  />
                </>
              )}
            </svg>
          </div>
        </div>
      </div>

      {/* Live Logs */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <div className="p-4 border-b border-slate-200 flex items-center justify-between">
          <h3 className="font-medium text-slate-900">{t('monitoring.liveLogs')}</h3>
          <button className="text-sm text-slate-500 hover:text-slate-700">
            {t('monitoring.clearLogs')}
          </button>
        </div>
        <div className="h-64 overflow-y-auto bg-slate-900 font-mono text-sm">
          {logs.map(log => (
            <div
              key={log.id}
              className={`px-4 py-2 border-b border-slate-800 ${
                log.type === 'error' ? 'text-red-400' :
                log.type === 'warning' ? 'text-yellow-400' :
                'text-green-400'
              }`}
            >
              <span className="text-slate-500">[{new Date(log.timestamp).toLocaleTimeString()}]</span>
              <span className={`ml-2 px-1 rounded ${
                log.type === 'error' ? 'bg-red-900' :
                log.type === 'warning' ? 'bg-yellow-900' :
                'bg-green-900'
              }`}>
                {log.type.toUpperCase()}
              </span>
              <span className="ml-2">{log.message}</span>
            </div>
          ))}
          {logs.length === 0 && (
            <div className="p-4 text-slate-500 text-center">
              {t('monitoring.waitingForLogs')}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
