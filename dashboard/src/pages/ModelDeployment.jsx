import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'

// Simulated deployed models
const mockDeployedModels = [
  {
    id: 'dep-001',
    modelId: 'model-001',
    name: 'Fraud Detection v2.1',
    type: 'logistic_regression',
    endpoint: '/api/v2/predict/fraud-detection',
    status: 'active',
    version: '2.1.0',
    replicas: 3,
    cpu: '500m',
    memory: '1Gi',
    requests: 15420,
    avgLatency: 45,
    uptime: 99.98,
    createdAt: '2024-01-15T10:30:00Z',
  },
  {
    id: 'dep-002',
    modelId: 'model-002',
    name: 'Credit Scoring',
    type: 'gradient_boosting',
    endpoint: '/api/v2/predict/credit-scoring',
    status: 'active',
    version: '1.0.0',
    replicas: 2,
    cpu: '250m',
    memory: '512Mi',
    requests: 8932,
    avgLatency: 62,
    uptime: 99.95,
    createdAt: '2024-01-10T14:20:00Z',
  },
  {
    id: 'dep-003',
    modelId: 'model-003',
    name: 'Churn Prediction',
    type: 'random_forest',
    endpoint: '/api/v2/predict/churn',
    status: 'scaling',
    version: '1.2.0',
    replicas: 1,
    cpu: '250m',
    memory: '512Mi',
    requests: 3201,
    avgLatency: 78,
    uptime: 99.90,
    createdAt: '2024-01-08T09:15:00Z',
  },
]

// Simulated available models for deployment
const mockAvailableModels = [
  { id: 'model-004', name: 'Customer Segmentation', type: 'kmeans', version: '1.0.0' },
  { id: 'model-005', name: 'Risk Assessment', type: 'neural_network', version: '2.0.0' },
  { id: 'model-006', name: 'Anomaly Detector', type: 'isolation_forest', version: '1.1.0' },
]

export default function ModelDeployment() {
  const { t } = useTranslation()
  const [deployedModels, setDeployedModels] = useState(mockDeployedModels)
  const [availableModels] = useState(mockAvailableModels)
  const [showDeployModal, setShowDeployModal] = useState(false)
  const [selectedModel, setSelectedModel] = useState(null)
  const [deployConfig, setDeployConfig] = useState({
    replicas: 1,
    cpu: '250m',
    memory: '512Mi',
    autoscaling: false,
    minReplicas: 1,
    maxReplicas: 5,
  })

  const statusColors = {
    active: 'bg-green-100 text-green-800',
    scaling: 'bg-yellow-100 text-yellow-800',
    deploying: 'bg-blue-100 text-blue-800',
    stopped: 'bg-gray-100 text-gray-800',
    error: 'bg-red-100 text-red-800',
  }

  const handleDeploy = () => {
    if (!selectedModel) return

    const newDeployment = {
      id: `dep-${Date.now()}`,
      modelId: selectedModel.id,
      name: selectedModel.name,
      type: selectedModel.type,
      endpoint: `/api/v2/predict/${selectedModel.name.toLowerCase().replace(/\s+/g, '-')}`,
      status: 'deploying',
      version: selectedModel.version,
      ...deployConfig,
      requests: 0,
      avgLatency: 0,
      uptime: 100,
      createdAt: new Date().toISOString(),
    }

    setDeployedModels([newDeployment, ...deployedModels])
    setShowDeployModal(false)
    setSelectedModel(null)

    // Simulate deployment completion
    setTimeout(() => {
      setDeployedModels(prev =>
        prev.map(d => d.id === newDeployment.id ? { ...d, status: 'active' } : d)
      )
    }, 3000)
  }

  const handleScaleUp = (deploymentId) => {
    setDeployedModels(prev =>
      prev.map(d => d.id === deploymentId ? { ...d, replicas: d.replicas + 1, status: 'scaling' } : d)
    )
    setTimeout(() => {
      setDeployedModels(prev =>
        prev.map(d => d.id === deploymentId ? { ...d, status: 'active' } : d)
      )
    }, 2000)
  }

  const handleScaleDown = (deploymentId) => {
    setDeployedModels(prev =>
      prev.map(d => {
        if (d.id === deploymentId && d.replicas > 1) {
          return { ...d, replicas: d.replicas - 1, status: 'scaling' }
        }
        return d
      })
    )
    setTimeout(() => {
      setDeployedModels(prev =>
        prev.map(d => d.id === deploymentId ? { ...d, status: 'active' } : d)
      )
    }, 2000)
  }

  const handleStop = (deploymentId) => {
    setDeployedModels(prev =>
      prev.map(d => d.id === deploymentId ? { ...d, status: 'stopped', replicas: 0 } : d)
    )
  }

  const handleRestart = (deploymentId) => {
    setDeployedModels(prev =>
      prev.map(d => d.id === deploymentId ? { ...d, status: 'deploying', replicas: 1 } : d)
    )
    setTimeout(() => {
      setDeployedModels(prev =>
        prev.map(d => d.id === deploymentId ? { ...d, status: 'active' } : d)
      )
    }, 2000)
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Model Deployment</h1>
          <p className="text-gray-600 mt-1">Deploy and manage your FHE models as API endpoints</p>
        </div>
        <button
          onClick={() => setShowDeployModal(true)}
          className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          Deploy Model
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white rounded-xl p-4 border border-gray-200">
          <div className="text-sm text-gray-500">Active Deployments</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">
            {deployedModels.filter(d => d.status === 'active').length}
          </div>
        </div>
        <div className="bg-white rounded-xl p-4 border border-gray-200">
          <div className="text-sm text-gray-500">Total Requests (24h)</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">
            {deployedModels.reduce((sum, d) => sum + d.requests, 0).toLocaleString()}
          </div>
        </div>
        <div className="bg-white rounded-xl p-4 border border-gray-200">
          <div className="text-sm text-gray-500">Avg. Latency</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">
            {Math.round(deployedModels.reduce((sum, d) => sum + d.avgLatency, 0) / deployedModels.length)}ms
          </div>
        </div>
        <div className="bg-white rounded-xl p-4 border border-gray-200">
          <div className="text-sm text-gray-500">Avg. Uptime</div>
          <div className="text-2xl font-bold text-green-600 mt-1">
            {(deployedModels.reduce((sum, d) => sum + d.uptime, 0) / deployedModels.length).toFixed(2)}%
          </div>
        </div>
      </div>

      {/* Deployed Models Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Deployed Models</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Model</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Endpoint</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Replicas</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Requests</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Latency</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {deployedModels.map(deployment => (
                <tr key={deployment.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="font-medium text-gray-900">{deployment.name}</div>
                    <div className="text-sm text-gray-500">v{deployment.version} - {deployment.type}</div>
                  </td>
                  <td className="px-6 py-4">
                    <code className="text-sm bg-gray-100 px-2 py-1 rounded">{deployment.endpoint}</code>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${statusColors[deployment.status]}`}>
                      {deployment.status}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleScaleDown(deployment.id)}
                        disabled={deployment.replicas <= 1 || deployment.status !== 'active'}
                        className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-50"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
                        </svg>
                      </button>
                      <span className="font-medium">{deployment.replicas}</span>
                      <button
                        onClick={() => handleScaleUp(deployment.id)}
                        disabled={deployment.status !== 'active'}
                        className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-50"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                        </svg>
                      </button>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">{deployment.requests.toLocaleString()}</td>
                  <td className="px-6 py-4 text-sm text-gray-900">{deployment.avgLatency}ms</td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      {deployment.status === 'stopped' ? (
                        <button
                          onClick={() => handleRestart(deployment.id)}
                          className="p-1 text-green-600 hover:text-green-800"
                          title="Start"
                        >
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                        </button>
                      ) : (
                        <button
                          onClick={() => handleStop(deployment.id)}
                          className="p-1 text-red-600 hover:text-red-800"
                          title="Stop"
                        >
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
                          </svg>
                        </button>
                      )}
                      <button className="p-1 text-gray-400 hover:text-gray-600" title="Logs">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Deploy Modal */}
      {showDeployModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full mx-4">
            <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
              <h3 className="text-lg font-semibold">Deploy Model</h3>
              <button onClick={() => setShowDeployModal(false)} className="text-gray-400 hover:text-gray-600">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="p-6 space-y-4">
              {/* Model Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Select Model</label>
                <select
                  value={selectedModel?.id || ''}
                  onChange={(e) => setSelectedModel(availableModels.find(m => m.id === e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                >
                  <option value="">Choose a model...</option>
                  {availableModels.map(model => (
                    <option key={model.id} value={model.id}>
                      {model.name} (v{model.version}) - {model.type}
                    </option>
                  ))}
                </select>
              </div>

              {/* Resources */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Replicas</label>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    value={deployConfig.replicas}
                    onChange={(e) => setDeployConfig({ ...deployConfig, replicas: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">CPU</label>
                  <select
                    value={deployConfig.cpu}
                    onChange={(e) => setDeployConfig({ ...deployConfig, cpu: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                  >
                    <option value="250m">250m</option>
                    <option value="500m">500m</option>
                    <option value="1000m">1 CPU</option>
                    <option value="2000m">2 CPU</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Memory</label>
                <select
                  value={deployConfig.memory}
                  onChange={(e) => setDeployConfig({ ...deployConfig, memory: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                >
                  <option value="256Mi">256 Mi</option>
                  <option value="512Mi">512 Mi</option>
                  <option value="1Gi">1 Gi</option>
                  <option value="2Gi">2 Gi</option>
                  <option value="4Gi">4 Gi</option>
                </select>
              </div>

              {/* Autoscaling */}
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  id="autoscaling"
                  checked={deployConfig.autoscaling}
                  onChange={(e) => setDeployConfig({ ...deployConfig, autoscaling: e.target.checked })}
                  className="w-4 h-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                />
                <label htmlFor="autoscaling" className="text-sm text-gray-700">Enable autoscaling</label>
              </div>

              {deployConfig.autoscaling && (
                <div className="grid grid-cols-2 gap-4 pl-7">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Min Replicas</label>
                    <input
                      type="number"
                      min="1"
                      value={deployConfig.minReplicas}
                      onChange={(e) => setDeployConfig({ ...deployConfig, minReplicas: parseInt(e.target.value) })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Max Replicas</label>
                    <input
                      type="number"
                      min="1"
                      value={deployConfig.maxReplicas}
                      onChange={(e) => setDeployConfig({ ...deployConfig, maxReplicas: parseInt(e.target.value) })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                    />
                  </div>
                </div>
              )}
            </div>
            <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
              <button
                onClick={() => setShowDeployModal(false)}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition"
              >
                Cancel
              </button>
              <button
                onClick={handleDeploy}
                disabled={!selectedModel}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition disabled:opacity-50"
              >
                Deploy
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
