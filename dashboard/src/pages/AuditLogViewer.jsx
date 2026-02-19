import { useState, useEffect, useMemo } from 'react'
import { useTranslation } from 'react-i18next'

// Generate mock audit logs
const generateMockLogs = () => {
  const actions = [
    { type: 'model_created', description: 'Created model', severity: 'info' },
    { type: 'model_trained', description: 'Trained model', severity: 'success' },
    { type: 'model_deployed', description: 'Deployed model', severity: 'success' },
    { type: 'prediction_made', description: 'Made prediction', severity: 'info' },
    { type: 'data_uploaded', description: 'Uploaded data', severity: 'info' },
    { type: 'data_encrypted', description: 'Encrypted data', severity: 'info' },
    { type: 'member_joined', description: 'Member joined consortium', severity: 'success' },
    { type: 'member_left', description: 'Member left consortium', severity: 'warning' },
    { type: 'proposal_created', description: 'Created proposal', severity: 'info' },
    { type: 'vote_cast', description: 'Vote cast on proposal', severity: 'info' },
    { type: 'login_success', description: 'User logged in', severity: 'success' },
    { type: 'login_failed', description: 'Failed login attempt', severity: 'error' },
    { type: 'api_key_created', description: 'Created API key', severity: 'warning' },
    { type: 'api_key_revoked', description: 'Revoked API key', severity: 'warning' },
    { type: 'settings_changed', description: 'Changed settings', severity: 'info' },
    { type: 'export_model', description: 'Exported model', severity: 'info' },
    { type: 'import_model', description: 'Imported model', severity: 'info' },
  ]

  const users = ['admin@company.com', 'analyst@company.com', 'engineer@company.com', 'manager@company.com']
  const resources = ['model-001', 'model-002', 'consortium-001', 'dataset-001', 'api-key-001']
  const ips = ['192.168.1.100', '10.0.0.50', '172.16.0.25', '192.168.2.150']

  const logs = []
  const now = Date.now()

  for (let i = 0; i < 100; i++) {
    const action = actions[Math.floor(Math.random() * actions.length)]
    logs.push({
      id: `log-${1000 - i}`,
      timestamp: new Date(now - i * 15 * 60 * 1000).toISOString(), // Every 15 minutes
      action: action.type,
      description: action.description,
      severity: action.severity,
      user: users[Math.floor(Math.random() * users.length)],
      resourceType: action.type.includes('model') ? 'model' :
                    action.type.includes('member') || action.type.includes('proposal') ? 'consortium' :
                    action.type.includes('data') ? 'dataset' : 'system',
      resourceId: resources[Math.floor(Math.random() * resources.length)],
      ipAddress: ips[Math.floor(Math.random() * ips.length)],
      userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
      metadata: action.type === 'prediction_made' ? { samples: Math.floor(Math.random() * 1000) + 1 } : {},
      txHash: action.type.includes('member') || action.type.includes('vote')
        ? `0x${Math.random().toString(16).slice(2, 66)}`
        : null,
    })
  }

  return logs
}

export default function AuditLogViewer() {
  const { t } = useTranslation()
  const [logs, setLogs] = useState([])
  const [filters, setFilters] = useState({
    search: '',
    severity: 'all',
    resourceType: 'all',
    dateFrom: '',
    dateTo: '',
    user: '',
  })
  const [selectedLog, setSelectedLog] = useState(null)
  const [currentPage, setCurrentPage] = useState(1)
  const logsPerPage = 20

  useEffect(() => {
    setLogs(generateMockLogs())
  }, [])

  const severityColors = {
    info: 'bg-blue-100 text-blue-800',
    success: 'bg-green-100 text-green-800',
    warning: 'bg-yellow-100 text-yellow-800',
    error: 'bg-red-100 text-red-800',
  }

  const severityIcons = {
    info: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    success: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    warning: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
    ),
    error: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  }

  // Filter logs
  const filteredLogs = useMemo(() => {
    return logs.filter(log => {
      if (filters.search && !log.description.toLowerCase().includes(filters.search.toLowerCase()) &&
          !log.action.toLowerCase().includes(filters.search.toLowerCase()) &&
          !log.user.toLowerCase().includes(filters.search.toLowerCase())) {
        return false
      }
      if (filters.severity !== 'all' && log.severity !== filters.severity) {
        return false
      }
      if (filters.resourceType !== 'all' && log.resourceType !== filters.resourceType) {
        return false
      }
      if (filters.user && !log.user.toLowerCase().includes(filters.user.toLowerCase())) {
        return false
      }
      if (filters.dateFrom && new Date(log.timestamp) < new Date(filters.dateFrom)) {
        return false
      }
      if (filters.dateTo && new Date(log.timestamp) > new Date(filters.dateTo + 'T23:59:59')) {
        return false
      }
      return true
    })
  }, [logs, filters])

  // Pagination
  const totalPages = Math.ceil(filteredLogs.length / logsPerPage)
  const paginatedLogs = filteredLogs.slice((currentPage - 1) * logsPerPage, currentPage * logsPerPage)

  // Statistics
  const stats = useMemo(() => {
    const today = new Date().toDateString()
    const todayLogs = logs.filter(log => new Date(log.timestamp).toDateString() === today)

    return {
      total: logs.length,
      today: todayLogs.length,
      errors: logs.filter(log => log.severity === 'error').length,
      warnings: logs.filter(log => log.severity === 'warning').length,
    }
  }, [logs])

  const formatDate = (isoString) => {
    const date = new Date(isoString)
    return date.toLocaleString()
  }

  const exportLogs = () => {
    const csv = [
      ['Timestamp', 'Action', 'Description', 'Severity', 'User', 'Resource Type', 'Resource ID', 'IP Address'].join(','),
      ...filteredLogs.map(log => [
        log.timestamp,
        log.action,
        log.description,
        log.severity,
        log.user,
        log.resourceType,
        log.resourceId,
        log.ipAddress,
      ].join(','))
    ].join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `audit-logs-${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Audit Log</h1>
          <p className="text-gray-600 mt-1">Complete history of system activities and events</p>
        </div>
        <button
          onClick={exportLogs}
          className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Export CSV
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-xl p-4 border border-gray-200">
          <div className="text-sm text-gray-500">Total Events</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">{stats.total}</div>
        </div>
        <div className="bg-white rounded-xl p-4 border border-gray-200">
          <div className="text-sm text-gray-500">Today</div>
          <div className="text-2xl font-bold text-blue-600 mt-1">{stats.today}</div>
        </div>
        <div className="bg-white rounded-xl p-4 border border-gray-200">
          <div className="text-sm text-gray-500">Warnings</div>
          <div className="text-2xl font-bold text-yellow-600 mt-1">{stats.warnings}</div>
        </div>
        <div className="bg-white rounded-xl p-4 border border-gray-200">
          <div className="text-sm text-gray-500">Errors</div>
          <div className="text-2xl font-bold text-red-600 mt-1">{stats.errors}</div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
          <div className="md:col-span-2">
            <label className="block text-xs font-medium text-gray-500 mb-1">Search</label>
            <input
              type="text"
              placeholder="Search logs..."
              value={filters.search}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Severity</label>
            <select
              value={filters.severity}
              onChange={(e) => setFilters({ ...filters, severity: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 text-sm"
            >
              <option value="all">All</option>
              <option value="info">Info</option>
              <option value="success">Success</option>
              <option value="warning">Warning</option>
              <option value="error">Error</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Resource Type</label>
            <select
              value={filters.resourceType}
              onChange={(e) => setFilters({ ...filters, resourceType: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 text-sm"
            >
              <option value="all">All</option>
              <option value="model">Model</option>
              <option value="consortium">Consortium</option>
              <option value="dataset">Dataset</option>
              <option value="system">System</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">From</label>
            <input
              type="date"
              value={filters.dateFrom}
              onChange={(e) => setFilters({ ...filters, dateFrom: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">To</label>
            <input
              type="date"
              value={filters.dateTo}
              onChange={(e) => setFilters({ ...filters, dateTo: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 text-sm"
            />
          </div>
        </div>
      </div>

      {/* Logs Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Severity</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">User</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Resource</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">IP</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {paginatedLogs.map(log => (
                <tr key={log.id} className="hover:bg-gray-50 cursor-pointer" onClick={() => setSelectedLog(log)}>
                  <td className="px-4 py-3 text-sm text-gray-500 whitespace-nowrap">
                    {formatDate(log.timestamp)}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full ${severityColors[log.severity]}`}>
                      {severityIcons[log.severity]}
                      {log.severity}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="font-medium text-gray-900 text-sm">{log.description}</div>
                    <div className="text-xs text-gray-500">{log.action}</div>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">{log.user}</td>
                  <td className="px-4 py-3">
                    <div className="text-sm text-gray-900">{log.resourceType}</div>
                    <div className="text-xs text-gray-500 font-mono">{log.resourceId}</div>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500 font-mono">{log.ipAddress}</td>
                  <td className="px-4 py-3">
                    {log.txHash && (
                      <span className="inline-flex items-center px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded-full">
                        Blockchain
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="px-4 py-3 border-t border-gray-200 flex items-center justify-between">
          <div className="text-sm text-gray-500">
            Showing {(currentPage - 1) * logsPerPage + 1} to {Math.min(currentPage * logsPerPage, filteredLogs.length)} of {filteredLogs.length} results
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50 hover:bg-gray-50"
            >
              Previous
            </button>
            <button
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50 hover:bg-gray-50"
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {/* Detail Modal */}
      {selectedLog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-auto">
            <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center sticky top-0 bg-white">
              <h3 className="text-lg font-semibold">Event Details</h3>
              <button onClick={() => setSelectedLog(null)} className="text-gray-400 hover:text-gray-600">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-gray-500">Timestamp</label>
                  <div className="text-sm text-gray-900 mt-1">{formatDate(selectedLog.timestamp)}</div>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500">Severity</label>
                  <div className="mt-1">
                    <span className={`inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full ${severityColors[selectedLog.severity]}`}>
                      {severityIcons[selectedLog.severity]}
                      {selectedLog.severity}
                    </span>
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500">Action</label>
                  <div className="text-sm text-gray-900 mt-1">{selectedLog.action}</div>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500">Description</label>
                  <div className="text-sm text-gray-900 mt-1">{selectedLog.description}</div>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500">User</label>
                  <div className="text-sm text-gray-900 mt-1">{selectedLog.user}</div>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500">IP Address</label>
                  <div className="text-sm text-gray-900 mt-1 font-mono">{selectedLog.ipAddress}</div>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500">Resource Type</label>
                  <div className="text-sm text-gray-900 mt-1">{selectedLog.resourceType}</div>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500">Resource ID</label>
                  <div className="text-sm text-gray-900 mt-1 font-mono">{selectedLog.resourceId}</div>
                </div>
              </div>

              {selectedLog.txHash && (
                <div>
                  <label className="block text-xs font-medium text-gray-500">Blockchain Transaction</label>
                  <div className="text-sm text-gray-900 mt-1 font-mono break-all bg-gray-50 p-2 rounded">
                    {selectedLog.txHash}
                  </div>
                </div>
              )}

              {Object.keys(selectedLog.metadata).length > 0 && (
                <div>
                  <label className="block text-xs font-medium text-gray-500">Metadata</label>
                  <pre className="text-sm text-gray-900 mt-1 bg-gray-50 p-2 rounded overflow-auto">
                    {JSON.stringify(selectedLog.metadata, null, 2)}
                  </pre>
                </div>
              )}

              <div>
                <label className="block text-xs font-medium text-gray-500">User Agent</label>
                <div className="text-sm text-gray-900 mt-1 font-mono text-xs">{selectedLog.userAgent}</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
